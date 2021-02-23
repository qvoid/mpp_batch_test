# MPP_BATCH_TEST

## 简介

---
本脚本用于通过 ADB 跑 [MPP](https://github.com/rockchip-linux/mpp) 的测试程序mpi_dec_test。当前仅仅支持JPEG解码
> 本脚本仅在 Linux 平台下测试，Windows 平台测试需要做一些输入输入的文件路径的兼容。

本脚本的工作流程是：

1. 检测环境（adb 设备，需要的libmpp.so 和 测试程序等）
2. 运行解析程序，先解析出码流参数(JPEG的宽高、颜色空间等)
3. 运行mpi_dec_test
4. 获取日志，解析，记录。

文件结构:

```text
.
├── bin
│   └── mpi_dec_test
├── dec_test.py
├── __init__.py
├── jpeg.py
├── lib
│   ├── libmpp.so
│   └── libvpu.so
├── ReadMe.md
└── utils.py
```

## 如何使用

### 1. 替换测试设备的设备名
设备名可以通过运行 `adb devices 获取`，例如：
```Shell
➜  ~ adb devices
List of devices attached
1SLX42HHQB	device
```
则这里的 *1SLX42HHQB* 即是设备名，赋值给 `device_name`。

### 2. 将lib和bin下的库和测试程序推送到板子上

这部分脚本可以自动做，目前这部分代码被注释掉了，如下：
```Python
#if not os.path.exists(test_lib):
#    log_exit("Not exit test libs directory")
#else:
#    adb.run_and_return_output('push', test_lib, '/vendor/lib/')

#if not os.path.exists(test_bin):
#    log_exit("Not exit test bin directory")
#else:
#    adb.run_and_return_output('push', test_bin, '/vendor/bin/')
```

### 3. 替换测试目录为待测试的码流目录
修改代码中的 *test_dirs* 为待测试的jpeg文件的文件夹路径，可以一次测试多个文件夹
```Python
# directory that store jpeg files
test_dirs = [\
        './path-to/dir_1', \
        './path-to/dir_2'
        ]
```

### 4. 运行 dec_test.py:

如果需要检查解码后的YUV结果，需要将 *DEBUG_MODE* 设置成 True，但是 YUV文件会占很大空间，需要注意。

```shell
./dec_test.py | tee 2>&1 runlog
```

> dec_test.py里面解析的程序运行结果部分是通过库和bin程序中添加的 printf 打印的， 不在MPP的develop分支上, 需要单独添加
