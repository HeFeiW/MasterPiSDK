import MasterPi
from MasterPi.HiwonderSDK import mecanum
import OPi.GPIO as GPIO
import time
from MasterPi.HiwonderSDK import Board
channel = 12
GPIO.setup(channel, GPIO.IN, pull_up_down=GPIO.PUD_UP)
if GPIO.input(channel):
    print('Input was HIGH')
else:
    print('Input was LOW')
print("successfully imported!")
Board.setBuzzer(0)
print("buzzing")
time.sleep(100)
GPIO.cleanup()
