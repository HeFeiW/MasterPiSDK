from pick_block import pick_block
from place_block import place_block
from path_tracking import path_tracking
from base_motion import *
if __name__ == '__main__':
    
    # picked_up =  pick_block('red')
    # print(f'main:{picked_up}')
    # placed_block = place_block((0,10,0))
    # print(f'main:{placed_block}')
    _, horizontal_detected, reach_the_end = path_tracking('black')
    if horizontal_detected:
        spinn(100,1)
    else:
        if horizontal_detected:
            backwards(50,0.1)
    _, horizontal_detected, reach_the_end = path_tracking('blue')
    if horizontal_detected:
        spinn(100,1)
    else:
        if horizontal_detected:
            backwards(50,0.1)