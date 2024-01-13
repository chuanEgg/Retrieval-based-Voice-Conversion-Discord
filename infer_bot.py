import os
import sys
from dotenv import load_dotenv
from infer.modules.vc.modules import VC
from infer.modules.uvr5.modules import uvr
from configs.config import Config

class voice_converter:
    def __init__(self):
        now_dir = os.getcwd()
        sys.path.append(now_dir)
        load_dotenv()
        config = Config()
        self.vc = VC(config)

    def vocal_extract(self,
                      model_choose = 'HP5_only_main_vocal',
                      dir_wav_input = 'E:\\Retrieval-based-Voice-Conversion-Discord\\audio',
                      opt_vocal_root = 'opt',
                      wav_inputs = None,
                      opt_ins_root = 'opt',
                      agg = 10,
                      format0 = 'wav'):
        print(dir_wav_input)
        # HP5_only_main_vocal E:\Retrieval-based-Voice-Conversion-Discord\audio opt None opt 10 mp3
        uvr(model_name=model_choose, 
            inp_root=dir_wav_input, 
            save_root_vocal=opt_vocal_root, 
            paths=wav_inputs, 
            save_root_ins=opt_ins_root, 
            agg=agg, 
            format0=format0)
        
    def change_sid(self, sid = 'nyan.pth'):
        self.vc.get_vc(sid)
    
    def infer(self,
              sid = 0,
              input_audio0 = None, 
              vc_transform0 = -12, 
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
    # obj.change_sid()
    # now_dir = os.getcwd()
    # res = obj.infer(input_audio0='E:\\Retrieval-based-Voice-Conversion-Discord\\test.wav',
    #                 vc_transform0=-12)
    # import numpy as np
    # from scipy.io.wavfile import write
    # rate = res[0]
    # write('result.wav', rate, res[1])
    obj.vocal_extract()
