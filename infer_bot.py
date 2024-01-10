import os
import sys
from dotenv import load_dotenv
from infer.modules.vc.modules import VC
from infer.modules.uvr5.modules import uvr
from infer.lib.train.process_ckpt import (
    change_info,
    extract_small_model,
    merge,
    show_info,
)
from i18n.i18n import I18nAuto
from configs.config import Config
from sklearn.cluster import MiniBatchKMeans
import torch
import numpy as np
import gradio as gr
import faiss
import fairseq
import pathlib
import json
from time import sleep
from subprocess import Popen
from random import shuffle
import warnings
import traceback
import threading
import shutil
import logging

global i18n
global config
global vc
global names
global uvr5_names
global index_root
global weight_uvr5_root
global weight_root
global index_paths

def vc_setup():
    now_dir = os.getcwd()
    sys.path.append(now_dir)
    load_dotenv()
    logging.getLogger("numba").setLevel(logging.WARNING)

    logger = logging.getLogger(__name__)

    tmp = os.path.join(now_dir, "TEMP")
    shutil.rmtree(tmp, ignore_errors=True)
    shutil.rmtree("%s/runtime/Lib/site-packages/infer_pack" % (now_dir), ignore_errors=True)
    shutil.rmtree("%s/runtime/Lib/site-packages/uvr5_pack" % (now_dir), ignore_errors=True)
    os.makedirs(tmp, exist_ok=True)
    os.makedirs(os.path.join(now_dir, "logs"), exist_ok=True)
    os.makedirs(os.path.join(now_dir, "assets/weights"), exist_ok=True)
    os.environ["TEMP"] = tmp
    warnings.filterwarnings("ignore")
    torch.manual_seed(114514)

    global config
    config = Config()
    global vc
    vc = VC(config)


    if config.dml == True:

        def forward_dml(ctx, x, scale):
            ctx.scale = scale
            res = x.clone().detach()
            return res

        fairseq.modules.grad_multiply.GradMultiply.forward = forward_dml
    global i18n
    i18n = I18nAuto()
    logger.info(i18n)
    # 判断是否有能用来训练和加速推理的N卡
    ngpu = torch.cuda.device_count()
    gpu_infos = []
    mem = []
    if_gpu_ok = False

    if torch.cuda.is_available() or ngpu != 0:
        for i in range(ngpu):
            gpu_name = torch.cuda.get_device_name(i)
            if any(
                value in gpu_name.upper()
                for value in [
                    "10",
                    "16",
                    "20",
                    "30",
                    "40",
                    "A2",
                    "A3",
                    "A4",
                    "P4",
                    "A50",
                    "500",
                    "A60",
                    "70",
                    "80",
                    "90",
                    "M4",
                    "T4",
                    "TITAN",
                ]
            ):
                # A10#A100#V100#A40#P40#M40#K80#A4500
                if_gpu_ok = True  # 至少有一张能用的N卡
                gpu_infos.append("%s\t%s" % (i, gpu_name))
                mem.append(
                    int(
                        torch.cuda.get_device_properties(i).total_memory
                        / 1024
                        / 1024
                        / 1024
                        + 0.4
                    )
                )
    if if_gpu_ok and len(gpu_infos) > 0:
        gpu_info = "\n".join(gpu_infos)
        default_batch_size = min(mem) // 2
    else:
        gpu_info = i18n("很遗憾您这没有能用的显卡来支持您训练")
        default_batch_size = 1
    gpus = "-".join([i[0] for i in gpu_infos])

class ToolButton(gr.Button, gr.components.FormComponent):
    """Small button with single emoji as text, fits inside gradio forms"""

    def __init__(self, **kwargs):
        super().__init__(variant="tool", **kwargs)

    def get_block_name(self):
        return "button"

def uvr_setup():
    global weight_root
    weight_root = os.getenv("weight_root")
    global weight_uvr5_root
    weight_uvr5_root = os.getenv("weight_uvr5_root")
    global index_root
    index_root = os.getenv("index_root")

    global names
    names = []
    for name in os.listdir(weight_root):
        if name.endswith(".pth"):
            names.append(name)
    global index_paths
    index_paths = []
    for root, dirs, files in os.walk(index_root, topdown=False):
        for name in files:
            if name.endswith(".index") and "trained" not in name:
                index_paths.append("%s/%s" % (root, name))

    global uvr5_names
    uvr5_names = []
    for name in os.listdir(weight_uvr5_root):
        if name.endswith(".pth") or "onnx" in name:
            uvr5_names.append(name.replace(".pth", ""))


def change_choices():
    global names
    names = []
    for name in os.listdir(weight_root):
        if name.endswith(".pth"):
            names.append(name)
    global index_paths
    index_paths = []
    for root, dirs, files in os.walk(index_root, topdown=False):
        for name in files:
            if name.endswith(".index") and "trained" not in name:
                index_paths.append("%s/%s" % (root, name))
    return {"choices": sorted(names), "__type__": "update"}, {
        "choices": sorted(index_paths),
        "__type__": "update",
    }


def clean():
    return {"value": "", "__type__": "update"}


def export_onnx(ModelPath, ExportedPath):
    from infer.modules.onnx.export import export_onnx as eo

    eo(ModelPath, ExportedPath)


sr_dict = {
    "32k": 32000,
    "40k": 40000,
    "48k": 48000,
}


def if_done(done, p):
    while 1:
        if p.poll() is None:
            sleep(0.5)
        else:
            break
    done[0] = True


def if_done_multi(done, ps):
    while 1:
        # poll==None代表进程未结束
        # 只要有一个进程未结束都不停
        flag = 1
        for p in ps:
            if p.poll() is None:
                flag = 0
                sleep(0.5)
                break
        if flag == 1:
            break
    done[0] = True

if __name__ == "__main__":
    vc_setup()
    uvr_setup()

# with gr.Blocks(title="RVC WebUI") as app:
#     gr.Markdown("## RVC WebUI")
#     gr.Markdown(
#         value=i18n(
#             "本软件以MIT协议开源, 作者不对软件具备任何控制力, 使用软件者、传播软件导出的声音者自负全责. <br>如不认可该条款, 则不能使用或引用软件包内任何代码和文件. 详见根目录<b>LICENSE</b>."
#         )
#     )
#     with gr.Tabs():
#         with gr.TabItem(i18n("模型推理")):
#             with gr.Row():
#                 sid0 = gr.Dropdown(label=i18n("推理音色"), choices=sorted(names))
#                 with gr.Column():
#                     refresh_button = gr.Button(i18n("刷新音色列表和索引路径"), variant="primary")
#                     clean_button = gr.Button(i18n("卸载音色省显存"), variant="primary")
#                 spk_item = gr.Slider(
#                     minimum=0,
#                     maximum=2333,
#                     step=1,
#                     label=i18n("请选择说话人id"),
#                     value=0,
#                     visible=False,
#                     interactive=True,
#                 )
#                 clean_button.click(
#                     fn=clean, inputs=[], outputs=[sid0], api_name="infer_clean"
#                 )
#             with gr.TabItem(i18n("单次推理")):
#                 with gr.Group():
#                     with gr.Row():
#                         with gr.Column():
#                             vc_transform0 = gr.Number(
#                                 label=i18n("变调(整数, 半音数量, 升八度12降八度-12)"), value=0
#                             )
#                             input_audio0 = gr.Textbox(
#                                 label=i18n("输入待处理音频文件路径(默认是正确格式示例)"),
#                                 placeholder="C:\\Users\\Desktop\\audio_example.wav",
#                             )
#                             file_index1 = gr.Textbox(
#                                 label=i18n("特征检索库文件路径,为空则使用下拉的选择结果"),
#                                 placeholder="C:\\Users\\Desktop\\model_example.index",
#                                 interactive=True,
#                             )
#                             file_index2 = gr.Dropdown(
#                                 label=i18n("自动检测index路径,下拉式选择(dropdown)"),
#                                 choices=sorted(index_paths),
#                                 interactive=True,
#                             )
#                             f0method0 = gr.Radio(
#                                 label=i18n(
#                                     "选择音高提取算法,输入歌声可用pm提速,harvest低音好但巨慢无比,crepe效果好但吃GPU,rmvpe效果最好且微吃GPU"
#                                 ),
#                                 choices=["pm", "harvest", "crepe", "rmvpe"]
#                                 if config.dml == False
#                                 else ["pm", "harvest", "rmvpe"],
#                                 value="rmvpe",
#                                 interactive=True,
#                             )

#                         with gr.Column():
#                             resample_sr0 = gr.Slider(
#                                 minimum=0,
#                                 maximum=48000,
#                                 label=i18n("后处理重采样至最终采样率，0为不进行重采样"),
#                                 value=0,
#                                 step=1,
#                                 interactive=True,
#                             )
#                             rms_mix_rate0 = gr.Slider(
#                                 minimum=0,
#                                 maximum=1,
#                                 label=i18n("输入源音量包络替换输出音量包络融合比例，越靠近1越使用输出包络"),
#                                 value=0.25,
#                                 interactive=True,
#                             )
#                             protect0 = gr.Slider(
#                                 minimum=0,
#                                 maximum=0.5,
#                                 label=i18n(
#                                     "保护清辅音和呼吸声，防止电音撕裂等artifact，拉满0.5不开启，调低加大保护力度但可能降低索引效果"
#                                 ),
#                                 value=0.33,
#                                 step=0.01,
#                                 interactive=True,
#                             )
#                             filter_radius0 = gr.Slider(
#                                 minimum=0,
#                                 maximum=7,
#                                 label=i18n(
#                                     ">=3则使用对harvest音高识别的结果使用中值滤波，数值为滤波半径，使用可以削弱哑音"
#                                 ),
#                                 value=3,
#                                 step=1,
#                                 interactive=True,
#                             )
#                             index_rate1 = gr.Slider(
#                                 minimum=0,
#                                 maximum=1,
#                                 label=i18n("检索特征占比"),
#                                 value=0.75,
#                                 interactive=True,
#                             )
#                             f0_file = gr.File(
#                                 label=i18n("F0曲线文件, 可选, 一行一个音高, 代替默认F0及升降调"),
#                                 visible=False,
#                             )

#                             refresh_button.click(
#                                 fn=change_choices,
#                                 inputs=[],
#                                 outputs=[sid0, file_index2],
#                                 api_name="infer_refresh",
#                             )
#                             # file_big_npy1 = gr.Textbox(
#                             #     label=i18n("特征文件路径"),
#                             #     value="E:\\codes\py39\\vits_vc_gpu_train\\logs\\mi-test-1key\\total_fea.npy",
#                             #     interactive=True,
#                             # )
#                 with gr.Group():
#                     with gr.Column():
#                         but0 = gr.Button(i18n("转换"), variant="primary")
#                         with gr.Row():
#                             vc_output1 = gr.Textbox(label=i18n("输出信息"))
#                             vc_output2 = gr.Audio(label=i18n("输出音频(右下角三个点,点了可以下载)"))

#                         but0.click(
#                             vc.vc_single,
#                             [
#                                 spk_item,
#                                 input_audio0,
#                                 vc_transform0,
#                                 f0_file,
#                                 f0method0,
#                                 file_index1,
#                                 file_index2,
#                                 # file_big_npy1,
#                                 index_rate1,
#                                 filter_radius0,
#                                 resample_sr0,
#                                 rms_mix_rate0,
#                                 protect0,
#                             ],
#                             [vc_output1, vc_output2],
#                             api_name="infer_convert",
#                         )
#             with gr.TabItem(i18n("批量推理")):
#                 gr.Markdown(
#                     value=i18n("批量转换, 输入待转换音频文件夹, 或上传多个音频文件, 在指定文件夹(默认opt)下输出转换的音频. ")
#                 )
#                 with gr.Row():
#                     with gr.Column():
#                         vc_transform1 = gr.Number(
#                             label=i18n("变调(整数, 半音数量, 升八度12降八度-12)"), value=0
#                         )
#                         opt_input = gr.Textbox(label=i18n("指定输出文件夹"), value="opt")
#                         file_index3 = gr.Textbox(
#                             label=i18n("特征检索库文件路径,为空则使用下拉的选择结果"),
#                             value="",
#                             interactive=True,
#                         )
#                         file_index4 = gr.Dropdown(
#                             label=i18n("自动检测index路径,下拉式选择(dropdown)"),
#                             choices=sorted(index_paths),
#                             interactive=True,
#                         )
#                         f0method1 = gr.Radio(
#                             label=i18n(
#                                 "选择音高提取算法,输入歌声可用pm提速,harvest低音好但巨慢无比,crepe效果好但吃GPU,rmvpe效果最好且微吃GPU"
#                             ),
#                             choices=["pm", "harvest", "crepe", "rmvpe"]
#                             if config.dml == False
#                             else ["pm", "harvest", "rmvpe"],
#                             value="rmvpe",
#                             interactive=True,
#                         )
#                         format1 = gr.Radio(
#                             label=i18n("导出文件格式"),
#                             choices=["wav", "flac", "mp3", "m4a"],
#                             value="wav",
#                             interactive=True,
#                         )

#                         refresh_button.click(
#                             fn=lambda: change_choices()[1],
#                             inputs=[],
#                             outputs=file_index4,
#                             api_name="infer_refresh_batch",
#                         )
#                         # file_big_npy2 = gr.Textbox(
#                         #     label=i18n("特征文件路径"),
#                         #     value="E:\\codes\\py39\\vits_vc_gpu_train\\logs\\mi-test-1key\\total_fea.npy",
#                         #     interactive=True,
#                         # )

#                     with gr.Column():
#                         resample_sr1 = gr.Slider(
#                             minimum=0,
#                             maximum=48000,
#                             label=i18n("后处理重采样至最终采样率，0为不进行重采样"),
#                             value=0,
#                             step=1,
#                             interactive=True,
#                         )
#                         rms_mix_rate1 = gr.Slider(
#                             minimum=0,
#                             maximum=1,
#                             label=i18n("输入源音量包络替换输出音量包络融合比例，越靠近1越使用输出包络"),
#                             value=1,
#                             interactive=True,
#                         )
#                         protect1 = gr.Slider(
#                             minimum=0,
#                             maximum=0.5,
#                             label=i18n(
#                                 "保护清辅音和呼吸声，防止电音撕裂等artifact，拉满0.5不开启，调低加大保护力度但可能降低索引效果"
#                             ),
#                             value=0.33,
#                             step=0.01,
#                             interactive=True,
#                         )
#                         filter_radius1 = gr.Slider(
#                             minimum=0,
#                             maximum=7,
#                             label=i18n(">=3则使用对harvest音高识别的结果使用中值滤波，数值为滤波半径，使用可以削弱哑音"),
#                             value=3,
#                             step=1,
#                             interactive=True,
#                         )
#                         index_rate2 = gr.Slider(
#                             minimum=0,
#                             maximum=1,
#                             label=i18n("检索特征占比"),
#                             value=1,
#                             interactive=True,
#                         )
#                 with gr.Row():
#                     dir_input = gr.Textbox(
#                         label=i18n("输入待处理音频文件夹路径(去文件管理器地址栏拷就行了)"),
#                         placeholder="C:\\Users\\Desktop\\input_vocal_dir",
#                     )
#                     inputs = gr.File(
#                         file_count="multiple", label=i18n("也可批量输入音频文件, 二选一, 优先读文件夹")
#                     )

#                 with gr.Row():
#                     but1 = gr.Button(i18n("转换"), variant="primary")
#                     vc_output3 = gr.Textbox(label=i18n("输出信息"))

#                     but1.click(
#                         vc.vc_multi,
#                         [
#                             spk_item,
#                             dir_input,
#                             opt_input,
#                             inputs,
#                             vc_transform1,
#                             f0method1,
#                             file_index3,
#                             file_index4,
#                             # file_big_npy2,
#                             index_rate2,
#                             filter_radius1,
#                             resample_sr1,
#                             rms_mix_rate1,
#                             protect1,
#                             format1,
#                         ],
#                         [vc_output3],
#                         api_name="infer_convert_batch",
#                     )
#                 sid0.change(
#                     fn=vc.get_vc,
#                     inputs=[sid0, protect0, protect1],
#                     outputs=[spk_item, protect0, protect1, file_index2, file_index4],
#                     api_name="infer_change_voice",
#                 )
#         with gr.TabItem(i18n("伴奏人声分离&去混响&去回声")):
#             with gr.Group():
#                 gr.Markdown(
#                     value=i18n(
#                         "人声伴奏分离批量处理， 使用UVR5模型。 <br>合格的文件夹路径格式举例： E:\\codes\\py39\\vits_vc_gpu\\白鹭霜华测试样例(去文件管理器地址栏拷就行了)。 <br>模型分为三类： <br>1、保留人声：不带和声的音频选这个，对主人声保留比HP5更好。内置HP2和HP3两个模型，HP3可能轻微漏伴奏但对主人声保留比HP2稍微好一丁点； <br>2、仅保留主人声：带和声的音频选这个，对主人声可能有削弱。内置HP5一个模型； <br> 3、去混响、去延迟模型（by FoxJoy）：<br>  (1)MDX-Net(onnx_dereverb):对于双通道混响是最好的选择，不能去除单通道混响；<br>&emsp;(234)DeEcho:去除延迟效果。Aggressive比Normal去除得更彻底，DeReverb额外去除混响，可去除单声道混响，但是对高频重的板式混响去不干净。<br>去混响/去延迟，附：<br>1、DeEcho-DeReverb模型的耗时是另外2个DeEcho模型的接近2倍；<br>2、MDX-Net-Dereverb模型挺慢的；<br>3、个人推荐的最干净的配置是先MDX-Net再DeEcho-Aggressive。"
#                     )
#                 )
#                 with gr.Row():
#                     with gr.Column():
#                         dir_wav_input = gr.Textbox(
#                             label=i18n("输入待处理音频文件夹路径"),
#                             placeholder="C:\\Users\\Desktop\\todo-songs",
#                         )
#                         wav_inputs = gr.File(
#                             file_count="multiple", label=i18n("也可批量输入音频文件, 二选一, 优先读文件夹")
#                         )
#                     with gr.Column():
#                         model_choose = gr.Dropdown(label=i18n("模型"), choices=uvr5_names)
#                         agg = gr.Slider(
#                             minimum=0,
#                             maximum=20,
#                             step=1,
#                             label="人声提取激进程度",
#                             value=10,
#                             interactive=True,
#                             visible=False,  # 先不开放调整
#                         )
#                         opt_vocal_root = gr.Textbox(
#                             label=i18n("指定输出主人声文件夹"), value="opt"
#                         )
#                         opt_ins_root = gr.Textbox(
#                             label=i18n("指定输出非主人声文件夹"), value="opt"
#                         )
#                         format0 = gr.Radio(
#                             label=i18n("导出文件格式"),
#                             choices=["wav", "flac", "mp3", "m4a"],
#                             value="flac",
#                             interactive=True,
#                         )
#                     but2 = gr.Button(i18n("转换"), variant="primary")
#                     vc_output4 = gr.Textbox(label=i18n("输出信息"))
#                     but2.click(
#                         uvr,
#                         [
#                             model_choose,
#                             dir_wav_input,
#                             opt_vocal_root,
#                             wav_inputs,
#                             opt_ins_root,
#                             agg,
#                             format0,
#                         ],
#                         [vc_output4],
#                         api_name="uvr_convert",
#                     )
        
#         tab_faq = i18n("常见问题解答")
#         with gr.TabItem(tab_faq):
#             try:
#                 if tab_faq == "常见问题解答":
#                     with open("docs/cn/faq.md", "r", encoding="utf8") as f:
#                         info = f.read()
#                 else:
#                     with open("docs/en/faq_en.md", "r", encoding="utf8") as f:
#                         info = f.read()
#                 gr.Markdown(value=info)
#             except:
#                 gr.Markdown(traceback.format_exc())

#     if config.iscolab:
#         app.queue(concurrency_count=511, max_size=1022).launch(share=True)
#     else:
#         app.queue(concurrency_count=511, max_size=1022).launch(
#             server_name="0.0.0.0",
#             inbrowser=not config.noautoopen,
#             server_port=config.listen_port,
#             quiet=True,
#         )
