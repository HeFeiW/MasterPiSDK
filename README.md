# 开发记录

## 初始配置

### 连接校园网

1. 通过数据线进行串口连接

   - 用microUSB数据线连接板子和电脑，板子上电，电脑识别出新设备后，打开串口工具，设置波特率为115200，打开串口，即可看到板子的启动信息。
  
2. nmcli添加添加 802.1x 认证 wifi

   ```bash
   # 在板子终端输入
   sudo nmcli d wifi # 查看wifi列表
   sudo nmcli con add type wifi ifname wlan0 con-name Tsinghua-Secure ssid Tsinghua-Secure
   sudo nmcli con edit Tsinghua-Secure
    nmcli> set 802-1x.eap peap
    nmcli> set 802-1x.phase2-auth mschapv2
    nmcli> set 802-1x.identity <your_id> # 校园网账号
    nmcli> set 802-1x.password <your_password> # 校园网密码
    nmcli> set wifi-sec.key-mgmt wpa-eap
    nmcli> set connection.autoconnect true
    nmcli> save
    nmcli> activate
    nmcli> quit
    ```

3. 此时应该可以连接校园网了，在命令行输入

    ```bash
    ifconfig
    ```

    查看ip地址，找到wlan0网卡inet地址xxx.xxx.xxx.xxx

4. 通过ssh连接板子

    ```bash
    # 在本地终端cmd输入
    ssh HwHiAiUser@xxx.xxx.xxx.xxx # 这里的xxx.xxx.xxx.xxx是上一步查到的ip地址
    ```

    根据提示输入密码即可连接

5. 如果设置了自动连接，下次开机后会自动连接校园网，可以在`校园网自助服务平台-首页-在线信息`处查看设备的ip地址

### 安装依赖

#### ~~安装wiringpi~~

1. 准备工作
    
    确保系统中有配置文件`/etc/orangepi-release `：
    ```bash
    cat /etc/orangepi-release
    ```
    如果没有返回`BOARD=orangepiaipro`，则需要手动创建配置文件：
    ```bash
    echo "BOARD=orangepiaipro" | sudo tee /etc/orangepi-release
    ```

2. 下载 WiringOP 源码

    从官方仓库克隆 WiringOP 源码，切换到 next 分支，并安装编译工具：

    ```bash
    # 依次执行以下命令
    sudo apt-get update
    sudo apt-get install -y git
    git clone https://github.com/orangepi-xunlong/wiringOP.git -b next
    sudo apt-get install -y gcc make build-essential
    cd wiringOP
    sudo ./build clean
    sudo ./build
    ```

3. 测试安装
   
   ```bash
   gpio readall
   ```

    如果能够正常显示 GPIO 引脚映射表，说明安装成功。

4. Python 绑定

    这里我们使用[wiringOP-Python](https://github.com/orangepi-xunlong/wiringOP-Python)来绑定 Python。

    ```bash
    sudo apt-get install swig python3-dev python3-setuptools # 安装依赖
    git clone --recursive https://github.com/orangepi-xunlong/wiringOP-Python.git -b next # 克隆仓库，注意：1.这里使用的是 next 分支，否则无法在orangepiaipro上编译 2.要加上 --recursive 参数，否则会缺少子模块
    cd wiringOP-Python # 进入目录
    python3 generate-bindings.py > bindings.i
    sudo python3 setup.py install
    ```

    上述命令运行完毕后，注意查看输出信息，最后三行应该是类似下面的输出：

    ```bash
    Installed /usr/local/lib/python3.10/dist-packages/wiringpi-2.60.1-py3.10-linux-aarch64.egg # wiringpi的安装路径
    Processing dependencies for wiringpi==2.60.1
    Finished processing dependencies for wiringpi==2.60.1
    ```

    这个路径有可能并不在python的搜索路径中，可以通过以下命令查看 Python 的搜索路径：

    ```bash
    python3 -c "import sys; print(sys.path)"
    ```

    如果没有这个路径，可以通过以下命令添加：

    ```bash
    export PYTHONPATH=$PYTHONPATH:/usr/local/lib/python3.10/dist-packages #注意这里的路径要替换成你在上面编译输出中看到的wireingpi的安装路径
    # 也可以把这个命令加入到~/.bashrc文件的最后一行，这样每次打开终端都会自动执行，注意添加后要source ~/.bashrc使其生效
    ```

    可以使用以下命令测试 Python 绑定是否安装成功：

    ```bash
    python3 -c "import wiringpi as wp; wp.wiringPiSetup(); print(wp.digitalRead(0))"
    ```

    如果出现如下错误：

    ```bash
    Traceback (most recent call last):
    File "<stdin>", line 1, in <module>
    File "/home/HwHiAiUser/wiringOP-Python/wiringpi.py", line 15, in <module>
        import _wiringpi
    ModuleNotFoundError: No module named '_wiringpi'
    ```

    可能是权限问题，尝试用sudo运行python。（即运行`sudo python3 -c "import wiringpi as wp; wp.wiringPiSetup(); print(wp.digitalRead(0))"`）

    如果能够正常执行，说明 Python 绑定已安装成功。
    > 另一种方法是进行用户级别的安装，但依然需要提升当前用户的权限使之能够访问GPIO，具体方法如下：
    >
    > ```bash
    > cd /home/HwHiAiUser/wiringOP-Python
    > sudo chown -R $USER:$USER .
    > sudo chmod -R u+w .
    > pip install --user .
    > ```
    > 这样可以将wiringpi安装到用户目录下，不需要提升权限即可访问到wiringpi包。但是，在使用wiringpi时，常常需要访问GPIO，这时依然需要提升权限，可以通过新建一个组，将当前用户加入到这个组，然后将这个组的权限赋予GPIO设备，这样就可以在不提升权限的情况下访问GPIO了。具体方法如下：
    >
    > ```bash
    > sudo groupadd gpio # 新建一个gpio组
    > sudo usermod -aG gpio $USER # 将当前用户加入到gpio组
    > sudo chown root:gpio /dev/mem  # 将gpiomem和mem的所有者改为root，组改为gpio
    > sudo chmod g+rw  /dev/mem # 给gpio组赋予读写权限
    > sudo chown root:gpio /dev/mem /dev/gpiochip*
    > sudo chmod g+rw /dev/mem /dev/gpiochip*
    > sudo chown root:gpio /sys/class/gpio/export
    > sudo chmod g+rw /sys/class/gpio/export
    > sudo chown -R :gpio /sys/class/gpio
    > sudo chmod -R g+rw /sys/class/gpio
    > sudo chown -R :gpio /sys/devices/platform/820f0000.gpio/gpiochip4/gpio
    > sudo chmod -R g+rw /sys/devices/platform/820f0000.gpio/gpiochip4/gpio
    > ```


5. 补充内容：使用 WiringOP 控制 GPIO

    以下是一个简单的 Python 示例，使用 WiringOP 控制 GPIO：

    ```python
    import wiringpi as wp

    # 初始化 WiringOP
    wp.wiringPiSetup()

    # 设置 GPIO0 为输出模式
    wp.pinMode(0, wp.OUTPUT)

    # 设置 GPIO0 为高电平
    wp.digitalWrite(0, wp.HIGH)

    # 读取 GPIO1 的状态
    wp.pinMode(1, wp.INPUT)
    value = wp.digitalRead(1)
    print("GPIO1 value:", value)
    ```

#### ~~安装OPI.GPIO~~

> OPI.GPIO是一个兼容RPi.GPIO的库，可以在香橙派上使用RPi.GPIO的代码。一开始尝试使用wiringOP的Python绑定，但是在使用RPi.GPIO的代码时发现有些函数没有实现，所以改用OPI.GPIO。后者的函数实现更加完整，并且基于RPi.GPIO实现，所以可以直接使用RPi.GPIO的代码。但是对OrangePiAiPro的支持并不完善，所以需要进行一些额外的设置。

1. 通过pip安装
   
   ```bash
   # 切换到root用户执行以下命令
    pip install --upgrade OPi.GPIO
    ```
    
2. 测试安装

    ```bash
    pip show OPi.GPIO
    ```

    如果看到安装的信息，说明安装成功。

3. 使用示例

    ```python
    import OPi.GPIO as GPIO # 在 MasterPi/HiwonderSDK/Board.py 中把RPi.GPIO改为OPi.GPIO
    # 注意是OPi不是OPI，，，
    ```

4. ~~兼容orangePiAiPro~~

    1. 在`MasterPi/MasterPi/HiwonderSDK/Board.py`中引入了orangepiaipro的引脚映射表。（这一步已经实现，不需要自己操作）

5. 设置文件权限

    进行GPIO操作需要用户对GPIO相关配置文件进行读写，这些文件很多是由内核动态创建的，并且默认权限组是root:root。为了避免直接使用root运行脚本，要增加一个gpio权限组，将当前用户加入权限组，并赋予组相应权限。所需操作如下：

    1. 在终端依次执行：
    
    ```bash
    sudo groupadd gpio # 新建一个gpio用户组
    sudo usermod -aG gpio $USER # 将当前用户加入到gpio组
    sudo chown root:gpio /dev/mem /dev/gpiochip* #修改静态文件的权限
    sudo chmod g+rw /dev/mem /dev/gpiochip*
    sudo chown root:gpio /sys/class/gpio/export
    sudo chmod g+rw /sys/class/gpio/export
    sudo apt install nano 
    sudo nano /etc/udev/rules.d/99-gpio.rules # 新建规则，使得内核动态创建GPIO文件时实时设置权限
    SUBSYSTEM=="gpio*", PROGRAM="/bin/sh -c 'find -L /sys/class/gpio/ -maxdepth 2 -exec chown root:gpio {} \; -exec chmod 770 {} \; || true'" # 在/etc/udev/rules.d/99-gpio.rules写入这一
    保存并退出
    sudo udevadm control --reload-rules # 应用规则
    sudo udevadm trigger --subsystem-match=gpio
    ```
#### 从源码安装GPIO
1. clone源码
```bash
git clone git@github.com:rm-hull/OPi.GPIO.git
```
2. 修改部分函数，避免抛出异常
```python
# ~/OPi.GPIO/OPi/GPIO.py line 468,line 469
# 注释掉下面这两行，避免在连续修改同一个端口时抛出异常
        if channel in _exports:
            raise RuntimeError("Channel {0} is already configured".format(channel))
```
3. 编译


#### MasterPi源码

1. 从GiHub仓库clone MasterPi SDK源码
    ```bash
    git clone https://github.com/HeFeiW/MasterPiSDK.git
    ```

    > 补充：远程文件传到本地：
    >
    > ```bash
    > scp filename username@ip_address:/home/username # 这里的filename是源码文件地址，username是香橙派用户名，ip_address是香橙派ip地址
    > scp username@ip_address:/home/username/filename /local_dir # 这里的filename是源码文件地址，username是香橙派用户名，ip_address是香橙派ip地址，local_dir是本地目标文件夹
    > # 如果是文件夹，加上-r参数
    > scp -r username@ip_address:/home/username/foldername /local_dir # 服务器文件夹传到本地
    > scp -r /local_dir/foldername username@ip_address:/home/username # 本地文件夹传到服务器
    > unzip filename -d <target_dir> # 这里的filename是源码文件地址，target_dir是解压目标文件夹
    > ```

2. 编译自定义包

    ```bash
    cd MasterPi
    python setup.py install --user # 这里--user参数用于将包安装到用户级目录下，从而无需root权限。
    ```

    检验是否安装成功

    ```bash
    pip show MasterPi
    ```

    如果看到安装的信息，说明安装成功。

    > 补充：由于MasterPi提供的源码是基于树莓派的，使用的GPIO库是RPi.GPIO，而香橙派使用的是wiringpi，所以这里编译的代码是经过修改的，具体修改内容见`MasterPi/README.md`。
    > 所需的库如果没有安装，在运行setup.py时会提示安装。

5. 运行

    ```bash
    python MasterPi/main.py
    ```
### 配置权限

1. gpio权限

2. tty权限
```bash
sudo usermod -aG tty $USER
newgrp tty
```
为了不改变原有的tty用户组的权限，这里要用到acl来进行更细致的权限管理。首先检查文件系统是否支持acl
```bash
(base) HwHiAiUser@orangepiaipro:/$ lsblk # 查看系统中可用的磁盘和分区
NAME        MAJ:MIN RM   SIZE RO TYPE MOUNTPOINTS
mmcblk1     179:0    0 119.1G  0 disk 
├─mmcblk1p1 179:1    0     1M  0 part 
├─mmcblk1p2 179:2    0 118.8G  0 part / # 显然，这是我们使用的文件系统（也可能会是别的名字）
└─mmcblk1p3 179:3    0    50M  0 part /exchange
```
使用 blkid 命令查看设备的文件系统类型：
```
sudo tune2fs -l /dev/<disk_name> | grep "Default mount options" # 这里的<disk_name>是上面目标文件系统的名字，例如，在上面的示例中是mmcblk1p2
```
如果输出中包含`acl`，则表示文件系统支持 ACL，可以继续进行下面的步骤。
```bash
sudo groupadd tty_r
sudo usermod -aG tty_r $USER
sudo setfacl -m g:tty_r:rw- /dev/tty*
```
```bash
```
```bash
```

3. i2c权限
```bash
sudo usermod -aG i2c $USER
newgrp i2c
```
sudo i2cdetect -y 0

目前遇到的问题：
    1. 客服提供的RasAdapter 原理图是v5.3的，端口和手里的v3.6不完全一样，有一些控制模块不能确定其映射关系。已经在技术交流群&[某个线上电商](https://robu.in/product/hiwonder-rasadapter_v3-6-expansion-board/)尝试索要对应版本的datasheet。
    2. i2c设备查找不到，怀疑是由于没有配置gpio为i2c接口。需要修改设备树，详情：
    在 Orange Pi 上，使用 `smbus` 控制 GPIO 接口复用为 I2C 的过程分为两部分：

1. **硬件层面**：通过设备树（Device Tree）或内核配置将 GPIO 引脚复用为 I2C 功能。
2. **软件层面**：使用 Python 的 `smbus` 库与 I2C 设备通信。

以下详细说明如何实现这两部分。

---

### 1. **硬件层面：配置 GPIO 为 I2C 功能**

#### 1.1 确认 GPIO 引脚
   - 查看 Orange Pi 的原理图或手册，确认哪些 GPIO 引脚可以复用为 I2C 功能。
   - 例如，Orange Pi Zero 的 `PA11` 和 `PA12` 可以复用为 I2C0 的 `SCL` 和 `SDA`。

#### 1.2 修改设备树
   - 设备树用于配置硬件资源，包括 GPIO 复用功能。
   - 找到设备树文件（通常位于 `/boot/dtb/` 或 `/boot/` 目录下），例如 `sun8i-h3-orangepi-zero.dtb`。
   - 修改设备树文件，将 GPIO 配置为 I2C 功能。

##### 示例：配置 GPIO 为 I2C
   假设需要将 `PA11` 和 `PA12` 配置为 I2C0 的 `SCL` 和 `SDA`：
   ```dts
   &i2c0 {
       pinctrl-names = "default";
       pinctrl-0 = <&i2c0_pins>;
       status = "okay";
   };

   &pio {
       i2c0_pins: i2c0_pins {
           pins = "PA11", "PA12";
           function = "i2c0";
       };
   };
   ```

#### 1.3 编译并加载设备树
   - 如果修改了设备树源文件（`.dts`），需要将其编译为二进制文件（`.dtb`）。
   - 使用 `dtc` 工具编译：
     ```bash
     dtc -I dts -O dtb -o sun8i-h3-orangepi-zero.dtb sun8i-h3-orangepi-zero.dts
     ```
   - 将编译好的设备树文件复制到 `/boot/` 目录，并更新引导配置。
   - 重启系统以应用更改：
     ```bash
     sudo reboot
     ```

#### 1.4 验证 I2C 配置
   - 使用 `i2cdetect` 工具检查 I2C 总线是否正常工作：
     ```bash
     sudo apt install i2c-tools
     sudo i2cdetect -l
     sudo i2cdetect -y 0
     ```
   - 如果看到 I2C 设备地址，说明配置成功。

---

### 2. **软件层面：使用 `smbus` 控制 I2C**

#### 2.1 安装 `smbus` 库
   - 在 Python 中，`smbus` 是一个用于与 I2C 设备通信的库。
   - 安装 `smbus`：
     ```bash
     sudo apt update
     sudo apt install python3-smbus
     ```

#### 2.2 编写 Python 脚本
   - 使用 `smbus` 库与 I2C 设备通信。

##### 示例：读取 I2C 设备数据
   ```python
   import smbus

   # 初始化 I2C 总线
   bus = smbus.SMBus(0)  # 0 表示 I2C0 总线

   # I2C 设备地址
   device_address = 0x50  # 替换为实际的设备地址

   # 读取一个字节
   def read_byte(register):
       return bus.read_byte_data(device_address, register)

   # 写入一个字节
   def write_byte(register, value):
       bus.write_byte_data(device_address, register, value)

   # 示例：读取寄存器 0x00 的值
   v