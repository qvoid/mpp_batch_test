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

device_name = '1SLX42HHQB'
test_dir = './'
board_dir = '/data/tmp'
result_dir = 'result'

class RESULT(Enum):
    OK = 0
    NOK = 1

class JpegInfo:
    def __init__(self, file_name, width, height, color_fmt):
        self.file_name = file_name
        self.width = width
        self.height = height
        self.fmt = str.lower(str(color_fmt))
        self.path = ""
        self.md5 = ""
        self.hw_cycle = 0
        self.kernel_time = 0
        self.proc_time = 0
        self.hw_fps = 0
        self.proc_fps = 0
        self.out_yuv = 0
        self.result = 0

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

if not adb.mkdir("/data/", "tmp"):
    log_exit("failed to create /data/tmp on device")

adb.run_and_return_output(['shell', 'echo', '0x100', '>', '/sys/module/rk_vcodec/parameters/mpp_dev_debug'])
adb.set_property("jpegd_debug", '0xff')

if not os.path.exists(test_dir + result_dir):
    os.makedirs(test_dir + result_dir)

#device_arch = adb.get_device_arch()
#adb.check_run(['shell', 'ls'])
#shell_cmd = 'cd /data/tmp && ls'
#sys.exit(subprocess.call([adb.adb_path, 'shell', shell_cmd]))

def decode_file(file_name):
    print("******** Start decode: ", file_name);
    jpg_file = JPEGFile(file_name)
    jpg_file.parse()
    jpg_info = JpegInfo(file_name, jpg_file.getWidth(), jpg_file.getHeight(), jpg_file.getColorFormat().name)
    jpg_info.md5 = hashlib.md5(open(file_name, 'rb').read()).hexdigest()

    adb.run(['push', file_name, board_dir])
    adb.run(['shell', 'cd', board_dir, '&&', 'rm', 'output00.yuv'])
    adb.run(['shell', 'cd', board_dir, '&&', 'rm', 'dec.log'])
    adb.run(['shell', 'dmesg', '-c'])
    adb.run(['shell', 'logcat', '-c'])
    adb.run(['shell', 'cd', board_dir, '&&', 'mpi_dec_test', '-t', '7', \
            '-w', str(jpg_info.width), '-h', str(jpg_info.height), \
            '-i', file_name])
    name = os.path.splitext(file_name)[0]
    log_name = name + '.log'
    hor_stride = str(jpg_info.width)
    ver_stride = str(jpg_info.height)
    yuv_name = name + '_' + hor_stride + 'x' + ver_stride + '_' +jpg_info.fmt + '.yuv'
    adb.run_and_return_output(['shell', 'cd', board_dir, '&&', 'logcat', '-d', '|', 'tee', '2>&1', 'dec.log'])
    adb.run_and_return_output(['pull', '/data/tmp/output00.yuv', yuv_name])
    adb.run_and_return_output(['pull', '/data/tmp/dec.log', log_name])
    adb.run(['shell', 'cd', board_dir, '&&', 'ls', '-lh', 'output00.yuv'])
    adb.run(['shell', 'cd', board_dir, '&&', 'rm', 'output00.yuv'])
    cmd('mv ' + log_name + ' ' + test_dir + result_dir + '/')
    cmd('mv ' + yuv_name + ' ' + test_dir + result_dir + '/')


def decode_dir(dir_path):
    for file_name in listdir(dir_path):
        ext = os.path.splitext(file_name)[1]
        if ext != '.jpg' and ext != '.jpeg':
            continue
        decode_file(file_name)
        break

"""
Summary decode result: speed, average fps,
"""
def sum_result():
    return

def main():
    decode_dir(test_dir)

if __name__ == '__main__':
    main()

