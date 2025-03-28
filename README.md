# thuei-1
Platform for the 1st Tsinghua University Embodied Intelligence Challenge

## Installation
```sh
git clone https://github.com/thuasta/thuei-1.git /root/thuei-1
```

### 运行逻辑

主函数循环调用read_img(frame)理解当前环境,通过全局变量修改当前的state，act，env：

other global variables:

1. lab_data

read_img:

1. state：
   1. __on_task(enum)
   2. __finished_task(list(enum))
   3. __target_color
2. act:
   1. whole_body:
      1. __stable=True/False:True为静止态，motor deactivated, arm_activated;
   2. arm_group:
      1. __grasp_pos(trans,quat)
      2. __hold=True/Flase；当__hold==True or __stable=False, arm 不可修改角度；
      3. __place_pos(trans,quat)
   3. 
3. env:
   1. __line_centerx
   2. __in_room(enum)

threading：

1. motor_move:
   1. 读取全局变量：
      1. __stable
      2. __line_centerx
      3. 
2. arm_move:
   1. __stable
   2. __hold
   3. __grasp_pos
   4. __place_pos
   