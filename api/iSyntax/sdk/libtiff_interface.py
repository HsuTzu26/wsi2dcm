# !/usr/bin/env python3
# -*- coding: utf-8 -*-

# Copyright © 2021 Koninklijke Philips N.V. All Rights Reserved.

# A copyright license is hereby granted for redistribution and use of the
# Software in source and binary forms, with or without modification, provided
# that the following conditions are met:
# • Redistributions of source code must retain the above copyright notice, this
#   copyright license and the following disclaimer.
# • Redistributions in binary form must reproduce the above copyright notice,
#   this copyright license and the following disclaimer in the documentation
#   and/ or other materials provided with the distribution.
# • Neither the name of Koninklijke Philips N.V. nor the names of its
#   subsidiaries may be used to endorse or promote products derived from the
#   Software without specific prior written permission.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
# AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
# IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE
# ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT OWNER OR CONTRIBUTORS BE
# LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR
# CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF
# SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS
# INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN
# CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE)
# ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED
# OF THE POSSIBILITY OF SUCH DAMAGE.

"""
libTIFF interfacing code
"""

from __future__ import absolute_import
from __future__ import division
import sys
import ctypes
import subprocess


def load_libtiff_library():
    """
    Load Libtiff library as per the OS
    """
    # Specify the name and path for the libtiff (.dll/.so) accordingly.
    # Change this path according to your Operating System(OS)
    lib_tiff = ''
    if "win" in sys.platform:
        lib_tiff = ctypes.cdll.LoadLibrary(r'libtiff-5.dll')
    elif "CentOS" in subprocess.check_output(["lsb_release", "-is"]).decode("utf-8"):
        lib_tiff = ctypes.cdll.LoadLibrary('/usr/lib64/libtiff.so.5')
    elif "Ubuntu" in subprocess.check_output(["lsb_release", "-is"]).decode("utf-8"):
        lib_tiff = ctypes.cdll.LoadLibrary(r'/usr/lib/x86_64-linux-gnu/libtiff.so.5')
    if lib_tiff is None:
        raise TypeError('Failed to load libtiff')
    return lib_tiff


# TIFFTAG_* constants from the header file:
TIFFTAG_IMAGEWIDTH = 256
TIFFTAG_IMAGELENGTH = 257
TIFFTAG_TILEWIDTH = 322
TIFFTAG_TILELENGTH = 323
TIFFTAG_BITSPERSAMPLE = 258
TIFFTAG_COMPRESSION = 259
COMPRESSION_JPEG = 7
TIFFTAG_SAMPLESPERPIXEL = 277
TIFFTAG_PLANARCONFIG = 284
TIFFTAG_PHOTOMETRIC = 262
TIFFTAG_JPEGQUALITY = 65537
TIFFTAG_ORIENTATION = 274
ORIENTATION_TOPLEFT = 1
TIFFTAG_JPEGCOLORMODE = 65538
JPEGCOLORMODE_RGB = 1
TIFFTAG_SUBFILETYPE = 254
PHOTOMETRIC_RGB = 2
PHOTOMETRIC_YCBCR = 6
FILETYPE_REDUCEDIMAGE = 0x1
TIFFTAG_YCBCRSUBSAMPLING = 530
BITSPERSAMPLE = 8
SAMPLESPERPIXEL = 3
PLANARCONFIG = 1
JPEGQUALITY = 80
YCBCRHORIZONTAL = 2
YCBCRVERTICAL = 2
TIFF_TILE_WIDTH = 512
TIFF_TILE_HEIGHT = 512


TIFFTAGS = {
    TIFFTAG_IMAGEWIDTH: (ctypes.c_uint32, lambda _d: _d.value),
    TIFFTAG_IMAGELENGTH: (ctypes.c_uint32, lambda _d: _d.value),
    TIFFTAG_SAMPLESPERPIXEL: (ctypes.c_uint32, lambda _d: _d.value),
    TIFFTAG_SUBFILETYPE: (ctypes.c_uint32, lambda _d: _d.value),
    TIFFTAG_TILELENGTH: (ctypes.c_uint32, lambda _d: _d.value),
    TIFFTAG_TILEWIDTH: (ctypes.c_uint32, lambda _d: _d.value),
    TIFFTAG_BITSPERSAMPLE: (ctypes.c_uint16, lambda _d: _d.value),
    TIFFTAG_COMPRESSION: (ctypes.c_uint16, lambda _d: _d.value),
    TIFFTAG_ORIENTATION: (ctypes.c_uint16, lambda _d: _d.value),
    TIFFTAG_PHOTOMETRIC: (ctypes.c_uint16, lambda _d: _d.value),
    TIFFTAG_PLANARCONFIG: (ctypes.c_uint16, lambda _d: _d.value),
    TIFFTAG_JPEGQUALITY: (ctypes.c_int, lambda _d: _d.value),
    TIFFTAG_JPEGCOLORMODE: (ctypes.c_int, lambda _d: _d.value),
    TIFFTAG_YCBCRSUBSAMPLING: (ctypes.c_int, lambda _d: _d.value)

}


class TIFF(ctypes.c_void_p):
    """ Holds a pointer to TIFF object.
    To open a tiff file for reading, use
    tiff = TIFF.open (filename, more='r')
    """

    def open(filename, mode='r'):  # pylint: disable=no-self-argument
        """ Open tiff file as TIFF.
        """
        tiff = LIBTIFF.TIFFOpen(filename, mode)
        if tiff.value is None:
            raise TypeError('Failed to open file {}'.format(b'filename'))
        return tiff

    def write_directory(self):
        """
        WriteDirectory
        :return: None
        """
        result = LIBTIFF.TIFFWriteDirectory(self)
        assert result == 1, result

    closed = False

    def close(self):
        """
        Method to close tiff file handle
        :return: None
        """
        if not self.closed and self.value is not None:
            LIBTIFF.TIFFClose(self)
            self.closed = True

    def set_field(self, tag, value, count=None):
        """
        Set TIFF field value with tag.
        tag can be numeric constant TIFFTAG_<tagname> or a
        string containing <tagname>.
        :param tag: Tiff tag
        :param value: Tag value
        :param count:
        :return: result
        """
        if isinstance(tag, str):
            tag = eval('TIFFTAG_' + tag.upper())  # pylint: disable=eval-used
        tiff_tag = TIFFTAGS.get(tag)
        if tiff_tag is None:
            print('Warning: no tag %r defined' % tag)
            return None
        data_type = tiff_tag[0]
        if data_type == ctypes.c_float:
            data_type = ctypes.c_double
        result = self.libtiff_set_field_interface(count, tag, data_type, value)
        return result

    def libtiff_set_field_interface(self, count, tag, data_type, value):
        """
        libtiff_set_field_interface
        :param count:
        :param tag: TIFF TAG
        :param data_type: data type
        :param value: Tag value
        :return: result
        """
        try:
            # value is an iterable
            data = data_type(*value)
        except TypeError:
            data = data_type(value)
        if count is None:
            LIBTIFF.TIFFSetField.argtypes = LIBTIFF.TIFFSetField.argtypes[:2] + [data_type]
            result = LIBTIFF.TIFFSetField(self, tag, data)
        else:
            LIBTIFF.TIFFSetField.argtypes = LIBTIFF.TIFFSetField.argtypes[:2] + [ctypes.c_uint,
                                                                                 data_type]
            result = LIBTIFF.TIFFSetField(self, tag, count, data)
        return result

    def compute_tile(self, x_coord, y_coord, planar_configuration, sample):
        """
        Compute Tilw Wrapper
        """
        return LIBTIFF.TIFFComputeTile(self, x_coord, y_coord, planar_configuration, sample)

    def write_encoded_tile(self, offset, level, data, data_size):
        """
        Write Encoded Tile Wrapper
        """
        return LIBTIFF.TIFFWriteEncodedTile(self, self.compute_tile(offset[0], offset[1],
                                                                    level, 0), data, data_size)

    def set_attribute(self, key, value):
        """
        Set Tiff file attributes
        :param key: Associated key
        :param value: value of key
        :return: None
        """
        assert self.set_field(key, value) == 1, \
            "could not set {} tag".format(str(key))

    def set_tiff_file_attributes(self, tiff_dim, level, start_level):
        """
        Setting tiff file common attributes
        :param tiff_dim: TIFF Dimensions at level
        :param level: Current level
        :param start_level: STarting level of TIFF file
        :return: None
        """
        level_scale_factor = 2 ** level
        # For subdirectories corresponding to the multi-resolution pyramid, set the following
        # Tag for all levels but the initial level
        if level > start_level:
            self.set_attribute(TIFFTAG_SUBFILETYPE, FILETYPE_REDUCEDIMAGE)

        # Setting TIFF file attributes
        self.set_attribute(TIFFTAG_IMAGEWIDTH, int(tiff_dim[0] / level_scale_factor))
        self.set_attribute(TIFFTAG_IMAGELENGTH, int(tiff_dim[1] / level_scale_factor))
        self.set_attribute(TIFFTAG_TILEWIDTH, TIFF_TILE_WIDTH)
        self.set_attribute(TIFFTAG_TILELENGTH, TIFF_TILE_HEIGHT)
        self.set_attribute(TIFFTAG_BITSPERSAMPLE, BITSPERSAMPLE)
        self.set_attribute(TIFFTAG_SAMPLESPERPIXEL, SAMPLESPERPIXEL)
        self.set_attribute(TIFFTAG_PLANARCONFIG, PLANARCONFIG)
        self.set_attribute(TIFFTAG_COMPRESSION, COMPRESSION_JPEG)
        self.set_attribute(TIFFTAG_JPEGQUALITY, JPEGQUALITY)
        self.set_attribute(TIFFTAG_ORIENTATION, ORIENTATION_TOPLEFT)

        # To choose bewteen RGB and YCbCr color model, uncomment the following line,
        # self.set_attribute(TIFFTAG_PHOTOMETRIC, PHOTOMETRIC_RGB)
        # Comment the following lines to change to RGB
        self.set_attribute(TIFFTAG_PHOTOMETRIC, PHOTOMETRIC_YCBCR)
        self.set_attribute(TIFFTAG_JPEGCOLORMODE, JPEGCOLORMODE_RGB)
        assert self.set_field(TIFFTAG_YCBCRSUBSAMPLING, YCBCRHORIZONTAL,
                              YCBCRVERTICAL) == 1, "could not set YCbCr subsample tag"


LIBTIFF = load_libtiff_library()
LIBTIFF.TIFFOpen.restype = TIFF
LIBTIFF.TIFFOpen.argtypes = [ctypes.c_char_p, ctypes.c_char_p]
LIBTIFF.TIFFSetField.restype = ctypes.c_int
LIBTIFF.TIFFSetField.argtypes = [TIFF, ctypes.c_uint, ctypes.c_void_p]  # last item is reset in
# TIFF.SetField method
LIBTIFF.TIFFWriteTile.restype = ctypes.c_int32
LIBTIFF.TIFFWriteTile.argtypes = [TIFF, ctypes.c_void_p, ctypes.c_uint32, ctypes.c_uint32,
                                  ctypes.c_uint32, ctypes.c_uint16]
LIBTIFF.TIFFWriteEncodedTile.restype = ctypes.c_int32
LIBTIFF.TIFFWriteEncodedTile.argtypes = [TIFF, ctypes.c_uint32, ctypes.c_void_p, ctypes.c_int32]

LIBTIFF.TIFFClose.restype = None
LIBTIFF.TIFFClose.argtypes = [TIFF]


# ################ #END-----libTIFF interfacing code------END ################
