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
This is a common program to extract single patch, multiple patches
and tiles (user defined tile_size) extraction.
extract_pixel_data.py is the dependency file to execute this.
Thus, based on the operation nature(single/multipatch/tiles) the
input of command line depends.
Note: In multi patch operation, patches requested should be of same level.
Note: The output will be stored in 'image_name' folder. For every time
the contents of this folder will be overwritten if same image is used.
The common input are:
1 : Path of the iSyntax file
2 : Number of patches (if number of patches is -1 then tiling is performed)
3 : Asynchronous True/False (if True the operation will perform in async).
4 : Indices of Patch and Patches (if number of patches >=2 then
separate two patches by '&')
5 : Resolution Level
6 : (Optional Parameter) Backend options like SOFTWARE, GLES2
7 : Contrast clip limit (range: 1 to 4, for default value 1.2)
8 : Sharpness (range: 0 to 10, for default value 2 )
9 : Color Correction gamma (range: 1 to 5, for default value 2.4 )
10 : Color Correction black point (range: 0 to 1, for default value 0 )
11 : Color Correction white point (range: 0 to 1, for default value 1 )
12: Color Gain (range: 0 to 1.5, for default value 1 )
(To enable Backend as GLES2 use '-b "GLES2"' if not given default is "SOFTWARE")
Eg:
So to extract a single patch the arguments should be in order
    "Path\\image.isyntax" 1 False "x_start,y_start,x_end,y_end" level -c <CONTRAST_VALUE>
    -s <SHARPENING_VALUE> -g <GAMMA_VALUE> -bp <BLACK_POINT_VALUE> -wp <WHITE_POINT_VALUE>
So to extract 3 patches , the arguments should be in order
   "Path\\image.isyntax" 3 True "x_start,y_start,x_end,y_end&x_start,
   y_start,x_end,y_end&x_start,y_start,x_end,y_end" level -c <CONTRAST_VALUE>
   -s <SHARPENING_VALUE> -g <GAMMA_VALUE> -bp <BLACK_POINT_VALUE> -wp <WHITE_POINT_VALUE>
So to extract a region of interest (tiling) , the arguments should be in order
   "Path\\image.isyntax" -1 True "x_start,y_start,x_end,y_end,
   tile_width,tile_height" level -c <CONTRAST_VALUE> -s <SHARPENING_VALUE>
   -g <GAMMA_VALUE> -bp <BLACK_POINT_VALUE> -wp <WHITE_POINT_VALUE>
tile_width,tile_height i.e. patch size to divide the region of
interest into multiple patches.
Note : Since all indices are referred to level 0, thus tile_width
and  tile_height requested is also inferred at level 0.
    Thus, to extract patches at level 2 if the given input was
256 x 256 thus the output is generated as 64x64 (256/2^2).
    To obtain same resolution at that level, the input patch
size should be multiplied by 2^level.
    Eg: If you want to extract 256 x 256 tile at any level then
the tile_width and tile_height should be (256*2^level)x(256*2^level)
Dependencies:
 Pip modules: numpy, futures, pillow
"""

from __future__ import absolute_import
import ast
import os
import argparse
import traceback
from pixelengine import PixelEngine
from backends import Backends
from patch_extraction import tiles_extraction, patch_extraction

def main():
    """
    Main
    :return: Extracts patch(es) and stores in a folder
    """
    parser = argparse.ArgumentParser(formatter_class=argparse.RawDescriptionHelpFormatter,
                                     description="""
This is a common program to extract single patch, multiple patches
and tiles (user defined tile_size) extraction.
extract_pixel_data.py is the dependency file to execute this.
Thus, based on the operation nature(single/multipatch/tiles) the
input of command line depends.
Note: In multi patch operation, patches requested should be of same level.
Note: The output will be stored in 'image_name' folder. For every time
the contents of this folder will be overwritten if same image is used.
The common input are:
1 : Path of the iSyntax file
2 : Number of patches (if number of patches is -1 then tiling is performed)
3 : Asynchronous True/False (if True the operation will perform in async).
4 : Indices of Patch and Patches (if number of patches >=2 then
separate two patches by '&')
5 : Resolution Level
6 : (Optional Parameter) Backend options like SOFTWARE, GLES2
7 : Contrast clip limit (range: 1 to 4, for default value 1.2)
8 : Sharpness (range: 0 to 10, for default value 2 )
9 : Color Correction gamma (range: 1 to 5, for default value 2.4 )
10 : Color Correction black point (range: 0 to 1, for default value 0 )
11 : Color Correction white point (range: 0 to 1, for default value 1 )
12: Color Gain (range: 0 to 1.5, for default value 1 )
(To enable Backend as GLES2 use '-b "GLES2"' if not given default is "SOFTWARE")
Eg:
So to extract a single patch the arguments should be in order
    "Path\\image.isyntax" 1 False "x_start,y_start,x_end,y_end" level -c <CONTRAST_VALUE>
    -s <SHARPENING_VALUE> -g <GAMMA_VALUE> -bp <BLACK_POINT_VALUE> -wp <WHITE_POINT_VALUE>
So to extract 3 patches , the arguments should be in order
   "Path\\image.isyntax" 3 True "x_start,y_start,x_end,y_end&x_start,
   y_start,x_end,y_end&x_start,y_start,x_end,y_end" level -c <CONTRAST_VALUE>
   -s <SHARPENING_VALUE> -g <GAMMA_VALUE> -bp <BLACK_POINT_VALUE> -wp <WHITE_POINT_VALUE>
So to extract a region of interest (tiling) , the arguments should be in order
   "Path\\image.isyntax" -1 True "x_start,y_start,x_end,y_end,
   tile_width,tile_height" level -c <CONTRAST_VALUE> -s <SHARPENING_VALUE>
   -g <GAMMA_VALUE> -bp <BLACK_POINT_VALUE> -wp <WHITE_POINT_VALUE>
tile_width,tile_height i.e. patch size to divide the region of
interest into multiple patches.
Note : Since all indices are referred to level 0, thus tile_width
and  tile_height requested is also inferred at level 0.
    Thus, to extract patches at level 2 if the given input was
256 x 256 thus the output is generated as 64x64 (256/2^2).
    To obtain same resolution at that level, the input patch
size should be multiplied by 2^level.
    Eg: If you want to extract 256 x 256 tile at any level then
the tile_width and tile_height should be (256*2^level)x(256*2^level)
Dependencies:
 Pip modules: numpy, futures, pillow
""")
    parser.add_argument("isyntax_image_path", help="isyntax image path")
    parser.add_argument("number_of_patches", help="number of patches")
    parser.add_argument("async_flag", help="async")
    parser.add_argument("dimensions", help="<x_start,y_start,x_end,y_end>")
    parser.add_argument("level", help="Requested Resolution Level")
    parser.add_argument("-c", "--contrast_clip_limit", \
                            help="Contrast clip limit, Ranges from 1 to 4")
    parser.add_argument("-s", "--sharpness", \
                            help="Sharpness, Ranges from 0 to 10")
    parser.add_argument("-g", "--color_correction_gamma", \
                            help="Color correction Gamma, Ranges from 1 to 5")
    parser.add_argument("-bp", "--color_correction_black_point", \
                            help="Color correction black point, Ranges from 0 to 1")
    parser.add_argument("-wp", "--color_correction_white_point", \
                            help="Color correction white point, Ranges from 0 to 1")
    parser.add_argument("-cg", "--color_gain", \
                        help="Color Gain, Ranges from 0 to 1.5")
    parser.add_argument("-b", "--backend",
                        choices=["SOFTWARE", "GLES2", "GLES3"], nargs='?',
                        default='SOFTWARE', help="select renderbackend")

    args = parser.parse_args()

    # Initiate pixel engine object through render backend and render context
    # Using CPU/GPU rendering options (eg. GLES2) - binding software context and backend
    backends = Backends()
    render_backend, render_context = backends.initialize_backend(args.backend)
    pixel_engine = PixelEngine(render_backend, render_context)
    pe_input = pixel_engine["in"]
    try:
        input_file = args.isyntax_image_path
        image_name = os.path.splitext(os.path.basename(input_file))[0]
        pe_input.open(input_file)
        #Initializing display view object
        view = pe_input["WSI"].display_view
        validate_and_apply_displayview_parameters(args, view, pe_input["WSI"].source_view.bits_stored)
        # Querying number of derived levels in an iSyntax file
        num_levels = view.num_derived_levels + 1
        dimensions = args.dimensions
        level = int(args.level)
        patches_count = int(args.number_of_patches)
        async_yes_no = args.async_flag
        async_yes_no = ast.literal_eval(async_yes_no)
        patch_input = dimensions.split('&')
        if len(patch_input) == patches_count:
            patch_extraction(patch_input, level, num_levels, view,
                             pixel_engine, image_name, async_yes_no)
        elif patches_count == -1:
            tiles_extraction(dimensions, level, image_name, view, pixel_engine, async_yes_no)
        else:
            print("Patch(es) requested doesn't match with input")
        pe_input.close()
    except RuntimeError:
        traceback.print_exc()

def  validate_and_apply_displayview_parameters(args, view, bits_stored):
    """
    Validate the user input display view parameters
    :args: Argument parser
    :view: Display view object
    :bits_stored: Getting bits stored for the source view
    :return: None
    """
    view.load_default_parameters()
    
    if(validatewithrange(args.contrast_clip_limit, 1, 4)):
        view.contrast_clip_limit = float(args.contrast_clip_limit)
    
    if(validatewithrange(args.sharpness, 0, 10)):
        view.sharpness = float(args.sharpness)

    if(validatewithrange(args.color_correction_gamma, 1, 5)):
        view.color_correction_gamma = float(args.color_correction_gamma)

    if(validatewithrange(args.color_correction_black_point, 0, 1)):
        view.color_correction_black_point = float(args.color_correction_black_point)
    
    if(validatewithrange(args.color_correction_white_point, 0, 1)):
        view.color_correction_white_point = float(args.color_correction_white_point)
    
    if(validatewithrange(args.color_gain, 0, 1.5)):
        view.color_gain = float(args.color_gain)
    
    print("Applying Display View Filters :")
    # For SGS files the default value for sharpness should be 4 and color_gain filter should be
    # applied with value 1 instead of contrast_clip_limit.
    if bits_stored == 8:
        print("Contrast Clip Limit : {}".format(view.contrast_clip_limit))
    else:
        print("Color Gain : {}".format(view.color_gain))

    print("Color Correction Gamma : {}".format(view.color_correction_gamma))
    print("Color Correction WhitePoint : {}".format(view.color_correction_white_point))
    print("Color Correction BlackPoint : {}".format(view.color_correction_black_point))
    print("Sharpness : {}".format(view.sharpness))

def validatewithrange(value, lowerbound, upperbound):
    if not (value == None) and (lowerbound <= float(value) <= upperbound):
        return True
    else:
        return False

if __name__ == "__main__":
    main()
