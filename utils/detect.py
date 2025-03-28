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
sys.path.append('/root/thuei-1/sdk-python/')
import time 
import yaml_handle
import torch
import torch.nn as nn
from acllite_resource import AclLiteResource
from acllite_model import AclLiteModel
from acllite_imageproc import AclLiteImageProc
from acllite_image import AclLiteImage
from acllite_logger import log_error, log_info

labels = ["0", "1", "2", "3", "4", "5", "6", "7", "8", "9"]
# labels = ["kettle", "mop", "dishcloth"]
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
    def postprocess(self,  tuple):
        x, y, w, h, frame = tuple
        print(x, y, w, h)
        predictions = self.result[0]
        print(predictions)
        scale_x = w / self.model_width
        scale_y = h / self.model_height

        # 解析预测结果
        predictions = predictions.reshape(-1, predictions.shape[-1])
        confidences = predictions[:, 4]
        class_scores = predictions[:, 5:]
        class_ids = np.argmax(class_scores, axis=1)
        
        max_conf_idx = np.argmax(confidences)
        max_conf_class = class_ids[max_conf_idx]
        cv2.rectangle(frame, (x,y), (x+w,y+h), (0,255,0), 2)
        cv2.putText(frame, labels[max_conf_class], (x, max(y-20,10)), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0,255,0), 2)
        cv2.imshow('Detection', frame)
        # # 修改: 只保留每个类别置信度最高的框
        # keep_boxes = []
        # for cls in np.unique(class_ids):
        #     cls_mask = (class_ids == cls)
        #     cls_boxes = predictions[cls_mask]
        #     cls_conf = confidences[cls_mask]
            
        #     # 只保留置信度最高的一个框
        #     if len(cls_conf) > 0:
        #         highest_conf_idx = np.argmax(cls_conf)
        #         cls_idx = np.where(cls_mask)[0][highest_conf_idx]
        #         keep_boxes.append(cls_idx)
        
        # # 过滤低置信度
        # keep_boxes = np.array(keep_boxes)
        # final_mask = confidences[keep_boxes] > 0.70
        # boxes = predictions[keep_boxes, :4][final_mask]
        # confidences = confidences[keep_boxes][final_mask]
        # class_ids = class_ids[keep_boxes][final_mask]

        # 绘制检测结果
        # for box, conf, cls_id in zip(boxes, confidences, class_ids):
        #     x1, y1, x2, y2 = (box * [scale_x, scale_y, scale_x, scale_y]).astype(int)
        #     label = f"{labels[cls_id]} {conf:.2f}"
        #     cv2.rectangle(self.src_image, (x1,y1), (x2,y2), (0,255,0), 2)
        #     cv2.putText(self.src_image, label, (x1, max(y1-20,10)), 
        #                 cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0,255,0), 2)
        
        # cv2.imshow('Detection', self.src_image)
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

def preprocess_image(img):
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    

    
    # 形态学操作，去除小噪声
    kernel = np.ones((3, 3), np.uint8)
    binary = cv2.morphologyEx(gray, cv2.MORPH_CLOSE, kernel)
    cv2.imshow('binary', binary)
    return binary



class Net(nn.Module):
    def __init__(self):
        super(Net, self).__init__()
        self.conv1 = nn.Conv2d(1, 32, kernel_size=3, padding=1)
        self.conv2 = nn.Conv2d(32, 64, kernel_size=3, padding=1)
        self.conv3 = nn.Conv2d(64, 128, kernel_size=3, padding=1)
        self.fc1 = nn.Linear(128 * 3 * 3, 256)  # 根据实际形状调整
        self.fc2 = nn.Linear(256, 10)

    def forward(self, x):
        x = torch.relu(torch.max_pool2d(self.conv1(x), 2))
        x = torch.relu(torch.max_pool2d(self.conv2(x), 2))
        x = torch.relu(torch.max_pool2d(self.conv3(x), 2))
        x = x.view(x.size(0), -1)
        x = torch.relu(self.fc1(x))
        x = self.fc2(x)
        return x



if __name__ == '__main__':

    model_path = '/root/thuei-1/EdgeAndRobotics/Samples/YOLOV5USBCamera/model/numbers.om'
    model_width = 640
    model_height = 640
    model = sampleYOLOV7(model_path, model_width, model_height)
    model.init_resource()

    lab_data = yaml_handle.get_yaml_data(yaml_handle.lab_file_path)

    # camera_index = find_camera_index()
    cap = cv2.VideoCapture("/dev/video0")
    # cv2.namedWindow('out', cv2.WINDOW_NORMAL)
    while True:
    # while __isRunning:
        ret,frame = cap.read()
        if ret:
            frame_resize = cv2.resize(frame, (640, 480), interpolation=cv2.INTER_NEAREST)
            frame_gb = cv2.GaussianBlur(frame_resize, (3, 3), 3)  
            frame_mask = cv2.inRange(frame_gb,
                                             (lab_data['blue']['min'][0],
                                              lab_data['blue']['min'][1],
                                              lab_data['blue']['min'][2]),
                                             (lab_data['blue']['max'][0],
                                              lab_data['blue']['max'][1],
                                              lab_data['blue']['max'][2]))  #对原图像和掩模进行位运算
            opened = cv2.morphologyEx(frame_mask, cv2.MORPH_OPEN, np.ones((3, 3),np.uint8))  #开运算
            closed = cv2.morphologyEx(opened, cv2.MORPH_CLOSE, np.ones((3, 3),np.uint8)) #闭运算
            closed[:, 0:100] = 0
            contours = cv2.findContours(closed, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)[-2]  #找出轮廓
            print(contours)
            
            for cnt in contours:
                x, y, w, h = cv2.boundingRect(cnt)
                if w * h > 300 and w * h < 10000:
                    roi = frame[y:y+h, x:x+w]
                    # model.preprocess(roi)
                    # model.infer()
                    # model.postprocess( (x, y, w, h, frame))
                    model = Net()
                    model.load_state_dict(torch.load("enhanced_mnist_model.pt"))
                    model.eval()
                    with torch.no_grad():
                        roi = cv2.resize(roi, (28, 28))
                        roi = cv2.cvtColor(roi, cv2.COLOR_BGR2GRAY)
                        roi = roi.reshape( 1, 28, 28)
                        output = model(torch.from_numpy(roi).unsqueeze(0).float())
                        prediction = torch.argmax(output).item()
                    cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 2)
                    cv2.putText(frame, str(prediction), (x, y - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)
                    cv2.imshow('Number Detection', frame)
        

            cv2.imshow('Number Detection', frame)
            key = cv2.waitKey(1)
            if key == 27:
                break
        else:
            time.sleep(0.01)
            print("no frame")    
    cv2.destroyAllWindows()

    model.release_resource()
    


# url = "https://github.com/pytorch/examples/raw/main/mnist/pretrained_model.pt"
# torch.save(torch.hub.load_state_dict_from_url(url, map_location=torch.device('cpu')), "mnist_model.pt")

# # 加载模型并识别图片
# model = torch.load("mnist_model.pt") if torch.cuda.is_available() or torch.backends.mps.is_available() else torch.load("mnist_model.pt", map_location=torch.device('cpu'))
# transform = transforms.Compose([transforms.Resize((28, 28)), transforms.ToTensor(), transforms.Normalize((0.1307,), (0.3081,))])
# print(f"识别结果: {torch.argmax(model(transform(Image.open('digit.png').convert('L')).unsqueeze(0))).item()}")