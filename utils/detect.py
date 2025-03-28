"""
Copyright (R) @huawei.com, all rights reserved
-*- coding:utf-8 -*-
CREATED:  2023-05-25 09:12:13
MODIFIED: 2023-05-25 10:10:55
"""


# import videocapture as video
import numpy as np
import cv2
import sys
sys.path.append("/root/ACLLite/python")  # 添加到文件开头
import time 

from acllite_resource import AclLiteResource
from acllite_model import AclLiteModel
from acllite_imageproc import AclLiteImageProc
from acllite_image import AclLiteImage
from acllite_logger import log_error, log_info

labels = ["0", "1", "2", "3", "4", "5", "6", "7", "8", "9"]

class sampleYOLOV7(object):
    '''load the model, and do preprocess, infer, postprocess'''
    def __init__(self, model_path, model_width, model_height):
        self.model_path = model_path
        self.model_width = model_width
        self.model_height = model_height

    def init_resource(self):
        # initial acl resource, create image processor, create model
        self._resource = AclLiteResource()
        self._resource.init()
    
        self._dvpp = AclLiteImageProc(self._resource) 
        self._model = AclLiteModel(self.model_path)

    def preprocess(self, frame):
        # resize frame, keep original image
        self.src_image = frame
        self.resized_image = cv2.resize(frame, (self.model_width, self.model_height))
        self.resized_image = self.resized_image.transpose(2,0,1)[np.newaxis,:]

    def infer(self):
        # infer frame
        self.result = self._model.execute([self.resized_image])
    
    @staticmethod
    def nms(boxes, scores, iou_threshold=0.5):
    # 按置信度排序
        order = scores.argsort()[::-1]
        keep = []
        
        while order.size > 0:
            # 保留置信度最高的框
            keep.append(order[0])
            if order.size == 1:
                break
                
            # 计算IoU
            xx1 = np.maximum(boxes[order[0], 0], boxes[order[1:], 0])
            yy1 = np.maximum(boxes[order[0], 1], boxes[order[1:], 1])
            xx2 = np.minimum(boxes[order[0], 2], boxes[order[1:], 2])
            yy2 = np.minimum(boxes[order[0], 3], boxes[order[1:], 3])
            
            w = np.maximum(0.0, xx2 - xx1)
            h = np.maximum(0.0, yy2 - yy1)
            inter = w * h
            
            area1 = (boxes[order[0], 2] - boxes[order[0], 0]) * (boxes[order[0], 3] - boxes[order[0], 1])
            area2 = (boxes[order[1:], 2] - boxes[order[1:], 0]) * (boxes[order[1:], 3] - boxes[order[1:], 1])
            iou = inter / (area1 + area2 - inter)
            
            # 删除IoU大于阈值的框
            inds = np.where(iou <= iou_threshold)[0]
            order = order[inds + 1]
            
        return keep
    def postprocess(self):
        predictions = self.result[0]
        h, w, _ = self.src_image.shape 
        scale_x = w / self.model_width
        scale_y = h / self.model_height

        # 解析预测结果
        predictions = predictions.reshape(-1, predictions.shape[-1])
        confidences = predictions[:, 4]
        class_scores = predictions[:, 5:]
        class_ids = np.argmax(class_scores, axis=1)
        
        # 修改: 只保留每个类别置信度最高的框
        keep_boxes = []
        for cls in np.unique(class_ids):
            cls_mask = (class_ids == cls)
            cls_boxes = predictions[cls_mask]
            cls_conf = confidences[cls_mask]
            
            # 只保留置信度最高的一个框
            if len(cls_conf) > 0:
                highest_conf_idx = np.argmax(cls_conf)
                cls_idx = np.where(cls_mask)[0][highest_conf_idx]
                keep_boxes.append(cls_idx)
        
        # 过滤低置信度
        keep_boxes = np.array(keep_boxes)
        final_mask = confidences[keep_boxes] > 0.70
        boxes = predictions[keep_boxes, :4][final_mask]
        confidences = confidences[keep_boxes][final_mask]
        class_ids = class_ids[keep_boxes][final_mask]

        # 绘制检测结果
        for box, conf, cls_id in zip(boxes, confidences, class_ids):
            x1, y1, x2, y2 = (box * [scale_x, scale_y, scale_x, scale_y]).astype(int)
            label = f"{labels[cls_id]} {conf:.2f}"
            cv2.rectangle(self.src_image, (x1,y1), (x2,y2), (0,255,0), 2)
            cv2.putText(self.src_image, label, (x1, max(y1-20,10)), 
                        cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0,255,0), 2)
        
        cv2.imshow('Detection', self.src_image)
    def release_resource(self):
        # release resource includes acl resource, data set and unload model
        del self._resource
        del self._dvpp
        del self._model
        del self.resized_image

def find_camera_index():
    max_index_to_check = 10  # Maximum index to check for camera
    for index in range(max_index_to_check):
        cap = cv2.VideoCapture(index)
        if cap.read()[0]:
            cap.release()
            return index
    # If no camera is found
    raise ValueError("No camera found.")


if __name__ == '__main__':
    model_path = '/root/thuei-1/EdgeAndRobotics/Samples/YOLOV5USBCamera/model/numbers.om'
    model_width = 640
    model_height = 640
    model = sampleYOLOV7(model_path, model_width, model_height)
    model.init_resource()

    # camera_index = find_camera_index()
    cap = cv2.VideoCapture(0)
    cv2.namedWindow('out', cv2.WINDOW_NORMAL)
    while True:
        ret, frame = cap.read()
        if not ret:  
            print("Can't receive frame (stream end?). Exiting ...")  
            break  
        # print(f"图像形状: {frame.shape}") 
        # frame = cv2.resize(frame, (640, 640)) 
        # print(f"图像形状: {frame.shape}") 
        print(model.model_height,model.model_width, frame.shape, model.model_path)
        model.preprocess(frame)
        model.infer()
        model.postprocess()
        # cv2.imshow('Frame', frame)
        if cv2.waitKey(1) & 0xFF == ord('q'):  
            break  
    cap.release()  
    cv2.destroyAllWindows()
    
    model.release_resource()
