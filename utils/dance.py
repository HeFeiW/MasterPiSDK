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
from utils.beep import buzz
import signal
import numpy as np
from utils.base_motion import spin

AK = ArmIK()

def reset():
    pass
#************************************************************
# 全局开始/停止函数
#************************************************************
# app初始化调用
def init():
    print("ColorSorting Init")
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

def dance():
    init()
    start()
    signal.signal(signal.SIGINT, stop)
    AK.setPitchRangeMoving((0,7,2), -90,-135, -45, 1500) 
    buzz(0.2)
    time.sleep(0.5)
    AK.setPitchRangeMoving((0,16,6), 0,-45, 45, 1500)
    buzz(0.2)
    time.sleep(0.5)
    AK.setPitchRangeMoving((0,0,26), 90,45, 135, 1500)
    buzz(0.2)
    time.sleep(0.5)
    Board.setPWMServoPulse(1, 1800, 500)
    buzz(0.2)
    time.sleep(0.5)
    Board.setPWMServoPulse(1, 1500, 500)
    buzz(0.2)
    time.sleep(0.5)
    AK.setPitchRangeMoving((0,1,15), -90,-135, -45, 1500)
    spin(100,2)



     