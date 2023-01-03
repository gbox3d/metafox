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
from yolov5SegModel import Yolov5SegModel

from http_thread import httpServerThread

#%%
_out_img = None
class myHandler(SimpleHTTPRequestHandler):
    
    def end_headers (self):
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET')
        self.send_header('Cache-Control', 'no-store, no-cache, must-revalidate')
        return super(myHandler, self).end_headers()
    
	#Handler for the GET requests
    def do_GET(self):
        
        print("self.path: ", self.path)
    
        try:
            if self.path=="/getimg":
                self.send_response(200,"ok")
                # self.send_header('Access-Control-Allow-Origin', '*')
                # self.send_header('Access-Control-Allow-Methods', 'GET')
                # self.send_header("Access-Control-Allow-Headers", "Content-type")
                
                self.send_header('Content-type','image/png')
                self.end_headers()
                
                if _out_img is not None :
                    # encode_param=[int(cv.IMWRITE_JPEG_QUALITY),90]
                    _,_encodee_img = cv.imencode('.png',_out_img, [int(cv.IMWRITE_PNG_COMPRESSION), 0])
                    self.wfile.write(_encodee_img.tobytes())

                    # self.wfile.write(cv.imencode('.png', _out_img))
                    # self.wfile.write(cv.imencode('.png', _out_img))
            else :
                self.send_response(200)
                self.send_header('Content-type','text/html')
                self.end_headers()
                self.wfile.write(bytes("Hello World !", "utf8"))
                
            
        #     self.path="/index_example2.html"
   
        # try:
		# 	#Check the file extension required and
		# 	#set the right mime type
        #     sendReply = False
        #     if self.path.endswith(".html"):
        #         mimetype='text/html'
        #         sendReply = True
        #     if self.path.endswith(".jpg"):
        #         mimetype='image/jpeg'
        #         sendReply = True
        #     if self.path.endswith(".gif"):
        #         mimetype='image/gif'
        #         sendReply = True
        #     if self.path.endswith(".js"):
        #         mimetype='application/javascript'
        #         sendReply = True
        #     if self.path.endswith(".css"):
        #         mimetype='text/css'
        #         sendReply = True

        #     if sendReply == True:
        #         #Open the static file requested and send it
        #         # f = open(curdir + sep + self.path) 
        #         with open(curdir + sep + self.path, 'rb') as f:
        #             self.send_response(200)
        #             self.send_header('Content-type',mimetype)
        #             self.end_headers()
        #             self.wfile.write(f.read())
            return

        except IOError:
            self.send_error(404,'File Not Found: %s' % self.path)

_http_thread = httpServerThread(8080, myHandler)
_http_thread.start()

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
# with torch.no_grad(): # 이렇게 안하면 추론을 반복시행하면 메모리 오버플로우발생
    
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
        
        # total_np_mask_img = np.zeros((im0.shape[0],im0.shape[1]),dtype=np.uint8)
        
        _,_,masks,segments,box_infos = _model.predict(im0 ,conf_thres=confidence)


        if masks is not None:
            
            # print('mask count :' , len(masks) )
            
            # total_mask_img = np.zeros(masks[0].shape,dtype=np.uint8)
            total_np_mask_img = np.zeros(masks[0].shape,dtype=np.uint8)
            out_img = cv.resize(out_img,masks[0].shape[:2][::-1])
            
            for i in range(len(masks)):
                mask = masks[i]
                
                if box_infos[i][5].item() == 0 : #person
                    np_mask_img = np.asarray((mask)*255,dtype=np.uint8)
                    total_np_mask_img = cv.bitwise_or(total_np_mask_img,np_mask_img)
            
            _total_np_mask_img = cv.cvtColor(total_np_mask_img,cv.COLOR_GRAY2BGRA)
            _total_np_mask_img[:,:,3] = total_np_mask_img
        
        if bShow : 
            _out_img = cv.cvtColor(out_img, cv.COLOR_BGR2BGRA)
            _out_img[:,:,3] = 255 #alpha
            _out_img = cv.bitwise_and(_out_img,_total_np_mask_img) # apply mask
            
            cv.imshow('frame',_out_img)
            # cv.imwrite('./out.png',_out_img)
        
        if cv.waitKey(1) == 27:
            break
        elif cv.waitKey(1) == ord('s'):
            cv.imwrite('./out.png',out_img)
            cv.imwrite('./_out.png',_out_img)
            print('save image')
        
        
        # break;
        
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
        _http_thread.stop()
        
        # time.sleep(2)
        # print('closing server socket')