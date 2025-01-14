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
Pixel Engine Connector
"""

from __future__ import absolute_import
from pixelengine import PixelEngine
from backends import Backends
from constants import Constants



class PixelEngineConnector:
    """
    This class initializes pixelengine and its properties.
    """
    def __init__(self, input_file, args_backend, args_display_view):
        """
        Constructor to initialize the pixel engine and its properties
        :param input_file: IsyntaxFilePath
        :param args_backend: The requested backend
        """
        # Initializing Pixel engine
        backends = Backends()
        render_backend, render_context = backends.initialize_backend(args_backend)
        self._pixel = PixelEngine(render_backend, render_context)
        self._pixel["in"].open(input_file)
        if args_display_view:
            self._view = self._pixel["in"]["WSI"].display_view
            self.set_display_view_properties()
        else:
            self._view = self._pixel["in"]["WSI"].source_view
            # To query for raw pixel data (source view), the bits truncation should be disabled.
            trunc_bits = {0: [0, 0, 0]}
            self._view.truncation(False, False, trunc_bits)
            if self._view.bits_stored == 9:
                # As SGS generates 9bit raw images(i2syntax / isyntax)
                # Converting this 9-bit pixel data to 8-bit pixel data to render in 8-bit display monitor.
                # Also making this data UFS equivalent by applying ICC Profile matrix
                # Note: ICC profile depends on the scanner
                self._view = self._view.add_user_view()
                matrix_filter = self._view.add_filter("3x3Matrix16")
                icc_matrix = self._pixel["in"]["WSI"].icc_matrix
                self._view.filter_parameter_matrix3x3(matrix_filter, "matrix3x3", icc_matrix)
                self._view.add_filter("Linear16ToSRGB8")
        self._levels = self._view.num_derived_levels + 1
        self.get_image_properties()

    def set_display_view_properties(self):
        """
        Method to set display view specific properties based on UFS/SGS Images.
        :return: None
        """
        # For SGS files the default value for sharpness should be 4 and color_gain filter should be
        # applied with value 1 instead of contrast_clip_limit.
        if self._pixel["in"]["WSI"].source_view.bits_stored == 8:
            self._view.contrast_clip_limit = float(Constants.contrast_clip_limit)
            self._view.sharpness = float(Constants.sharpness_gain_ufs)
        else:
            self._view.sharpness = float(Constants.sharpness_gain_sgs)
            self._view.color_gain = float(Constants.color_gain)
        self._view.color_correction_gamma = float(Constants.color_correction_gamma)
        self._view.color_correction_black_point = float(Constants.color_correction_black_point)
        self._view.color_correction_white_point = float(Constants.color_correction_white_point)


    def get_image_properties(self):
        """
        Method to get image file specific properties.
        :return: None
        """
        property_dict = [
            ["barcode", check_property(self._pixel["in"].barcode)],
            ["num_derived_levels",
             check_property(self._pixel["in"]["WSI"].source_view.num_derived_levels)],
            ["wavelet", check_property(self._pixel["in"]["WSI"].pixel_transform)],
            ["quality", check_property(self._pixel["in"]["WSI"].quality_preset)],
            ["compressor", check_property(self._pixel["in"]["WSI"].compressor)],
            ["scanner_operator_id",
             check_property(self._pixel["in"].scanner_operator_id)],
            ["scanner_calibration_status",
             check_property(self._pixel["in"].scanner_calibration_status)],
            ["acquisition_datetime", check_property(self._pixel["in"].acquisition_datetime)],
            ["date_of_last_calibration",
             check_property(self._pixel["in"].date_of_last_calibration)],
            ["manufacturer", check_property(self._pixel["in"].manufacturer)],
            ["model_name", check_property(self._pixel["in"].model_name)],
            ["device_serial_number", check_property(self._pixel["in"].device_serial_number)],
            ["software_versions", check_property(self._pixel["in"].software_versions)],
            ["derivation_description", check_property(self._pixel["in"].derivation_description)]
        ]
        Constants.property_list = property_dict

    def get_isyntax_facade_obj(self):
        """
        :return: Returns iSyntax facade object
        """
        return self._pixel["in"]

    def get_pe(self):
        """
        Returns pixel engine object
        :return: Returns _pixel
        """
        return self._pixel

    def get_max_levels(self):
        """
        Returns the maximum number of levels associated with the iSyntax file
        :return: Returns the maximum number of levels
        """
        return self._levels

    def get_source_view(self):
        """
        Returns source view
        :return: Returns _view
        """
        return self._view

def check_property(property_value):
    """
    Method to remove blank spaces from the property values.
    :param property_value: Value of property
    :return: property value without spaces.
    """
    property_value = str(property_value)
    if len(property_value.strip()) == 0:
        return "[]"
    return property_value.strip()
