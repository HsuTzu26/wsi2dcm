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
Patch extraction
 Dependencies:
     Pip modules: numpy, futures, pillow
"""

from __future__ import absolute_import
from __future__ import division
import os
import traceback
from concurrent import futures
from multiprocessing import cpu_count
from api.imgfile_info import imgfile_info
import numpy as np
from PIL import Image
from PySide6.QtCore import Signal


def write_image(pixels, patch_width, patch_height, file_name, image_name):
    """
    Save extracted regions as Patches to Disk
    :param pixels: Buffer
    :param patch_width: Width of patch
    :param patch_height: Height of patch
    :param file_name: Output filename
    :param image_name: isyntax file name
    :return: None
    """
    try:
        # Replace RGB with RGBA for aplha channel
        image = Image.frombuffer('RGB', (int(patch_width), int(patch_height)), pixels, 'raw',
                                 'RGB', 0, 1)
        image.save("." + os.path.sep + image_name + os.path.sep + str(file_name))
        #print("Patch(es) Successfully Generated")
    except RuntimeError:
        traceback.print_exc()


def get_patch_properties(region, view, isyntax_file_name):
    """
    As the input Patch size is from User which is at Level 0 representation.
    Derive Patch Size for the given Level (it defines the output patch image size too)
    :param region: Region
    :param view: view object
    :param isyntax_file_name: isyntax_file_name
    :return: patch_width,patch_height
    """
    # View Range is defined as a closed set i.e. the start and end index is inclusive
    # For example, for startIndex = 0 and endIndex = 511, the size is 512

    x_start, x_end, y_start, y_end, level = region.range
    dim_ranges = view.dimension_ranges(level)
    patch_width = int(1+(x_end-x_start)/dim_ranges[0][1])
    patch_height = int(1+(y_end-y_start)/dim_ranges[1][1])
    file_name = "{}_{}_{}_{}_{}_{}.png".format(isyntax_file_name, str(x_start),
                                               str(y_start), str(x_end + (2 ** level)),
                                               str(y_end + (2 ** level)), str(level))
    
    """
    file_name = "layer_{}_region_{}_{}.png".format(str(level), str(y_start), str(x_start))
    """
    return patch_width, patch_height, file_name


def extract_pixel_data(view, regions, pixel_engine, image_name, isyntax_file_name, file_info:imgfile_info, update_signal:Signal):
    """
    Extracting patches from source view
    :param view: source view object
    :param regions: Requested Regions
    :param pixel_engine: Object of pixel engine
    :param image_name: Output Image name
    :param isyntax_file_name: iSyntax Image Name
    :return: None
    """
    try:

        # Employing worker threads to demonstrate parallel processing can be employed
        # as and when the patches are returned by the PixelEngine
        jobs = ()
        remaining_regions = len(regions)

        with futures.ThreadPoolExecutor(max_workers=cpu_count()) as executor:
            while remaining_regions > 0:
                #print("Requesting regions batch")
                # This call returns the list of available patches
                # The SDK employs parallelism to prepare these patches (get Pixel data)
                # So one can also consume the available patches in parallel as they are made
                # available incrementally. If a single file is opened over a pixel engine object,
                # the output performance of pixel engine can be enhanced
                # by extracting patches through
                # wait_any() call. In case of multiple files the wait_any(regions) is suggested
                regions_ready = pixel_engine.wait_any()
                #print("Regions returned = " + str(len(regions_ready)))
                remaining_regions -= len(regions_ready)
                for region in regions_ready:
                    patch_width, patch_height, file_name = get_patch_properties(region, view,
                                                                                isyntax_file_name)
                    # Calculate patch image size for writting to disk
                    # 3 is samples per pixels for RGB
                    # 4 is samples per pixels for RGBA
                    pixel_buffer_size = patch_width * patch_height * 3
                    pixels = np.empty(int(pixel_buffer_size), dtype=np.uint8)
                    region.get(pixels)
                    # remove the patch from the region list to ensure we aren't duplicating read
                    # of  patches and the loop does terminate when all the patches are consumed.
                    regions.remove(region)
                    # Submitting to Job Thread for writing patches to disk
                    # print(f"{isyntax_file_name}|Generate Image File:{file_name}")
                    file_info.convert_status = f"讀取圖片(剩下{len(regions)}張)"
                    # update_signal.emit(0)
                    jobs = jobs + (executor.submit(write_image, pixels, patch_width, patch_height,
                                                   file_name, image_name),)
        futures.wait(jobs, return_when=futures.ALL_COMPLETED)
    except RuntimeError:
        traceback.print_exc()
