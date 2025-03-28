import sys
sys.path.append('/root/thuei-1/sdk-python/')
import HiwonderSDK.Board as Board
import HiwonderSDK.mecanum as mecanum
import signal
import time
chassis = mecanum.MecanumChassis(wheel_init_dir=[1, 1, 1, 1], wheel_init_map=[1, 3, 4, 2])

start = True
#关闭前处理
def Stop(signum, frame):
    global start
    start = False
    print('关闭中...')
    chassis.set_velocity(0,0,0)  # 关闭所有电机
    

signal.signal(signal.SIGINT, Stop)

   

def MotorStop():
    Board.setMotor(1, 0) 
    Board.setMotor(2, 0)
    Board.setMotor(3, 0)
    Board.setMotor(4, 0)

def spin(angular_velocity,sec):
    chassis.set_velocity(0,0,angular_velocity)
    time.sleep(sec)
    chassis.set_velocity(0,0,0)  # 关闭所有电机
    print('已关闭')
    return True
def backwards(velocity,sec):
    chassis.set_velocity(-velocity,90,0)
    time.sleep(sec)    
    chassis.set_velocity(0,0,0)  # 关闭所有电机
    print('已关闭')
def move(velocity,dir,sec):
    chassis.set_velocity(-velocity,dir,0)
    time.sleep(sec)
    chassis.set_velocity(0,0,0)
    print(f'moved----velocity:{velocity} dir:{dir} time:{sec}s')