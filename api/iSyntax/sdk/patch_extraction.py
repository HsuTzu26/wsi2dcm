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
    "Path\\image.isyntax" 1 False "x_start,y_start,x_end,y_end" level
So to extract 3 patches , the arguments should be in order
   "Path\\image.isyntax" 3 True "x_start,y_start,x_end,y_end&x_start,
y_start,x_end,y_end&x_start,y_start,x_end,y_end" level
So to extract a region of interest (tiling) , the arguments should be in order
   "Path\\image.isyntax" -1 True "x_start,y_start,x_end,y_end,
tile_width,tile_height" level
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
import sys
import ast
import os
import shutil
import argparse
import traceback
from pixelengine import PixelEngine
from api.iSyntax.sdk.extract_pixel_data import extract_pixel_data
from api.iSyntax.sdk.backends import Backends


def create_folder(image_name):
    """
    Create folder with image name
    :param image_name: Name of the isyntax image given as input
    :return: creates folder with image name
    """
    if os.path.exists("." + os.path.sep + image_name):
        shutil.rmtree("." + os.path.sep + image_name)
    os.mkdir("." + os.path.sep + image_name)


def create_patch_list(num_y_tiles, num_x_tiles, tile_size, starting_indices, level):
    """
    Create patch(es) and patch identifier lists
    :param num_y_tiles: Number of tiles along y-axis
    :param num_x_tiles:number of tiles along x-axis
    :param tile_size: Tile size
    :param starting_indices: Starting co-ordinates
    :param level: Level
    :return: patch list and patch identifier list
    """
    patches = []
    # Spilt the Region of Interest into multiple Tiles i.e. Patches as
    # per the User Defined Patch Size
    y_spatial = 0
    # View Range is defined as a closed set i.e. the start and end index is inclusive
    # For example, for Tile size of 512, First Tile range is 0 to 511,
    # Next Tile Range is 512 to 1023 ...
    for y_counter in range(num_y_tiles):
        y_patch_start = starting_indices[1] + (y_counter * tile_size[1])
        y_patch_end = (y_patch_start + tile_size[1]) - (2 ** level)
        x_spatial = 0
        for x_counter in range(num_x_tiles):
            x_patch_start = starting_indices[0] + (x_counter * tile_size[0])
            x_patch_end = (x_patch_start + tile_size[0]) - (2 ** level)
            patch = [x_patch_start, x_patch_end, y_patch_start, y_patch_end, level]
            patches.append(patch)
            # Associating spatial information to the patchList in order to
            # identify the patches returned asynchronously
            x_spatial += 1
        y_spatial += 1

    return patches


# pylint: disable=too-many-arguments, too-many-locals
def tiles_extraction(dimensions, level, image_name, view, pixel_engine, async_yes_no):
    """
    Tiles Extraction
    :param dimensions: Given input dimensions
    :param level: Given input level
    :param image_name: Given image name
    :param view: Source view
    :param pixel_engine: Pixel engine Instance
    :param async_yes_no: Async True or False
    :return: None
    """
    x_start, x_end, y_start, y_end, tile_width, tile_height = tiles_extraction_calculations(
        dimensions, level)
    # Divide the ROI Width by patch Width to calculate the number of patches
    # in X direction
    num_x_tiles = int((x_end - x_start) / tile_width)
    # Divide the ROI Height by patch Width to calculate the number of patches in
    # Y direction
    num_y_tiles = int((y_end - y_start) / tile_height)
    print("Number of Tiles in X and Y directions " + str(num_x_tiles) + "," +
          str(num_y_tiles))
    # Uncomment to Pad with an extra patch to cover the ROI
    # As the ROI width and height may not be an integer multiple of the
    # patch width and height
    # We can either choose to drop some region of the ROI or cover a
    # slightly bigger region
    if ((x_end - x_start) % tile_width) > 0:
        num_x_tiles += 1
    if (y_end - y_start) % tile_height > 0:
        num_y_tiles += 1
    try:
        patches = create_patch_list(num_y_tiles, num_x_tiles,
                                    [tile_width, tile_height],
                                    [x_start, y_start], level)

        isyntax_file_name = image_name
        image_name = image_name + '_' + str(len(patches))
        create_folder(image_name)
        # Prepare request against the Patch List on the View
        data_envelopes = view.data_envelopes(level)
        # To use alpha channel uncomment the below line
        # regions = view.request_regions(view_ranges, data_envelopes, True, [0, 0, 0, 0],
        # pixel_engine.BufferType(1))
        print("Extracting Pixel Data please wait...")
        print("Requesting patches. Preparing patch definitions...")
        regions = view.request_regions(patches, data_envelopes, async_yes_no, [254, 254, 254])
        print("Request Complete. Patch definitions ready.")
        extract_pixel_data(view, regions, pixel_engine, image_name, isyntax_file_name)
    except RuntimeError:
        traceback.print_exc()


def tiles_extraction_calculations(dimensions, level):
    """
    Method for tile calculation
    :param dimensions: Co-ordinates
    :param level: Given level
    :return: co-ordinates
    """
    input_list = dimensions.split(',')
    if len(input_list) == 6: #pylint: disable=no-else-return
        # As the SDK employs parallel processing, the patches
        # returned won't be in order
        # So, associating X and Y spatial identity of the
        # patches through a separate list
        # Creating a list of the input argument
        x_start = int(input_list[0])
        y_start = int(input_list[1])
        x_end = int(input_list[2])
        y_end = int(input_list[3])
        # Getting patch size from user input
        tile_width = int(input_list[4])
        tile_height = int(input_list[5])
        print("Patch Start and End Indices at Level - " + str(level))
        # print("xStart, xEnd, yStart, yEnd, tileWidth, tileHeight")
        # print(x_start, x_end, y_start, y_end, tile_width, tile_height)
        return x_start, x_end, y_start, y_end, tile_width, tile_height

    else:
        print("Invalid Input")
        sys.exit()


# pylint: disable=too-many-arguments, too-many-locals
def patch_extraction(patch_input, level, num_levels, view,
                     pixel_engine, image_name, async_yes_no):
    """
    Patch extraction
    :param patch_input: Patch Co-ordinates
    :param level: Given input level
    :param num_levels: Maximum levels available in given isyntax image
    :param view: Source view
    :param view_ranges: Ranges of the patch to extarct
    :param pixel_engine: Pixel engine instance
    :param image_name: Given isyntax image name
    :param async_yes_no: Async True or False
    :return: None
    """
    view_ranges = []
    try:
        for patch in range(len(patch_input)): #pylint: disable=consider-using-enumerate
            input_list = patch_input[patch].split(',')
            if ((len(input_list)) == 4) and (level < num_levels):
                # Creating a list of the input argument
                x_start = int(input_list[0])
                y_start = int(input_list[1])
                x_end = int(input_list[2])
                y_end = int(input_list[3])
                print("Patch Start and End Indices at Level - " + str(level))
                print("xStart, xEnd, yStart, yEnd")
                print(x_start, x_end, y_start, y_end)
                # View Range is defined as a closed set i.e. the start and end index
                # is inclusive
                # For example, for patch size of 1024, it should be 0 to 1023
                view_range = [x_start, (x_end - (2 ** level)), y_start, (y_end - (2 ** level)),
                              level]
                view_ranges.append(view_range)
            else:
                print("Invalid Input")
                sys.exit()
        isyntax_file_name = image_name
        image_name = image_name + '_' + str(len(view_ranges))
        create_folder(image_name)
        # Prepare request against the Patch List on the View
        data_envelopes = view.data_envelopes(level)
        # To use alpha channel uncomment the below line
        # regions = view.request_regions(view_ranges, data_envelopes, True, [0, 0, 0, 0],
        # pixel_engine.BufferType(1))
        print("Extracting Pixel Data please wait...")
        print("Requesting patches. Preparing patch definitions...")
        regions = view.request_regions(view_ranges, data_envelopes, async_yes_no, [254, 254, 254])
        print("Request Complete. Patch definitions ready.")
        extract_pixel_data(view, regions, pixel_engine, image_name, isyntax_file_name)
    except RuntimeError:
        traceback.print_exc()


def main():  # pylint: disable=too-many-locals
    """
    Main
    :return: Extracts patch(es) and stores in a folder
    """
    parser = argparse.ArgumentParser(formatter_class=argparse.RawDescriptionHelpFormatter,
                                     description="""
Extracts single patch, multiple patches and tiles (user defined tile_size)
To execute this program pass the path of the iSynatx image file as command line argument.
Eg:
python patch_extraction.py "<PATH_OF_ISYNTAX_FILE>" <NO_OF_PATCHES> <ASYNC_TRUE_OR_FALSE> "<PATCH_CO-ORDINATES>" <LEVEL>
""")
    parser.add_argument("isyntax_image_path", help="isyntax image path")
    parser.add_argument("number_of_patches", help="number of patches")
    parser.add_argument("async_flag", help="asynchronous mode True or False")
    parser.add_argument("dimensions", help="<x_start,y_start,x_end,y_end>")
    parser.add_argument("level", help="Requested Resolution Level")
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
        # The default view is Source truncation view,
        # to query for source view one needs to disable
        # the default source truncation view as shown
        view = pe_input["WSI"].source_view
        # For SDK releases prior to 2.0, by default truncation is disabled irrespective of the
        # quality preset of the iSyntax file. This API allows to configure the truncation
        # level to control the output bit rate. By default truncation is enabled while reading
        # iSyntax files created with the quality preset of Q1 or Q2,
        # and is disabled for quality preset Q0
        truncation_level = {0 : [0, 0, 0]}
        view.truncation(False, False, truncation_level)
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

if __name__ == "__main__":
    main()
