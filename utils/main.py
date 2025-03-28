#!/usr/bin/python3
# coding=utf8
import sys
sys.path.append('/root/thuei-1/sdk-python/')
import cv2
import time
import math
import signal
import Camera
import threading
import numpy as np
import yaml_handle
from .ArmIK.Transform import *
from .ArmIK.ArmMoveIK import *
from utils.base_motion import *
from utils.buzzer_func import *
from utils.camera import *
import HiwonderSDK.Misc as Misc
import HiwonderSDK.Board as Board
from HiwonderSDK.PID import PID
# constants
IMG_SIZE=(640,480)
ROI = [ # [ROI, weight]
        (240, 280,  0, 640, 0.1), 
        (340, 380,  0, 640, 0.3), 
        (430, 460,  0, 640, 0.6)
       ]

ROI_H1 = ROI[0][0]
ROI_H2 = ROI[1][0] - ROI[0][0]
ROI_H3 = ROI[2][0] - ROI[1][0]
ROI_H_LIST = [ROI_H1, ROI_H2, ROI_H3]
# global variables
# main thread
__isRunning = False # main function is running

__stable = True
__line_centerx = -1

__hold = True
__grasp_pos = (0,0,0)
__place_pos = (0,0,0)

__target_color = 'red'

lab_data = None
# submoudules initialize
AK = ArmIK()


# initialize
def start():
    global __isRunning
    reset()
    __isRunning = True
    print("Nana's good boy Start")
 
    # -------motor thread-----------------
    motor_th = threading.Thread(target=motor_thread)
    motor_th.setDaemon(True)
    motor_th.start()    

    # -------arm thread-----------------
    arm_th = threading.Thread(target=arm_thread)
    arm_th.setDaemon(True)
    arm_th.start() 

def load_config():
    global lab_data
    lab_data = yaml_handle.get_yaml_data(yaml_handle.lab_file_path)

# 初始位置
def initMove():
    Board.setPWMServoPulse(1, 1500, 800)
    AK.setPitchRangeMoving((0, 7, 11), -60, -90, 0, 1500)#TODO set了哪些？
    MotorStop()
    
def init():
    print("Nana's good boy Init")
    load_config()
    print("config loaded")
    initMove()
    print("move initialized")
# app退出玩法调用
def exit():
    global __isRunning
    __isRunning = False
    MotorStop()
    print("Nana's good boy Exit")

def reset():
    # TODO 补全全局变量初始化
    global __isRunning
    global __stable
    global __line_centerx
    global __hold
    global __grasp_pos
    global __place_pos
    global __target_color
    __isRunning = False # main function is running
    __stable = True
    __line_centerx = -1
    __hold = True
    __grasp_pos = (0,0,0)
    __place_pos = (0,0,0)
    __target_color = 'red'

def motor_thread():
    return
def arm_thread():
    return
def read_img(img):
        #write
        global line_centerx
        #read
        global __target_color
        
        img_copy = img.copy()
        img_h, img_w = img.shape[:2]
        
        if not __isRunning or __target_color == ():
            return img
        
        frame_resize = cv2.resize(img_copy, IMG_SIZE, interpolation=cv2.INTER_NEAREST)
        frame_gb = cv2.GaussianBlur(frame_resize, (3, 3), 3)         
        centroid_x_sum = 0
        weight_sum = 0
        center_ = []
        n = 0

        #将图像分割成上中下三个部分，这样处理速度会更快，更精确
        for r in ROI:
            roi_h = ROI_H_LIST[n]
            n += 1       
            blobs = frame_gb[r[0]:r[1], r[2]:r[3]]
            frame_lab = cv2.cvtColor(blobs, cv2.COLOR_BGR2LAB)  # 将图像转换到LAB空间
            area_max = 0
            areaMaxContour = 0
            for i in lab_data:
                if i in __target_color:
                    detect_color = i
                    frame_mask = cv2.inRange(frame_lab,
                                            (lab_data[i]['min'][0],
                                            lab_data[i]['min'][1],
                                            lab_data[i]['min'][2]),
                                            (lab_data[i]['max'][0],
                                            lab_data[i]['max'][1],
                                            lab_data[i]['max'][2]))  #对原图像和掩模进行位运算
                    eroded = cv2.erode(frame_mask, cv2.getStructuringElement(cv2.MORPH_RECT, (3, 3)))  #腐蚀
                    dilated = cv2.dilate(eroded, cv2.getStructuringElement(cv2.MORPH_RECT, (3, 3))) #膨胀

            cnts = cv2.findContours(dilated , cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_TC89_L1)[-2]#找出所有轮廓
            cnt_large, area = getAreaMaxContour(cnts)#找到最大面积的轮廓
            if cnt_large is not None:#如果轮廓不为空
                rect = cv2.minAreaRect(cnt_large)#最小外接矩形
                box = np.int0(cv2.boxPoints(rect))#最小外接矩形的四个顶点
                for i in range(4):
                    box[i, 1] = box[i, 1] + (n - 1)*roi_h + ROI[0][0]
                    box[i, 1] = int(Misc.map(box[i, 1], 0, IMG_SIZE[1], 0, img_h))
                for i in range(4):                
                    box[i, 0] = int(Misc.map(box[i, 0], 0, IMG_SIZE[0], 0, img_w))

                cv2.drawContours(img, [box], -1, (0,0,255,255), 2)#画出四个点组成的矩形
            
                #获取矩形的对角点
                pt1_x, pt1_y = box[0, 0], box[0, 1]
                pt3_x, pt3_y = box[2, 0], box[2, 1]            
                center_x, center_y = (pt1_x + pt3_x) / 2, (pt1_y + pt3_y) / 2#中心点       
                cv2.circle(img, (int(center_x), int(center_y)), 5, (0,0,255), -1)#画出中心点         
                center_.append([center_x, center_y])                        
                #按权重不同对上中下三个中心点进行求和
                centroid_x_sum += center_x * r[4]
                weight_sum += r[4]
        if weight_sum != 0:
            #求最终得到的中心点
            cv2.circle(img, (line_centerx, int(center_y)), 10, (0,255,255), -1)#画出中心点
            line_centerx = int(centroid_x_sum / weight_sum)  
        else:
            line_centerx = -1
        return img

if __name__ == '__main__':
    
    init()
    start()
    signal.signal(signal.SIGINT, exit)
    # ---------定义摄像头-----------------
    cap = cv2.VideoCapture(0)
    # -----------------------------------


    while __isRunning:
        ret,img = cap.read()
        if ret:
            frame = img.copy()
            img_h, img_w = frame.shape[:2]
            # 将图像的下1/4部分设置为黑色
            frame[int(img_h * 3 / 4):, :] = (0, 0, 0)
            Frame = read_img(frame)
            frame_resize = cv2.resize(Frame, (320, 240))
            cv2.imshow('frame', frame_resize)
            key = cv2.waitKey(1)
            if key == 27:
                break
        else:
            time.sleep(0.01)
    cv2.destroyAllWindows()