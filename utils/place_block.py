#!/usr/bin/python3
# coding=utf8
import sys
sys.path.append('/root/thuei-1/sdk-python/')
import cv2
import time
import Camera
import threading
import yaml_handle
from ArmIK.Transform import *
from ArmIK.ArmMoveIK import *
import HiwonderSDK.Sonar as Sonar
import HiwonderSDK.Board as Board
from CameraCalibration.CalibrationConfig import *
from HiwonderSDK.PID import PID
import numpy as np
if sys.version_info.major == 2:
    print('Please run this program with python3!')
    sys.exit(0)

AK = ArmIK()
HWSONAR = Sonar.Sonar() #超声波传感器
pitch_pid = PID(P=0.28, I=0.16, D=0.18) #Pid要调参啊

count = 0
_stop = False
color_list = []
get_roi = False
__isRunning = False
detect_color = 'None'
start_pick_up = False
start_count_t1 = True
temp_targ = (0,0,0)
line_centerx = -1 # whf added according to visual patrol
picked_up = False
move_to = (0,0)
# 变量重置
def reset():
    global _stop
    global count
    global get_roi
    global color_list
    global detect_color
    global start_pick_up
    global __target_color
    global start_count_t1
    global line_centerx
    global picked_up
    global lower_frame
    global move_to
    line_centerx = -1
    count = 0
    _stop = False
    color_list = []
    get_roi = False
    __target_color = ()
    detect_color = 'None'
    start_pick_up = False
    start_count_t1 = True
    picked_up = False
    lower_frame = []
    move_to = (0,0)
#************************************************************
# 全局开始/停止函数
#************************************************************
# app初始化调用
def init():
    print("ColorSorting Init")
    # 超声波开启后默认关闭灯
    # HWSONAR.setRGBMode(0)
    # HWSONAR.setPixelColor(0, Board.PixelColor(0,0,0))
    # HWSONAR.setPixelColor(1, Board.PixelColor(0,0,0))    
    # HWSONAR.show()
    # load_config()
    initMove()

# app开始玩法调用
def start():
    global __isRunning
    reset()
    __isRunning = True
    print("ColorSorting Start")

# app停止玩法调用
def stop():
    global _stop #_stop 是干什么用的？
    global __isRunning
    _stop = True
    __isRunning = False
    # set_rgb('None')
    MotorStop() # whf added according to visual patrol
    print("ColorSorting Stop")

# app退出玩法调用
def exit():
    global _stop
    global __isRunning
    _stop = True
    # set_rgb('None')
    __isRunning = False
    MotorStop() # whf added according to visual patrol
    print("ColorSorting Exit")
#************************************************************
# 运动控制API
#************************************************************

# 夹持器夹取时闭合的角度
servo1 = 1500

# 初始位置
def initMove():
    Board.setPWMServoPulse(1, servo1, 800)
    AK.setPitchRangeMoving((0, 8, 10), -90, -90, 0, 1500)
    MotorStop() # whf added according to visual patrol

def MotorStop():
    Board.setMotor(1, 0) 
    Board.setMotor(2, 0)
    Board.setMotor(3, 0)
    Board.setMotor(4, 0)

def place_block(place_targ):
    init()
    start()
    for i in range(3):
        result = AK.setPitchRangeMoving((place_targ[0],place_targ[1],place_targ[2]+8), -90, -90, 0) # 运行到对应颜色的坐标上方
        if result == False:
            print(f'pick_block failed{i}')
        else:
            unreachable = False
            time.sleep(result[2]/1000) #如果可以到达指定位置，则获取运行时间
        AK.setPitchRangeMoving(place_targ, -90,-90, 0, 500)  # 放置到检测到颜色对应的坐标
        time.sleep(0.5)
        if not __isRunning:
            continue
        Board.setPWMServoPulse(1, 1800, 500) # 张开爪子
        time.sleep(0.5)
        if not __isRunning:
            continue
        if not __isRunning:
            continue
        Board.setPWMServosPulse([1200, 4, 1,1500, 3,515, 4,2170,5,945]) # 机械臂进行复位
        time.sleep(2)
        return True
    return False
