# MPP_BATCH_TEST

## 简介

---
本脚本用于通过 ADB 跑 [MPP](https://github.com/rockchip-linux/mpp) 的测试程序mpi_dec_test。当前仅仅支持JPEG解码
工作流程是：

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

1. 替换测试设备的name, (adb devices 可以获取)
2. 将lib和bin下的库和测试程序推送到板子上
3. 替换测试目录为待测试的码流目录
4. 运行 dec_test.py:

```shell
./dec_test.py | tee 2>&1 runlog
```

> dec_test.py里面解析的程序运行结果部分是通过库和bin程序中添加的 printf 打印的， 不在MPP的develop分支上, 需要单独添加
