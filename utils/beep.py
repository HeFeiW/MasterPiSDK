import time
import sys
sys.path.append('/root/thuei-1/sdk-python/')
import HiwonderSDK.Board as Board
def buzz(sec):
    Board.setBuzzer(0)
    Board.setBuzzer(1)
    time.sleep(sec) # 延时
    Board.setBuzzer(0) #关闭
