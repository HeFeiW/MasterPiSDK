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
    load_config()
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
cv2
def move_arm():
    global rect
    global _stop
    global get_roi
    global unreachable
    global __isRunning
    global detect_color
    global start_pick_up
    global rotation_angle
    global world_X, world_Y
    global temp_targ
    global line_centerx
    global lower_frame
    global move_to
    
    while True:
        if __isRunning:        
            # print(f"start_pick_up:{start_pick_up}")
            if detect_color != 'None' and start_pick_up:  #如果检测到方块,开始夹取
                
                # set_rgb(detect_color) # 设置扩展板上的彩灯与检测到的颜色一样
                # setBuzzer(0.1)     # 设置蜂鸣器响0.1秒
                # (0,6,18)
                print(f'targ{temp_targ}')
                Board.setPWMServoPulse(1, 2000, 500) # 张开爪子
                AK.setPitchRangeMoving((temp_targ[0],temp_targ[1],temp_targ[2]+8), -90,-135, -45, 1500) 
                time.sleep(1)
                success = AK.setPitchRangeMoving(temp_targ, -90,-135, -45, 1500) 
                print(f'success:{success}')
                if success is False:
                    print("pick failed")
                    start_pick_up = False
                    move_to = temp_targ
                    time.sleep(1)
                    continue
                time.sleep(1.5)
                Board.setPWMServoPulse(1, 1500, 500) # 闭合爪子
                time.sleep(1.5)
                result = AK.setPitchRangeMoving((temp_targ[0],temp_targ[1],8), -90, -90, 0)
                if not __isRunning:
                    continue
                result = AK.setPitchRangeMoving((0, 8, 10), -90, -90, 0, 1500) #机械臂hold在default位置
                print(f'im back')
                check_picked_up(lower_frame)
                detect_color = 'None'
                get_roi = False
                start_pick_up = False
                # set_rgb(detect_color)
            else:
                time.sleep(0.01)
                # start_pick_up = False                
        else:
            if _stop:
                _stop = False
                initMove()
            time.sleep(0.01)
            # start_pick_up = False
#************************************************************
# CV API
#************************************************************
rect = None
size = (640, 480)
rotation_angle = 0
unreachable = False 
world_X, world_Y = 0, 0
img_centerx = 320

range_rgb = {
    'red':   (0, 0, 255),
    'blue':  (255, 0, 0),
    'green': (0, 255, 0),
    'black': (0, 0, 0),
    'white': (255, 255, 255),
}

roi = [ # [ROI, weight]
        (240, 280,  0, 640, 0.1), 
        (340, 380,  0, 640, 0.3), 
        (430, 460,  0, 640, 0.6)
       ]

roi_h1 = roi[0][0]
roi_h2 = roi[1][0] - roi[0][0]
roi_h3 = roi[2][0] - roi[1][0]

roi_h_list = [roi_h1, roi_h2, roi_h3]

size = (640, 480)
lab_data = None
def load_config():
    global lab_data, servo_data
    
    lab_data = yaml_handle.get_yaml_data(yaml_handle.lab_file_path)


#找出面积最大的轮廓
#参数为要比较的轮廓的列表
def getAreaMaxContour(contours) :
        contour_area_temp = 0
        contour_area_max = 0
        area_max_contour = None

        for c in contours : #历遍所有轮廓
            contour_area_temp = math.fabs(cv2.contourArea(c))  #计算轮廓面积
            if contour_area_temp > contour_area_max:
                contour_area_max = contour_area_temp
                if contour_area_temp > 300:  #只有在面积大于300时，最大面积的轮廓才是有效的，以过滤干扰
                    area_max_contour = c

        return area_max_contour, contour_area_max  #返回最大的轮廓
def run_block(img):
    global roi
    global rect
    global count
    global get_roi
    global center_list
    global unreachable
    global __isRunning
    global start_pick_up
    global rotation_angle
    global last_x, last_y
    global world_X, world_Y
    global start_count_t1, t1
    global detect_color, draw_color, color_list
    
    img_copy = img.copy()
    img_h, img_w = img.shape[:2]   

    if not __isRunning: # 检测是否开启玩法，没有开启则返回原图像
        return img
    
    frame_resize = cv2.resize(img_copy, size, interpolation=cv2.INTER_NEAREST)
    frame_gb = cv2.GaussianBlur(frame_resize, (3, 3), 3)     
    frame_lab = cv2.cvtColor(frame_gb, cv2.COLOR_BGR2LAB)  # 将图像转换到LAB空间
    color_area_max = None
    max_area = 0
    areaMaxContour_max = 0
    
    if not start_pick_up:
        for i in lab_data:
            if i in __target_color:
                frame_mask = cv2.inRange(frame_lab,
                                             (lab_data[i]['min'][0],
                                              lab_data[i]['min'][1],
                                              lab_data[i]['min'][2]),
                                             (lab_data[i]['max'][0],
                                              lab_data[i]['max'][1],
                                              lab_data[i]['max'][2]))  #对原图像和掩模进行位运算
                
                # cv2.imshow("frame_lab",frame_lab)
                # cv2.imshow("frame_gb",frame_mask)
                opened = cv2.morphologyEx(frame_mask, cv2.MORPH_OPEN, np.ones((3, 3),np.uint8))  #开运算
                closed = cv2.morphologyEx(opened, cv2.MORPH_CLOSE, np.ones((3, 3),np.uint8)) #闭运算
                closed[:, 0:100] = 0
                contours = cv2.findContours(closed, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)[-2]  #找出轮廓
                areaMaxContour, area_max = getAreaMaxContour(contours)  #找出最大轮廓
                print("runing")
                if areaMaxContour is not None:
                    if area_max > max_area:#找最大面积
                        max_area = area_max
                        color_area_max = i
                        areaMaxContour_max = areaMaxContour
        if max_area > 2500:  # 有找到最大面积
            rect = cv2.minAreaRect(areaMaxContour_max)
            box = np.int0(cv2.boxPoints(rect))
            cv2.drawContours(img, [box], -1, range_rgb[color_area_max], 2)
            
            if not start_pick_up:
                if color_area_max == 'red':  #红色最大
                    color = 1
                elif color_area_max == 'green':  #绿色最大
                    color = 2
                elif color_area_max == 'blue':  #蓝色最大
                    color = 3
                else:
                    color = 0
                color_list.append(color)
                # print(f"color_list:{color_list}")
                if len(color_list) == 3:  #多次判断
                    # 取平均值
                    color = int(round(np.mean(np.array(color_list))))
                    color_list = []
                    if color:
                        start_pick_up = True
                        if color == 1:
                            detect_color = 'red'
                            draw_color = range_rgb["red"]
                        elif color == 2:
                            detect_color = 'green'
                            draw_color = range_rgb["green"]
                        elif color == 3:
                            detect_color = 'blue'
                            draw_color = range_rgb["blue"]
                    else:
                        start_pick_up = False
                        detect_color = 'None'
                        draw_color = range_rgb["black"]
        else:
            if not start_pick_up:
                draw_color = (0, 0, 0)
                detect_color = "None"

    cv2.putText(img, "Color: " + detect_color, (10, img.shape[0] - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.65, draw_color, 2)
    return img
def check_picked_up(lower_frame):
    global __target_color
    global start_pick_up
    global picked_up
    frame_resize = cv2.resize(lower_frame, size, interpolation=cv2.INTER_NEAREST)
    frame_gb = cv2.GaussianBlur(frame_resize, (3, 3), 3)     
    frame_lab = cv2.cvtColor(frame_gb, cv2.COLOR_BGR2LAB)  # 将图像转换到LAB空间
    color_area_max = None
    max_area = 0
    areaMaxContour_max = 0
    
    # 计算frame_lab的总面积
    frame_lab_height, frame_lab_width = frame_lab.shape[:2]
    total_area = frame_lab_height * frame_lab_width
    
    for i in range(3):
        for i in lab_data:
            if i in __target_color:
                frame_mask = cv2.inRange(frame_lab,
                                            (lab_data[i]['min'][0],
                                            lab_data[i]['min'][1],
                                            lab_data[i]['min'][2]),
                                            (lab_data[i]['max'][0],
                                            lab_data[i]['max'][1],
                                            lab_data[i]['max'][2]))  #对原图像和掩模进行位运算
                max_area = cv2.countNonZero(frame_mask)        
                print(f'maxarea{max_area/total_area}')
                if max_area/total_area > 0.4:  # 有找到最大面积
                    picked_up = True
                    return
                else:
                    picked_up = False
    return
#运行子线程 
th = threading.Thread(target=move_arm)
th.setDaemon(True)
th.start()    
 
t1 = 0
roi = ()
center_list = []
last_x, last_y = 0, 0
draw_color = range_rgb["black"]
length = 50
w_start = 200
h_start = 200


def pick_block(color):
    init()
    start()
    global __target_color
    global temp_targ
    global lower_frame
    global picked_up
    __target_color = color
    cap = cv2.VideoCapture(0)
    while True:
        if picked_up:
            return (True,())
        ret,img = cap.read()
        if ret:
            frame = img.copy()
            img_h, img_w = frame.shape[:2]
            # 将图像的下1/4部分设置为黑色
            lower_frame = np.copy(frame[int(img_h * 3 / 4):, 230:450])
            frame[int(img_h * 3 / 4):, 0:230] = np.random.randint(0, 256, (int(img_h / 4), 230, 3), dtype=np.uint8)
            frame[int(img_h * 3 / 4):, 450:] = np.random.randint(0, 256, (int(img_h / 4), img_w-450, 3), dtype=np.uint8)
            Frame = run_block(frame)
            # print(f"frame.shape():{frame.shape}")
            frame_resize = cv2.resize(Frame, (640, 480))
            roi = getROI(cv2.boxPoints(rect))
            roi_rounded = tuple(int(round(value)) for value in roi)
            frame_roi = getMaskROI(frame_resize,roi_rounded,(640,480))
            
            cv2.imshow('frame', frame)#temp
            
            cv2.imshow('lower', lower_frame)#temp
            print(f'pickedup:{picked_up}')
            # 在frame上画出rect
            if rect is not None:
                x_i,y_i = getCenter(rect, roi_rounded, (640,480), 3)
                x,y = convertCoordinate(x_i,y_i,(640,480))
                temp_targ= (x,y-0.7*x,-1.5)
                # 夹的距离有点靠前，向后挪1cm
                # temp_targ[1]-=1
                cv2.imwrite('/root/thuei-1/utils/img.jpg',frame)
                box = cv2.boxPoints(rect)
                box = np.int0(box)
                cv2.drawContours(frame, [box], 0, (0, 255, 0), 2)
            key = cv2.waitKey(1)
            if key == 27:
                break
        else:
            time.sleep(0.01)
    cv2.destroyAllWindows()