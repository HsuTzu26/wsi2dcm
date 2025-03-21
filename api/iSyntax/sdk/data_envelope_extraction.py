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
This code extracts Data Envelope available in an iSyntax Image
It writes data envelopes for the given input iSyntax image as
'<image_name>_<data_envelope_number>_data_envelope.bmp'
Query: python data_envelope_extraction.py '<isyntax_image_path>'
Dependencies:
    Pip modules: numpy, futures, pillow
"""

from __future__ import absolute_import
import argparse
import traceback
import os
import math
import numpy as np
from PIL import Image
from pixelengine import PixelEngine
from backends import Backends


def main():
    """
    Initiate pixel engine object through render backend and render context
    We are using the CPU rendering option - binding software context and backend
    :return: None
    """
    backends = Backends()
    render_backend, render_context = backends.initialize_backend("SOFTWARE")
    pixel_engine = PixelEngine(render_backend, render_context)

    parser = argparse.ArgumentParser(formatter_class=argparse.RawDescriptionHelpFormatter,
                                     description="""
Extracts all data envelopes present in isyntax image
The program will extract all the data envelopes available as part of isyntax image.
To execute this program just pass the path of the iSyntax image file as command lne argument.
Eg:
python data_envelope_extraction.py "<PATH_OF_ISYNTAX_FILE>"
""")
    parser.add_argument("input_file", help="Image File")
    args = parser.parse_args()
    input_file = args.input_file
    image_name = os.path.splitext(os.path.basename(input_file))[0]
    pe_in = pixel_engine["in"]
    pe_in.open(input_file)
    # Get the source_view i.e. the view which provided raw pixel data
    view = pe_in["WSI"].source_view
    # To query for raw pixel data (source view), the truncation level should be disabled.
    truncation_level = {0: [0, 0, 0]}
    view.truncation(False, False, truncation_level)
    if view.bits_stored == 9:
        # As SGS generates 9bit raw images(i2syntax / isyntax)
        # Converting this 9-bit pixel data to 8-bit pixel data to render in 8-bit display monitor.
        # Also making this data UFS equivalent by applying ICC Profile matrix
        # Note: ICC profile depends on the scanner
        view = view.add_user_view()
        matrix_filter = view.add_filter("3x3Matrix16")
        icc_matrix = pe_in["WSI"].icc_matrix
        view.filter_parameter_matrix3x3(matrix_filter, "matrix3x3", icc_matrix)
        view.add_filter("Linear16ToSRGB8")
    # Querying number of derived levels in an iSyntax file
    num_levels = view.num_derived_levels + 1
    # Calculating the middle level (rounded) to extract data envelope since data envelope
    # indices varies based on level
    mid_level = int(math.floor(num_levels / 2))
    try:
        data_envelopes = view.data_envelopes(0).as_rectangles()
        print("Given input image contains {} levels and {} valid data"
              "envelopes with indices as".format(str(num_levels), str(len(data_envelopes))))
        patch_extract(view, data(view, mid_level), pixel_engine, mid_level, image_name)
    except RuntimeError:
        traceback.print_exc()


def write_image(pixels, width, height, file_name):
    """
    Save extracted regions as Patches to Disk
    return: None
    """
    # Replace RGB with RGBA for alpha channel
    image = Image.frombuffer('RGB', (int(width), int(height)), pixels, 'raw', 'RGB', 0, 1)
    image.save(file_name)


def data(view, mid_level):
    """
    Creating data envelopes list
    as_rectangles method returns the min and max indices
    for the bounding rectangle of the data envelope i.e.
    (x-min, x-max, y-min, y-max) - refer to the image below

(x-min, y-min)                        (x-max, y-min)
    *-------------------------------------------*
    |                                           |
    |                                           |
    |                                           |
    |                                           |
    *-------------------------------------------*
(x-min, y-max)                        (x-max, y-max)

    :param view: Source View
    :param mid_level: The middle level of isyntax file
    :return: ranges
    """
    ranges = []
    for step, envelope in enumerate(view.data_envelopes(mid_level).as_rectangles()):
        print("DataEnvelope_{}: {}".format(step, envelope))
        envelope.append(mid_level)
        ranges.append(envelope)
    return ranges


def calculate_width_height(view_range, view):
    """
    Calculate Width and Height
    """
    x_start, x_end, y_start, y_end, level = view_range
    dim_ranges = view.dimension_ranges(level)
    # Calculate width and height for tile size with respect to mid level
    width = int(1 + (x_end - x_start) / dim_ranges[0][1])
    height = int(1 + (y_end - y_start) / dim_ranges[1][1])
    return width, height


def patch_extract(view, view_ranges, pixel_engine, mid_level, image_name):
    """
    :param view: Source view object
    :param view_ranges: list of view range of every data envelope
    :param pixel_engine: Object of pixel engine class
    :param mid_level: The middle level of isyntax file
    :param image_name: The filename of extracted data envelope
    :return: None
    """
    print("Extracting data envelopes at level {}".format(str(mid_level)))
    increment = 0
    # Prepare request against the Patch List on the View
    data_envelopes = view.data_envelopes(mid_level)
    # To use alpha channel uncomment the below line
    # regions = view.request_regions(view_ranges, data_envelopes, True,
    #                                [0,0,0,0],pixel_engine.BufferType(1))
    regions = view.request_regions(view_ranges, data_envelopes, True, [0, 0, 0])  # Comment this
    # line for 'RGBA' enable
    # Employing worker threads to demonstrate parallel processing can be employed
    # as and when the patches are returned by the PixelEngine
    while len(regions) > 0:
        # This call returns the list of available patches
        # The SDK employs parallelism to prepare these patches (get Pixel data)
        # So one can also consume the available patches in parallel as they are made
        # available incrementally
        regions_ready = pixel_engine.wait_any(regions)
        for region in regions_ready:
            width, height = calculate_width_height(region.range, view)
            # For RGB, samples per pixel is 3 (#Channels)
            # For RGBA, samples per pixel is 4 (#Channels)
            pixel_buffer_size = width * height * 3
            pixels = np.empty(int(pixel_buffer_size), dtype=np.uint8)
            file_name = "{}_{}_data_envelope.png".format(image_name, str(increment))
            region.get(pixels)
            # remove the patch from the region list to ensure we are not duplicating read of
            # patches and the loop does terminate when all the patches are consumed.
            regions.remove(region)
            # Submitting to Job Thread for writing patches to disk
            write_image(pixels, width, height, file_name)
            increment += 1
    print("Data envelopes created")


if __name__ == "__main__":
    main()
