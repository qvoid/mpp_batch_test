#!/usr/bin/python3
# -*- coding: UTF-8 -*-

import subprocess
import hashlib
import sys
import os
from os import listdir
import os.path
from os.path import isfile, join
import time
import re
from utils import *
from enum import Enum
from jpeg import *

"""
Replace device by yours.
Device name can be found by "adb devices"
"""
device_name = '1SLX42HHQB'
test_dir = './'             # directory that store jpeg files
board_dir = '/data/tmp'     # directory on board that store temporay test file and result
result_dir = 'result'       # directory under test_idr that store test result 
test_lib = './lib'          # directory that store test libraries
test_bin = './bin'          # directory that store test binary
CLK_FREQ = 297000000
DEBUG_MODE = False
IRQ_OK = '0x0000434c'

class JpegInfo:
    def __init__(self, file_name, width, height, color_fmt):
        self.file_name = file_name
        self.width = width
        self.height = height
        self.fmt = str.lower(str(color_fmt))
        self.path = ""
        self.md5 = ""
        self.hw_cycle = 0
        self.irq = ""
        self.kernel_time = 0        # time in us
        self.hw_fps = 0
        self.hw_pixel_per_sec = 0
        self.proc_time = 0          # time in us
        self.proc_fps = 0
        self.result = 0
        self.yuv = ""
        self.log = ""

def cmd(command):
    subp =  subprocess.Popen(command, shell = True, stdout = subprocess.PIPE, stderr = subprocess.PIPE, encoding = "utf-8")
    subp.wait(2)
    std_out_data, std_err_data = subp.communicate()
    ret = False
    if subp.poll() == 0:
        print("cmd Succeeded: ", command)
        ret = True
    else:
        print("cmd Failed: ", command)
        ret = False
    return (ret, std_out_data, std_err_data)

def check_device(device_name):
    ret, out, err = cmd("adb devices")
    if not ret:
       print("list adb devices failed") 
       return False
    if re.search(device_name, out) != None:
        print("found device: ", device_name)
        return True
    else:
        print("not found device: ", device_name)
        return False

if not check_device(device_name):
    log_exit("Please check device connnection")

adb = AdbHelper(device_name)
if not adb.switch_to_root():
    log_exit("failed to root device: ", device_name)
if not adb.remount():
    log_exit("failed to remount device: ", device_name)

#if not os.path.exists(test_lib):
#    log_exit("Not exit test libs directory")
#else:
#    adb.run_and_return_output('push', test_lib, '/vendor/lib/')

#if not os.path.exists(test_bin):
#    log_exit("Not exit test bin directory")
#else:
#    adb.run_and_return_output('push', test_bin, '/vendor/bin/')

if not adb.mkdir("/data/", "tmp"):
    log_exit("failed to create /data/tmp on device")

if DEBUG_MODE:
    # 0x100 for debug kernel time
    adb.run_and_return_output(['shell', 'echo', '0x100', '>', '/sys/module/rk_vcodec/parameters/mpp_dev_debug'])
    adb.set_property("jpegd_debug", '0xff')
else:
    adb.run_and_return_output(['shell', 'echo', '0x100', '>', '/sys/module/rk_vcodec/parameters/mpp_dev_debug'])
    adb.set_property("jpegd_debug", '0')

if not os.path.exists(test_dir + result_dir):
    os.makedirs(test_dir + result_dir)

#device_arch = adb.get_device_arch()
#adb.check_run(['shell', 'ls'])
#shell_cmd = 'cd /data/tmp && ls'
#sys.exit(subprocess.call([adb.adb_path, 'shell', shell_cmd]))

def decode_file(file_name):
    print("******** Start decode: ", file_name);

    name = os.path.splitext(file_name)[0]

    jpg_file = JPEGFile(file_name)
    jpg_file.parse()
    jpg_info = JpegInfo(file_name, jpg_file.getWidth(), jpg_file.getHeight(), jpg_file.getColorFormat().name)
    jpg_info.md5 = hashlib.md5(open(file_name, 'rb').read()).hexdigest()
    jpg_info.path = test_dir
    hor_stride = str(jpg_info.width)
    ver_stride = str(jpg_info.height)

    yuv_name = name + '_' + hor_stride + 'x' + ver_stride + '_' + jpg_info.fmt + '.yuv'
    log_name = name + '.log'

    adb.run(['push', file_name, board_dir])
    adb.run(['shell', 'dmesg', '-C'])
    adb.run(['shell', 'logcat', '-c'])
    ret, stdoutdata = adb.run_and_return_output(['shell', 'cd', board_dir, '&&', 'mpi_dec_test', '-t', '7', \
            '-w', str(jpg_info.width), '-h', str(jpg_info.height), \
            '-i', file_name], log_output=False)

    adb.run_and_return_output(['shell', 'cd', board_dir, '&&', 'logcat', '-d', '|', 'tee', '2>&1', 'dec.log'], log_output=False)
    adb.run(['pull', '/data/tmp/dec.log', log_name])
    cmd('mv ' + log_name + ' ' + test_dir + result_dir + '/')
    adb.run(['shell', 'cd', board_dir, '&&', 'rm', 'dec.log'])

    if DEBUG_MODE:
        ret = adb.run(['pull', '/data/tmp/output00.yuv', yuv_name])
        if ret:
            jpg_info.result = False
        else:
            adb.run(['shell', 'cd', board_dir, '&&', 'rm', 'output00.yuv'])
            cmd('mv ' + yuv_name + ' ' + test_dir + result_dir + '/')

    if not ret:
        jpg_info.result = False

    match_cycle = re.search('decode one frame in cycles: (\d+)', stdoutdata)
    if match_cycle:
        jpg_info.hw_cycle = int(match_cycle.group(1))

    match_irq = re.search('decode result: irq (.{10})', stdoutdata)
    if match_irq:
        jpg_info.irq = match_irq.group(1)
    
    match_cost_time = re.search('mpi_dec_test cost time: (\d+)', stdoutdata)
    if match_cost_time:
        jpg_info.proc_time = int(match_cost_time.group(1))

    if DEBUG_MODE:
        ret = False
        stdoutdata = None
        stderrdata = None
        ret, stdoutdata, stderrdata = cmd("grep -i 'session' " + result_dir + '/' + log_name + " | grep 'jpegd' | grep 'time' | awk '{print $12}'")
        if ret:
            jpg_info.kernel_time = int(stdoutdata)

    if jpg_info.irq == IRQ_OK:
        jpg_info.result = True
    else:
        jpg_info.result = False
    
    pixels = jpg_info.width * jpg_info.height
    if jpg_file.getColorFormat() == FORMAT.YUV420 or jpg_file.getColorFormat() == FORMAT.YUV411:
        pixels = pixels * 1.5
    elif jpg_file.getColorFormat() == FORMAT.YUV422 or jpg_file.getColorFormat() == FORMAT.YUV440:
        pixels = pixels * 2
    elif jpg_file.getColorFormat() == FORMAT.YUV444:
        pixels = pixels * 3
        
    jpg_info.hw_pixel_per_sec = format(pixels / jpg_info.hw_cycle * CLK_FREQ, '.2f')
    jpg_info.hw_fps = format(CLK_FREQ / jpg_info.hw_cycle, '.2f')

    jpg_info.proc_fps = format(1000000 / jpg_info.proc_time, '.2f')

    print(jpg_info.irq, jpg_info.result, jpg_info.hw_cycle, jpg_info.hw_fps, jpg_info.hw_pixel_per_sec, \
            jpg_info.proc_time, jpg_info.proc_fps)
    
    return jpg_info
    

def decode_dir(dir_path):
    for file_name in listdir(dir_path):
        ext = os.path.splitext(file_name)[1]
        if ext != '.jpg' and ext != '.jpeg':
            continue
        decode_file(file_name)

"""
Summary decode result: speed, average fps,
"""
def sum_result():
    return

def main():
    decode_dir(test_dir)

if __name__ == '__main__':
    main()

