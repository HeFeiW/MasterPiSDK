import sys
sys.path.append('/root/thuei-1/sdk-python/')
import HiwonderSDK.Board as Board
import HiwonderSDK.mecanum import *

def MotorStop():
    Board.setMotor(1, 0) 
    Board.setMotor(2, 0)
    Board.setMotor(3, 0)
    Board.setMotor(4, 0)

def spin(radias):
    
    