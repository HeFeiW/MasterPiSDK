#!/usr/bin/env python3
# encoding:utf-8
import cv2
import sys
sys.path.append('/root/thuei-1/sdk-python/')
import math
import numpy as np
from CameraCalibration.CalibrationConfig import *

def detect_red_square(image, square_length=3.0):
    """
    检测图像中的红色方块并计算其在机械臂坐标系中的位置
    
    参数:
        image: 输入图像
        square_length: 方块实际边长(cm)
        
    返回:
        (x, y): 方块中心在机械臂坐标系中的位置
        angle: 旋转角度
    """
    # 获取图像尺寸
    size = (image.shape[1], image.shape[0])
    
    # 转换到HSV颜色空间进行红色检测
    hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)
    
    # 定义红色范围（可能需要根据实际环境调整）
    lower_red1 = np.array([0, 100, 100])
    upper_red1 = np.array([10, 255, 255])
    lower_red2 = np.array([160, 100, 100])
    upper_red2 = np.array([180, 255, 255])
    
    # 创建掩膜
    mask1 = cv2.inRange(hsv, lower_red1, upper_red1)
    mask2 = cv2.inRange(hsv, lower_red2, upper_red2)
    mask = cv2.bitwise_or(mask1, mask2)
    
    # 进行形态学操作，去除噪点
    kernel = np.ones((5, 5), np.uint8)
    mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel)
    mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel)
    
    # 查找轮廓
    contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    
    if not contours:
        return None, None, None
    
    # 找到最大轮廓（假设是方块）
    cnt = max(contours, key=cv2.contourArea)
    
    # 计算最小外接矩形
    rect = cv2.minAreaRect(cnt)
    box = cv2.boxPoints(rect)
    box = np.int0(box)
    
    # 获取ROI区域
    roi = getROI(box)
    
    # 获取方块中心坐标
    pixel_x, pixel_y = getCenter(rect, roi, size, square_length)
    
    # 转换为机械臂坐标系
    arm_x, arm_y = convertCoordinate(pixel_x, pixel_y, size)
    
    # 计算旋转角度
    servo_angle = getAngle(arm_x, arm_y, rect[2])
    
    # 可以在图像上绘制结果进行可视化
    result_img = image.copy()
    cv2.drawContours(result_img, [box], 0, (0, 255, 0), 2)
    cv2.circle(result_img, (int(pixel_x), int(pixel_y)), 5, (0, 0, 255), -1)
    
    return (arm_x, arm_y), servo_angle, result_img

# 示例使用
if __name__ == "__main__":
    # 读取图像
    image = cv2.imread('red_square.jpg')
    
    if image is None:
        print("无法读取图像")
        sys.exit(1)
    
    # 检测红色方块
    position, angle, result_img = detect_red_square(image, square_length=3.0)
    
    if position is not None:
        print(f"方块在机械臂坐标系中的位置: X={position[0]}cm, Y={position[1]}cm")
        print(f"旋转角度: {angle}")
        
        # 显示结果
        cv2.imshow("检测结果", result_img)
        cv2.waitKey(0)
        cv2.destroyAllWindows()
    else:
        print("未能检测到红色方块")
