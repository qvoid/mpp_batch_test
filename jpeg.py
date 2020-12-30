"""jpeg.py: parse jpeg file
"""

import struct
from enum import Enum

# Define markers
MARKERS = {}
# Start Of Frame markers, non-differential, Huffman coding
MARKERS[b'\xff\xc0'] = 'SOF0'       # Baseline DCt
MARKERS[b'\xff\xc1'] = 'SOF1'       # Extended sequential DCT
MARKERS[b'\xff\xc2'] = 'SOF2'       # Progressive DCT
MARKERS[b'\xff\xc3'] = 'SOF3'       # Lossless (sequential)
# Start Of Frame markers, differential, Huffman coding
MARKERS[b'\xff\xc5'] = 'SOF5'
MARKERS[b'\xff\xc6'] = 'SOF6'
MARKERS[b'\xff\xc7'] = 'SOF7'
# Start Of Frame markers, non-differential, arithmetic coding
MARKERS[b'\xff\xc8'] = 'JPG'
MARKERS[b'\xff\xc9'] = 'SOF9'
MARKERS[b'\xff\xca'] = 'SOF10'
MARKERS[b'\xff\xcb'] = 'SOF11'
# Start Of Frame markers, differential arithmetic coding
MARKERS[b'\xff\xcd'] = 'SOF13'
MARKERS[b'\xff\xce'] = 'SOF14'
MARKERS[b'\xff\xcf'] = 'SOF15'

MARKERS[b'\xff\xc4'] = 'DHT'        # Define Huffman table(s)
# Arithmetic coding conditioning specification
MARKERS[b'\xff\xcc'] = 'DAC'

# Restart interval termination
MARKERS[b'\xff\xd0'] = 'RST0'
MARKERS[b'\xff\xd1'] = 'RST1'
MARKERS[b'\xff\xd2'] = 'RST2'
MARKERS[b'\xff\xd3'] = 'RST3'
MARKERS[b'\xff\xd4'] = 'RST4'
MARKERS[b'\xff\xd5'] = 'RST5'
MARKERS[b'\xff\xd6'] = 'RST6'
MARKERS[b'\xff\xd7'] = 'RST7'

# Ohter markers
MARKERS[b'\xff\xd8'] = 'SOI'        # Start of image
MARKERS[b'\xff\xd9'] = 'EOI'        # End of image
MARKERS[b'\xff\xda'] = 'SOS'        # Start of scan
MARKERS[b'\xff\xdb'] = 'DQT'        # Define quantization table(s)
MARKERS[b'\xff\xdc'] = 'DNL'        # Define number of lines
MARKERS[b'\xff\xdd'] = 'DRI'        # Define restart interval
MARKERS[b'\xff\xde'] = 'DHP'        # Define hierarchical progression
MARKERS[b'\xff\xdf'] = 'EXP'        # Expand reference components(s)

# Reserved for application segments
MARKERS[b'\xff\xe0'] = 'APP0'
MARKERS[b'\xff\xe1'] = 'APP1'
MARKERS[b'\xff\xe2'] = 'APP2'
MARKERS[b'\xff\xe3'] = 'APP3'
MARKERS[b'\xff\xe4'] = 'APP4'
MARKERS[b'\xff\xe5'] = 'APP5'
MARKERS[b'\xff\xe6'] = 'APP6'
MARKERS[b'\xff\xe7'] = 'APP7'
MARKERS[b'\xff\xe8'] = 'APP8'
MARKERS[b'\xff\xe9'] = 'APP9'
MARKERS[b'\xff\xea'] = 'APP10'
MARKERS[b'\xff\xeb'] = 'APP11'
MARKERS[b'\xff\xec'] = 'APP12'
MARKERS[b'\xff\xed'] = 'APP13'
MARKERS[b'\xff\xee'] = 'APP14'
MARKERS[b'\xff\xef'] = 'APP15'

# Reserved for JPEG extensions
MARKERS[b'\xff\xf0'] = 'JPG0'
MARKERS[b'\xff\xf1'] = 'JPG1'
MARKERS[b'\xff\xf2'] = 'JPG2'
MARKERS[b'\xff\xf3'] = 'JPG3'
MARKERS[b'\xff\xf4'] = 'JPG5'
MARKERS[b'\xff\xf6'] = 'JPG6'
MARKERS[b'\xff\xf7'] = 'JPG7'
MARKERS[b'\xff\xf8'] = 'JPG8'
MARKERS[b'\xff\xf9'] = 'JPG9'
MARKERS[b'\xff\xfa'] = 'JPG10'
MARKERS[b'\xff\xfb'] = 'JPG11'
MARKERS[b'\xff\xfc'] = 'JPG12'
MARKERS[b'\xff\xfd'] = 'JPG13'

MARKERS[b'\xff\xfe'] = 'COM'        # Comment

# Reserved markers
MARKERS[b'\xff\x01'] = 'TEM'        # For temporary private use in arithmetic coding
MARKERS[b'\xff\x02'] = 'RES'        # Reserved

class FORMAT(Enum):
    UKNOWN = -1
    YUV400 = 0
    YUV411 = 1
    YUV420 = 2
    YUV422 = 3
    YUV440 = 4
    YUV444 = 5
    RGB888 = 6
    BGR565 = 7

class JPEGFile(object):
    def __init__(self, filename):
        self.filename = filename
        self.color_format = FORMAT.UKNOWN
    
    def getWidth(self):
        return self.width

    def getHeight(self):
        return self.height

    def getNcomponents(self):
        return self.n_components

    def getSampleFactor(self):
        return self.sample_factor

    def getPrecision(self):
        return self.precision

    def getColorFormat(self):
        return self.color_format

    def getFileSize(self):
        return self.file_size
    
    def parse(self):
        fileobj = open(self.filename, 'rb')
        contents = fileobj.read()
        fileobj.close()
        self.file_size = len(contents)

        start = 0
        end = 0
        is_sof0_found = False

        #"""
        #The JFIF is entirely compoatible with the standard JPEG interchange format;
        #the only additional requirement is the mandatory presence of the APP0 marker
        #right after the SOI marker.
        #"""
        #if (contents[0 : 4] != b'\xff\xd8\xff\xe0'):
        #    print(self.filename, "is not a JFIF")
        #    return -1
        if contents[0 : 2] != b'\xff\xd8':
            print(self.filename, "is not JFIF")
            return False

        start = 2

        while True:
            tmp = contents[start : start + 2]
            length = (contents[start + 2] << 8) + contents[start + 3]
            end = start + length + 2 - 1
            if tmp in MARKERS:
                print("found marker: ", MARKERS[tmp], tmp, "length: ", length)

            if tmp == b'\xff\xc0':
                is_sof0_found = True
                self.precision = contents[start + 4]
                self.height = (contents[start + 5] << 8) + contents[start + 6]
                self.width = (contents[start + 7] << 8) + contents[start + 8]
                self.n_components = contents[start + 9]
                n_com = self.n_components
                self.sample_factor = 0
                while n_com > 0:
                    n_com = n_com - 1
                    self.sample_factor += (contents[start + 9 + n_com * 3 + 2] << (8 * n_com))
                break
            elif tmp == b'\xff\xd9':
                print("EOI found")
                break
            else:
                start = end + 1
                if start > len(contents):
                    print("end of file")
                    break
                continue

        if not is_sof0_found:
            return False

        if self.sample_factor == 0x111122:
            self.color_format = FORMAT.YUV420
        elif self.sample_factor == 0x111121:
            self.color_format = FORMAT.YUV422
        elif self.sample_factor == 0x111112:
            self.color_format = FORMAT.YUV440
        elif self.sample_factor == 0x111111:
            self.color_format = FORMAT.YUV444
        elif self.sample_factor == 0x111141:
            self.color_format = FORMAT.YUV411
        elif self.sample_factor == 0x11:
            self.color_format = FORMAT.YUV400
        else:
            print("unknown color format")
            return False

        print("width: ", self.width, "height: ", self.height, "format: ", self.color_format, self.precision, self.n_components)
        return True
