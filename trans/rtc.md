1. 找不到rtc设备
```bash
$ls /dev/rtc*
ls: cannot access '/dev/rtc*': No such file or directory
```
```bash
$ ls /sys/class/rtc --all
.  ..
```
2. 无法读取rtc时间
```bash
$hwclock --verbose
hwclock from util-linux 2.37.2
System Time: 1739849447.403260
Trying to open: /dev/rtc0
Trying to open: /dev/rtc
Trying to open: /dev/misc/rtc
No usable clock interface found.
hwclock: Cannot access the Hardware Clock via any known method.
```

3. 内核rtc模块已加载
```bash
$ lsmod | grep rtc
rtc_rv8803             20480  0
```

4. 另外，在之前的调试中也一直找不到设备树
```bash
$ ls /boot --all
.  ..
```
