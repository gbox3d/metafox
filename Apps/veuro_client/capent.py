#%%
import socket
import io
import struct

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

from pathlib import Path

from PIL import Image, ImageDraw, ImageFont
from IPython.display import display


from http.server import BaseHTTPRequestHandler,HTTPServer,SimpleHTTPRequestHandler

import shapely
from shapely.geometry import Point, Polygon, LineString, GeometryCollection

FILE = Path(__file__).resolve()
ROOT = FILE.parents[2]  # project root directory ../../

if str(ROOT) not in sys.path:
    sys.path.append(str(ROOT))  # add ROOT to PATH
    print('add ROOT to PATH' , str(ROOT))    
ROOT = Path(os.path.relpath(ROOT, Path.cwd()))  # relative

# import udpServer
from modules.dariusVision import lastest_Cam2
from modules.etc import isnotebook
from veuroClientLib import veroTcpClient

#%%
with open( Path.joinpath( ROOT ,'Apps/neukey/config.yaml') , 'r') as f:
    config_data = yaml.load(f,Loader=yaml.FullLoader)
    print(config_data)
    remoteIP = config_data['remoteIP']
    remotePort = config_data['remotePort']
    source = config_data['source']
    height = config_data['height']
    width = config_data['width']
    bankId = config_data['bankId']
    

#%%
lcam = None
if source.isnumeric() :
    lcam = lastest_Cam2(vid_src=int(source),width=width,height=height,grab_delay=0.02)
    print(f'cam {source} open ')
else:
    print('source is not numeric' , source)

try :
    senderObj = veroTcpClient(remoteIP,remotePort,
                              buff_size=1024,bankId=bankId,timeout=0.5)
    senderObj.connect()
    
    time.sleep(1)
    print('start send data')
    
    while True:
        try :
            
            if source.isnumeric() :
                ret ,frame = lcam.read()
            else :
                frame = cv.imread(source)
                ret = True
                
            # frame = cv.resize(frame,(320,240))
            
            _,_encodee_img = cv.imencode('.png',frame)
            
            startTime = time.time()
            # senderClass.send_data(senderObj,_encodee_img.tobytes())
            senderObj.send_data(_encodee_img.tobytes())
            delay = time.time() - startTime
            print(f'network delay : {delay} sec , size : {len(_encodee_img.tobytes())}')
            
            cv.imshow('frame',frame)
            
            if cv.waitKey(1) == 27:
                print('esc break')
                
                break
            
        except Exception as ex:
            if type(ex) == socket.timeout :
                pass
            else :
                print(f'error : {ex}')
                time.sleep(1)
                break;
        
except Exception as ex:
    print(f'error : {ex}')
    # time.sleep(1)
    # exit()
except KeyboardInterrupt :
    print('exiting....')
    # time.sleep(1)
senderObj.close()
time.sleep(1)

time.sleep(1)
if lcam != None:
    lcam.stop()

print('exit')
        