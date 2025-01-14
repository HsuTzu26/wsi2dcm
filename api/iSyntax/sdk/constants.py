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
Constants
"""

from __future__ import absolute_import
from platform import system


class Constants:
    """
    This class has all the constants used by the viewer sample code.
    """
    tile_width = 512
    tile_height = 512
    tile_cache_horizontal = 4
    tile_cache_vertical = 2
    pixel_pan = 1
    level_shift_factor = 1
    sample_per_pixel = 3
    level_zero = 0
    macro_label_win_size = (1200, 400)
    macro_image_size = (950, 400)
    label_image_size = (250, 400)
    macro_label_win_size_ratio = (0.625, 0.39)
    macro_image_size_ratio = (0.8, 1)
    label_image_size_ratio = (0.199, 1)
    property_win_size_ratio = (0.625, 0.56)
    property_list = []
    sharpness_gain_sgs = 4
    sharpness_gain_ufs = 2
    color_gain = 1
    contrast_clip_limit = 1.2
    color_correction_gamma = 2.4
    color_correction_black_point = 0
    color_correction_white_point = 1

    @staticmethod
    def get_mouse_wheel():
        """
        Sets mouse wheel as per platform(OS)
        :return: mouse_wheel_down, mouse_wheel_up
        """
        if "Windows" in system():
            mouse_wheel_down = -120
            mouse_wheel_up = 120
        else:
            mouse_wheel_down = 5
            mouse_wheel_up = 4
        return mouse_wheel_down, mouse_wheel_up

    @staticmethod
    def get_property_list():
        """
        Method to get property List
        """
        return Constants.property_list
