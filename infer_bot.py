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

class voice_converter:
    def __init__(self):
        self.config = Config()
        self.vc = VC(self.config)
        self.i18n = I18nAuto()
        self.names = []
        self.uvr5_names = []
        self.index_paths = []
        self.index_root = ""
        self.weight_root = ""
        self.weight_uvr5_root = ""
        
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

        if self.config.dml == True:
            def forward_dml(ctx, x, scale):
                ctx.scale = scale
                res = x.clone().detach()
                return res

            fairseq.modules.grad_multiply.GradMultiply.forward = forward_dml
        logger.info(self.i18n)
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
            gpu_info = self.i18n("很遗憾您这没有能用的显卡来支持您训练")
            default_batch_size = 1
        gpus = "-".join([i[0] for i in gpu_infos])
        self.weight_root = os.getenv("weight_root")
        self.weight_uvr5_root = os.getenv("weight_uvr5_root")
        self.index_root = os.getenv("index_root")
        self.names = []
        for name in os.listdir(self.weight_root):
            if name.endswith(".pth"):
                self.names.append(name)
        self.index_paths = []
        for root, dirs, files in os.walk(self.index_root, topdown=False):
            for name in files:
                if name.endswith(".index") and "trained" not in name:
                    self.index_paths.append("%s/%s" % (root, name))
        self.uvr5_names = []
        for name in os.listdir(self.weight_uvr5_root):
            if name.endswith(".pth") or "onnx" in name:
                self.uvr5_names.append(name.replace(".pth", ""))

    def change_sid(self, sid = 'nyan.pth', protect0 = 0.33, protect1 = 0.33):
        [spk_item, protect0, protect1, file_index2, file_index4] = self.vc.get_vc(sid, protect0, protect1)
        print(spk_item, protect0, protect1, file_index2, file_index4)
    
    def infer(self,
              sid = 0,
              spk_item = 0,
              input_audio0 = None, 
              vc_transform0 = 0.0, 
              f0_file = None, 
              f0method0 = 'rmvpe', 
              file_index1 = 'logs/nyan/added_IVF631_Flat_nprobe_1_nyan_v2.index', 
              file_index2 = None, 
              index_rate1 = 0.75, 
              filter_radius0 = 3, 
              resample_sr0 = 0, 
              rms_mix_rate0 = 0.25, 
              protect0 = 0.33
              ):
        [vc_output1, vc_output2] = self.vc.vc_single(
            sid,
            input_audio0,
            vc_transform0,
            f0_file,
            f0method0,
            file_index1,
            file_index2,
            # file_big_npy1,
            index_rate1,
            filter_radius0,
            resample_sr0,
            rms_mix_rate0,
            protect0,
        )
        # print(vc_output2)
        return vc_output2


if __name__ == "__main__":
    obj = voice_converter()
    obj.change_sid()
    now_dir = os.getcwd()
    res = obj.infer(input_audio0='E:\\Retrieval-based-Voice-Conversion-Discord\\test.wav',
                    vc_transform0=-12)
    import numpy as np
    from scipy.io.wavfile import write
    rate = res[0]
    write('result.wav', rate, res[1])
