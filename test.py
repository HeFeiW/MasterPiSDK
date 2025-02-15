import MasterPi
from MasterPi.HiwonderSDK import mecanum
import OPi.GPIO as GPIO
import time
from MasterPi.HiwonderSDK import Board
GPIO.setwarnings(False)
channel = 12
GPIO.setup(channel, GPIO.IN, pull_up_down=GPIO.PUD_UP)
if GPIO.input(channel):
    print('Input was HIGH')
else:
    print('Input was LOW')
print("successfully imported!")
print("buzzing")
GPIO.setup(31,GPIO.OUT,0)
GPIO.output(31,0)
time.sleep(1)
# Board.setBuzzer(0)
# GPIO.cleanup()
# except Exception as e:
#     print(e)
# finally:
#     GPIO.cleanup()
#     print("cleaned UP")
