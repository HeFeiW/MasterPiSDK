


#!/usr/bin/python3
# coding=utf8
import sys
sys.path.append('/root/thuei-1/sdk-python/')
import cv2
import time
import math
import signal
import threading
import numpy as np
import yaml_handle
from ArmIK.Transform import *
from ArmIK.ArmMoveIK import *
import HiwonderSDK.Misc as Misc
import HiwonderSDK.Board as Board
from HiwonderSDK.PID import PID
reach_the_end = False
horizontal_detected = False
cap = None
AK = ArmIK()
pitch_pid = PID(P=0.28, I=0.16, D=0.18)

range_rgb = {
    'red': (0, 0, 255),
    'blue': (255, 0, 0),
    'green': (0, 255, 0),
    'black': (0, 0, 0),
    'white': (255, 255, 255),
}

# 巡线
if sys.version_info.major == 2:
    print('Please run this program with python3!')
    sys.exit(0)


# 设置检测颜色
def setTargetColor(target_color):
    global __target_color

    print("COLOR", target_color)
    __target_color = target_color
    return (True, ())

lab_data = None

def load_config():
    global lab_data
    lab_data = yaml_handle.get_yaml_data(yaml_handle.lab_file_path)

# 初始位置
def initMove():
    
    Board.setPWMServoPulse(1, 1500, 800)
    AK.setPitchRangeMoving((0, 7, 11), -60, -90, 0, 1500)
    MotorStop()
    
line_centerx = -1
# 变量重置
def reset():
    global line_centerx
    global __target_color
    
    line_centerx = -1
    __target_color = ()
    
# app初始化调用
def init():
    print("VisualPatrol Init")
    load_config()
    initMove()

__isRunning = False
# app开始玩法调用
def start():
    global __isRunning
    reset()
    __isRunning = True
    print("VisualPatrol Start")

# app停止玩法调用
def stop():
    global __isRunning
    __isRunning = False
    MotorStop()
    print("VisualPatrol Stop")

# app退出玩法调用
def exit():
    global __isRunning
    __isRunning = False
    MotorStop()
    print("VisualPatrol Exit")

def setBuzzer(timer):
    Board.setBuzzer(0)
    Board.setBuzzer(1)
    time.sleep(timer)
    Board.setBuzzer(0)

def MotorStop():
    Board.setMotor(1, 0) 
    Board.setMotor(2, 0)
    Board.setMotor(3, 0)
    Board.setMotor(4, 0)
 
#关闭前处理
def Stop(signum, frame):
    global __isRunning
    
    __isRunning = False
    print('关闭中...')
    MotorStop()  # 关闭所有电机
    if cap is not None:
        print('releasing cap at stop')
        cap.release()
import cv2
from paddleocr import PaddleOCR
import easyocr
import cv2
import numpy as np
import torch
import torchvision.transforms as transforms
from PIL import Image

import sys
sys.path.append('/root/thuei-1/crnn.pytorch/models/')
from crnn import CRNN
# 加载预训练 CRNN 模型
model_path = "/root/thuei-1/crnn.pytorch/data/crnn.pth"
model = CRNN(32, 1, 37, 256)
model.load_state_dict(torch.load(model_path, map_location=torch.device('cpu')))
model.eval()

def preprocess_image(img):
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    cv2.imshow('gray', gray)
    # 自适应二值化，适应不同光照
    binary = cv2.adaptiveThreshold(gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
                                   cv2.THRESH_BINARY_INV, 11, 2)
    
    # 形态学操作，去除小噪声
    kernel = np.ones((3, 3), np.uint8)
    binary = cv2.morphologyEx(binary, cv2.MORPH_CLOSE, kernel)

    return binary

def recognize_number(roi):
    transform = transforms.Compose([
        transforms.Grayscale(),
        transforms.Resize((32, 100)),
        transforms.ToTensor(),
        transforms.Normalize((0.5,), (0.5,))
    ])
    
    roi_pil = Image.fromarray(roi)
    roi_tensor = transform(roi_pil).unsqueeze(0)

    with torch.no_grad():
        preds = model(roi_tensor)
        _, preds = preds.max(2)
        preds = preds.transpose(1, 0).contiguous().view(-1)
        
    return ''.join([chr(pred + 48) for pred in preds])  # 将预测结果转换为数字



def path_tracking(color):
    global __target_color  
    global __isRunning 
    global horizontal_detected
    global reach_the_end
    global cap
    init()
    start()
    cap=cv2.VideoCapture("/dev/video0")


    signal.signal(signal.SIGINT, Stop)
    __target_color = color
    print("start")
    
    ocr = PaddleOCR(use_angle_cls=True, lang="ch")  # 只识别英文和数字
    while __isRunning and (not horizontal_detected) and (not reach_the_end):
    # while __isRunning:
        ret,frame = cap.read()
        if ret:
            processed_frame = preprocess_image(frame)
    
            contours, _ = cv2.findContours(processed_frame, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            
            for cnt in contours:
                x, y, w, h = cv2.boundingRect(cnt)
                if w * h > 50:
                    roi = processed_frame[y:y+h, x:x+w]
                    result = ocr.ocr(roi, cls=True)
        
                    if result and result[0]:
                        text = result[0][0][1][0]  # 取第一个识别结果的文本
                        print(f"识别结果: {text}")

                        cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 2)
                        cv2.putText(frame, text, (x, y - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 0, 0), 2)

            cv2.imshow('Number Detection', frame)
            key = cv2.waitKey(1)
            if key == 27:
                break
        else:
            time.sleep(0.01)
            print("no frame")    
    cv2.destroyAllWindows()
    if cap is not None:
        print('releasing cap at return')
        cap.release()
    return __isRunning, horizontal_detected, reach_the_end

if __name__ == "__main__":
    path_tracking('red')



