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
(To enable Backend as GLES2 use '-b "GLES2"' if not given default is "SOFTWARE")
Eg:
So to extract a single patch the arguments should be in order
    -u <USER_NAME> -p <PASSWORD> -hname <HOSTNAME> -sop <SOP_Instance_UID> 1
    False "x_start,y_start,x_end,y_end" level
So to extract 3 patches , the arguments should be in order
    -u <USER_NAME> -p <PASSWORD> -hname <HOSTNAME> -sop <SOP_Instance_UID> 3
    True "x_start,y_start,x_end,y_end&x_start, y_start,x_end,y_end&
    x_start,y_start,x_end,y_end" level
So to extract a region of interest (tiling) , the arguments should be in order
   -u <USER_NAME> -p <PASSWORD> -hname <HOSTNAME> -sop <SOP_Instance_UID> -1
    True "x_start,y_start,x_end,y_end, tile_width,tile_height" level
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
import traceback
import argparse
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
Extracts single patch, multiple patches and tiles (user defined tile_size) by Using ims protocol
To execute this program username, password, hostname, SOP Instance UID, and certificate path as command line argument.
Eg:
python patch_extraction_ims_streaming.py -u <USERNAME> -p <PASSWORD> -hname <HOSTNAME> -sop <SOP_INSTANCE_UID>
-cert <CERTIFICATE_PATH> <NO_OF_PATCHES> <ASYNC_TRUE_OR_FALSE> "<PATCH_CO-ORDINATES>" <LEVEL>
""")
    parser.add_argument("-u", "--username", help="username")
    parser.add_argument("-p", "--password", help="password")
    parser.add_argument("-hname", "--hostname", help="hostname")
    parser.add_argument("-sop", "--sop_instance_uid", help="SOP Instance UID of image")
    parser.add_argument("-cert", "--certificate_path", help="Certificate path")
    parser.add_argument("number_of_patches", help="number of patches")
    parser.add_argument("async_flag", help="asynchronous mode True or False")
    parser.add_argument("dimensions", help="<x_start,y_start,x_end,y_end>")
    parser.add_argument("level", help="Requested Resolution Level")
    parser.add_argument("-b", "--backend",
                        choices=["SOFTWARE", "GLES2", "GLES3"], nargs='?',
                        default='SOFTWARE', help="select renderbackend")
    args = parser.parse_args()

    isyntax_image_path = "ims://{}:{}@{}/TileService/{}".format(args.username,
                                                                args.password,
                                                                args.hostname,
                                                                args.sop_instance_uid)
    # Initiate pixel engine object through render backend and render context
    # Using CPU/GPU rendering options (eg. GLES2) - binding software context and backend
    backends = Backends()
    render_backend, render_context = backends.initialize_backend(args.backend)
    pixel_engine = PixelEngine(render_backend, render_context)
    pixel_engine.certificates = args.certificate_path
    pe_input = pixel_engine["in"]
    try:
        pe_input.open(isyntax_image_path)
        # Initializing source view object i.e. the view which provided raw pixel data
        view = pe_input["WSI"].source_view
        # To query for raw pixel data (source view), the truncation level should be disabled.
        truncationlevel = {0 : [0, 0, 0]}
        view.truncation(False, False, truncationlevel)
        if view.bits_stored == 9:
            # As SGS generates 9bit raw images(i2syntax / isyntax)
            # Converting this 9-bit pixel data to 8-bit pixel data to render in 8-bit display monitor.
            # Also making this data UFS equivalent by applying ICC Profile matrix
            # Note: ICC profile depends on the scanner
            view = view.add_user_view()
            matrix_filter = view.add_filter("3x3Matrix16")
            icc_matrix = pe_input["WSI"].icc_matrix
            view.filter_parameter_matrix3x3(matrix_filter, "matrix3x3", icc_matrix)
            view.add_filter("Linear16ToSRGB8")
        # Getting number of levels of the iSyntax file
        num_levels = view.num_derived_levels + 1
        dimensions = args.dimensions
        level = int(args.level)
        patches_count = int(args.number_of_patches)
        async_yes_no = args.async_flag
        async_yes_no = ast.literal_eval(async_yes_no)
        patch_input = dimensions.split('&')
        if len(patch_input) == patches_count:
            patch_extraction(patch_input, level, num_levels, view,
                            pixel_engine, args.sop_instance_uid, async_yes_no)
        elif patches_count == -1:
            tiles_extraction(dimensions, level, args.sop_instance_uid, view, pixel_engine, async_yes_no)
        else:
            print("Patch(es) requested doesn't match with input")
        pe_input.close()
    except RuntimeError:
        traceback.print_exc()


if __name__ == "__main__":
    main()
