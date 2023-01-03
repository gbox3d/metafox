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

class senderClass:
    checkcode = 20221223
    
    def __init__(self,ip,port,buff_size,bankId) :
        self.ip = ip
        self.port = port
        self.buff_size = buff_size
        self.bankId = bankId
    def connect(self) :
        try :
            self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.client_socket.connect((self.ip, self.port))
            self.client_socket.settimeout(60)
            
            _result = self.client_socket.recv(1024)
            _code,_cmd,_,_,_ = struct.unpack('<LBBBB', _result)
            print(f'code : {_code}, cmd : {_cmd}')
            
            if _cmd == 0 :
                print('connected ok')
            else :
                print('connected fail : error code ' , _cmd)
        except Exception as ex:
            print(f'error : {ex}')
    def send_ping(self) :
        _packpack = struct.pack('<LBBBB', self.checkcode,0x10,0,0,0)
        self.client_socket.sendall(_packpack)
        _result = self.client_socket.recv(1024)
        _code,_cmd,_,_,_ = struct.unpack('<LBBBB', _result)
        print(f'code : {_code}, cmd : {_cmd}')
        
    def send_data(self,data) :
        _data = data
        _header = struct.pack('<LBBBBLffLLL', self.checkcode,0x01,self.bankId,0,0,len(_data),0,0,0,0,0)
        self.client_socket.sendall(_header)
        self.client_socket.sendall(_data)
            
        # time.sleep(60)
            
        # _result = self.client_socket.recv(1024)
        
        # # print(f'result : {len(_result)}')
        # _code,_cmd,_,_,_,buff_size = struct.unpack('<LBBBBL', _result)
        # print(f'code : {_code}, cmd : {_cmd} , buff_size : {buff_size}')
        
        # return _cmd,_,_,_,buff_size
        
    def download(self) :
        
        _header = struct.pack('<LBBBB', self.checkcode,0x02,self.bankId,0,0)
        self.client_socket.sendall(_header)
        
        _result = self.client_socket.recv(1024)
        
        #read header
        _code,_cmd,_,_,_,buff_size = struct.unpack('<LBBBBL', _result[0:12])
        print(f'code : {_code}, cmd : {_cmd} , buff_size : {buff_size}')
        
        #read data
        _data = _result[12:]
        while len(_data) < buff_size :
            _data += self.client_socket.recv(1024)
        
        # display(Image.open(io.BytesIO(_data)))
        
        
    def close(self) :
        _packpack = struct.pack('<LBBBB', self.checkcode,0x99,0,0,0)
        self.client_socket.sendall(_packpack)
        _result = self.client_socket.recv(1024)
        _code,_cmd,_,_,_ = struct.unpack('<LBBBB', _result)
        print(f'code : {_code}, cmd : {_cmd}')
        self.client_socket.close()

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
    senderObj = senderClass(remoteIP,remotePort,1024,bankId)
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
            senderClass.send_data(senderObj,_encodee_img.tobytes())
            delay = time.time() - startTime
            print(f'network delay : {delay} sec , size : {len(_encodee_img.tobytes())}')
            
            cv.imshow('frame',frame)
            
            
            
            # if isnotebook() :
            #     display(Image.open(io.BytesIO(_encodee_img.tobytes())))
            
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
    time.sleep(1)
    # exit()
except KeyboardInterrupt :
    print('exiting....')
    time.sleep(1)

time.sleep(1)
if lcam != None:
    lcam.stop()
senderObj.close()
print('exit')
        