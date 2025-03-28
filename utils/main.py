from pick_block import pick_block
from pick_block import turn_light_switch
from place_block import place_block
from sorting import sort
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
#     #sort()
    
#     # dance()
    
#     _, horizontal_detected, reach_the_end = path_tracking('red')
#     if reach_the_end:
#         print("reached")
#     elif horizontal_detected:
#         print('horizontal detected')
#     # print ("going front")
#     # chassis.set_velocity(100,90,0)
#     # time.sleep(3)
#     # chassis.set_velocity(0,0,0)
# # #--------------关灯转向----------------------------------
#     print ("going front")
#     chassis.set_velocity(100,90,0)
#     time.sleep(0.8)
#     print ("turning light")
#     turn_light_switch()
#     chassis.set_velocity(0, 0, 100)
#     time.sleep(0.5)
#     chassis.set_velocity(0,0,0)  # 关闭所有电机
    
# #  #--------------导航去卧室----------------------------------
    
    chassis.set_velocity(70,0,0)
    time.sleep(0.8)
    chassis.set_velocity(0,0,0)
#     for i in range(3):
#         _, horizontal_detected, reach_the_end = path_tracking('black')
#         print(f'horizontal_detected:{horizontal_detected}')
#         if horizontal_detected:
#             break
#     time.sleep(1)
#     print('passing the cross')
#     chassis.set_velocity(100,90,-0.5)
#     time.sleep(1)
#     chassis.set_velocity(0,0,0)
# #     chassis.set_velocity(50,90,0)
# #     time.sleep(0.6)
    for i in range(10):
        _, horizontal_detected, reach_the_end = path_tracking('black')
        print(f'horizontal_detected:{horizontal_detected}')
        print(f'reach_the_end:{reach_the_end}')
        if reach_the_end:
            break
    # chassis.set_velocity(100,180,0)
    # time.sleep(1)
#  #--------------卧室等待任务----------------------------------
    print ("going left")
    chassis.set_velocity(100,180,0)
    time.sleep(0.5)
    chassis.set_velocity(0,0,0)
    print ("waiting")
    time.sleep(9)

# # #-------------给奶奶跳舞任务------------------------------
    print ("going right")
    chassis.set_velocity(100,0,0)
    time.sleep(4)
    chassis.set_velocity(0,0,0)
    time.sleep(2.3)
    chassis.set_velocity(100,0,0)
    dance()

# # #-------------垃圾分类任务------------------------------
    for i in range(10):
        _, horizontal_detected, reach_the_end = path_tracking('black')
        print(f'horizontal_detected:{horizontal_detected}')
        print(f'reach_the_end:{reach_the_end}')
        if horizontal_detected:
            break
    chassis.set_velocity(0,0,10)
    time.sleep(1)
    chassis.set_velocity(0,0,0)
    chassis.set_velocity(60,90,0)
    time.sleep(1)
    chassis.set_velocity(0,0,0)
    for i in range(10):
        _, horizontal_detected, reach_the_end = path_tracking('red')
        print(f'horizontal_detected:{horizontal_detected}')
        print(f'reach_the_end:{reach_the_end}')
        if horizontal_detected:
            break
    sort()
    print('sorting')
    

    