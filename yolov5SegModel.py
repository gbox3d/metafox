import torch
import numpy as np

from models.common import DetectMultiBackend
from utils.dataloaders import IMG_FORMATS, VID_FORMATS, LoadImages, LoadScreenshots, LoadStreams
from utils.general import (LOGGER, Profile, check_file, check_img_size, check_imshow, check_requirements, colorstr, cv2,
                           increment_path, non_max_suppression, print_args, scale_boxes, scale_segments,
                           strip_optimizer)
from utils.plots import Annotator, colors, save_one_box
from utils.segment.general import masks2segments, process_mask, process_mask_native
from utils.torch_utils import select_device, smart_inference_mode

from utils.augmentations import (Albumentations, augment_hsv, classify_albumentations, classify_transforms, copy_paste,
                                 letterbox, mixup, random_perspective)

class Yolov5SegModel():
    def __init__(self, weights='yolov5s-seg.pt', imgsz=(640, 640),device='' ,bs=1,dnn=False,half=False):
        self.weights = weights
        self.imgsz = imgsz
        self.bs = bs
        self.device = select_device(device) # CUDA:0,1,2,3 or CPU
        
        #load model
        self.model = DetectMultiBackend(weights=weights, device=self.device, dnn=dnn, fp16=half)
        self.stride, self.names, self.pt = self.model.stride, self.model.names, self.model.pt
        self.imgsz = check_img_size(imgsz, s=self.stride)  # check image size
        self.model.warmup(imgsz=(1 if self.pt else bs, 3, *imgsz))  # warmup
        
        self.__version__ = '0.0.1'
    
        
    def predict(self,img,classes=None,conf_thres=0.25,iou_thres=0.45,max_det=1000,agnostic_nms=False,retina_masks=False):
        im = letterbox(img, new_shape=self.imgsz)[0]
        im = im.transpose(2, 0, 1)[None]
        im = np.ascontiguousarray(im)  # contiguous
    
        im = torch.from_numpy(im).to( self.model.device)
        im = im.half() if self.model.fp16 else im.float()  # uint8 to fp16/32
        im /= 255  # 0 - 255 to 0.0 - 1.0
        if len(im.shape) == 3:
            im = im[None]  # expand for batch dim
        
        # bs=1
        # model.warmup(imgsz=(1 if pt else bs, 3, *imgsz))  # warmup
        pred, proto = self.model(im, augment=False, visualize=False)[:2]
        pred = non_max_suppression(pred, conf_thres, iou_thres, classes, agnostic_nms, max_det=max_det, nm=32)
        
        im0 = img.copy()
        
        masks = None
        segments = None
        
        for i, det in enumerate(pred):  # per image
        # print(i,det)
            if len(det) > 0:
                masks = process_mask(proto[i], det[:, 6:], det[:, :4], im.shape[2:], upsample=True)  # HWC
                det[:, :4] = scale_boxes(im.shape[2:], det[:, :4], im0.shape).round()  # rescale boxes to im0 size
            
                segments = [
                    scale_segments(im0.shape if retina_masks else im.shape[2:], x, im0.shape, normalize=True)
                    for x in reversed(masks2segments(masks))
                    ]
        
        return pred, proto, masks, segments, [ (*xyxy,conf,cls) for i, (*xyxy, conf, cls) in enumerate(reversed(det[:, :6])) ]
        
        
        