


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
    while __isRunning and (not horizontal_detected) and (not reach_the_end):
    # while __isRunning:
        ret,img = cap.read()
        if ret:
            frame = img.copy()
            # frame[430:, :] = np.random.randint(0, 256, (50, 640, 3), dtype=np.uint8)
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

            data = pytesseract.image_to_data(gray, output_type=pytesseract.Output.DICT)
            for i in range(len(data['text'])):
                if data['text'][i].isdigit():
                    x, y, w, h = data['left'][i], data['top'][i], data['width'][i], data['height'][i]
                    cv2.rectangle(frame, (x, y), (x+w, y+h), (0, 255, 0), 2) data['text'][i]
                    print(f"数字 {data['text'][i]} 坐标: ({x}, {y}, {x+w}, {y+h})")

            cv2.imshow('frame', frame)
            key = cv2.waitKey(1)
            if key == 27:
                break
        else:
            time.sleep(0.01)
    cv2.destroyAllWindows()
    if cap is not None:
        print('releasing cap at return')
        cap.release()
    return __isRunning, horizontal_detected, reach_the_end

import cv2
import pytesseract

# 读取图像
image = cv2.imread('test.jpg')


# 使用Tesseract检测数字


# 遍历检测结果


cv2.imshow('Result', image)
cv2.waitKey(0)