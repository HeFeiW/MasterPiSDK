from pick_block import pick_block
from pick_block import turn_light_switch
from place_block import place_block
#from dance import dance
# from path_tracking import path_tracking
from VisualPatrol_init import path_tracking
from base_motion import *
from beep import buzz
import OPi.GPIO as GPIO
import cv2
from dance import dance
if __name__ == '__main__':
    GPIO.setup(31, GPIO.OUT)
    buzz(0.2)
    # ---------test cam --------------------------------
    # print("正在尝试打开摄像头...")
    # cap = cv2.VideoCapture(0)
    
    # # 打印摄像头属性
    # print(f"Backend: {cap.getBackendName()}")
    # print(f"摄像头是否打开: {cap.isOpened()}")
    
    # if not cap.isOpened():
    #     print("摄像头打开失败，正在检查设备...")
    #     import subprocess
    #     result = subprocess.run(['v4l2-ctl', '--list-devices'], capture_output=True, text=True)
    #     print("可用设备：")
    #     print(result.stdout)
    #     exit()
        
    # # 设置摄像头参数
    # cap.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter_fourcc('M','J','P','G'))
    # cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
    # cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
    # picked_up =  pick_block('red')
    # print(f'main:{picked_up}')
    # placed_block = place_block((0,10,0))
    # print(f'main:{placed_block}')
    # ----------- test cam end -----------------------------------
    # dance()
    
    _, horizontal_detected, reach_the_end = path_tracking('red')
    print(f'horizontal_detected:{horizontal_detected}')
    print(f"reach_the_end:{reach_the_end}")
    if reach_the_end:
        spin(100,1)
    else:
        if horizontal_detected:
            backwards(50,0.1)
    turn_light_switch()
#    _, horizontal_detected, reach_the_end = path_tracking('red')
#    print(f'horizontal_detected:{horizontal_detected}')
#    print(f"reach_the_end:{reach_the_end}")
#    if horizontal_detected:
#        spinn(100,1)
#    else:
#        if horizontal_detected:
#            backwards(50,0.1)