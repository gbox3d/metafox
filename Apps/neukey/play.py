#%%
import socket
from struct import *
import json
from turtle import width
import yaml
import torch

import cv2 as cv 
import sys
import time 
import numpy as np
import datetime
import os
from struct import *
from pathlib import Path

FILE = Path(__file__).resolve()
ROOT = FILE.parents[2]  # project root directory ../../

if str(ROOT) not in sys.path:
    sys.path.append(str(ROOT))  # add ROOT to PATH
    print('add ROOT to PATH' , str(ROOT))
    
ROOT = Path(os.path.relpath(ROOT, Path.cwd()))  # relative

# import udpServer

from modules.dariusVision import lastest_Cam2
from modules.etc import isnotebook
from yolov5SegModel import Yolov5SegModel

#%%

with open( Path.joinpath( ROOT ,'Apps/neukey/config.yaml') , 'r') as f:
    config_data = yaml.load(f,Loader=yaml.FullLoader)
    print(config_data)
    # outputDir = config_data['outputDir']
    width = config_data['width']
    height = config_data['height']
    imgsz = config_data['imgsz']
    port = config_data['port']
    source = config_data['source']
    bShow = config_data['bShow']
    weights = config_data['weights']
    device_select = config_data['device']
    bFlip = config_data['flip']
    confidence = config_data['confidence']
    player_keypoint = config_data['player_keypoint']
    player_keypoint_radius = config_data['player_keypoint_radius']
    # bShow = config_data['show']

#%%
lcam = None
if source.isnumeric() :
    lcam = lastest_Cam2(vid_src=int(source),width=width,height=height,grab_delay=0.02,bShow=bShow)
    print(f'cam {source} open ')
else:
    print('source is not numeric' , source)

#%%
with torch.no_grad(): # 이렇게 안하면 추론을 반복시행하면 메모리 오버플로우발생
    
    _model = Yolov5SegModel(weights=weights, imgsz=(imgsz, imgsz),device='' ,bs=1,dnn=False,half=False)
    
    print('load model done')
    print(f"model stride: {_model.stride} , imgsz: {_model.imgsz}")
    print("name: ", _model.names)

    try :
        while True:
                
            if source.isnumeric() :
                ret ,frame = lcam.read()
            else :
                frame = cv.imread(source)
                ret = True
            
            if bFlip :
                frame = cv.flip(frame, 1)
            
            im0 = frame.copy()
            out_img = im0.copy()
            
            _,_,masks,segments,box_infos = _model.predict(im0 ,conf_thres=confidence)

            if masks is not None:
                
                for i in range(len(masks)):
                    mask = masks[i]
                    _seg = segments[i]
                    
                    np_mask_img = np.asarray((mask)*255,dtype=np.uint8)
                    out_img = cv.bitwise_and(out_img,out_img,mask=np_mask_img)
            
            if bShow : 
                cv.imshow('frame',out_img)
            
            if cv.waitKey(1) == 27:
                break
            
    except Exception as ex:
        print(f'error : {ex}')
        time.sleep(1)
        # exit()
    except KeyboardInterrupt :
        print('exiting....')
        time.sleep(1)
    finally :
        if lcam != None:
            lcam.stop()
        # time.sleep(2)
        # print('closing server socket')