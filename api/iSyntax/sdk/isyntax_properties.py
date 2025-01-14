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
Display properties of an iSyntax  file
The program demonstrates the properties of an iSyntax file.
The properties are structured in the following manner:
      -> Properties of image file : The common properties associated to the iSynatax file are
      displayed here.
      -> Properties of sub image : The specific properties associated to the sub image(WSI,
      LABEL,MACRO) are displayed here.
      -> View properties : View specific properties are only associated with WSI.
 To execute this program just pass the path of the iSynatx image file as command line argument.
 Eg:
       python isyntax_properties.py "<PATH_OF_ISYNTAX_FILE>"
"""

from __future__ import absolute_import
import argparse
from pixelengine import PixelEngine


def image_properties(pixel_engine):
    """
    Properties related to input file are used in this method
    :return: Number of images
    """
    pe_input = pixel_engine["in"]
    num_images = pe_input.num_images
    print("[common properties]")
    print("pixel engine version : " + pixel_engine.version)
    print("barcode : " + str(pe_input.barcode))
    print("acquisition_datetime : " + str(pe_input.acquisition_datetime))
    print("date_of_last_calibration : " + str(pe_input.date_of_last_calibration))
    print("time_of_last_calibration : " + str(pe_input.time_of_last_calibration))
    print("manufacturer : " + str(pe_input.manufacturer))
    print("model_name : " + str(pe_input.model_name))
    print("device_serial_number : " + str(pe_input.device_serial_number))
    if pe_input.derivation_description:
        print("derivation_description : " + pe_input.derivation_description)
    if pe_input.software_versions:
        print("software_versions : " + str(pe_input.software_versions))
    print("num_images : " + str(num_images))
    return num_images


def sub_image_properties(pixel_engine, num_images):
    """
    Properties related to sub images are used in this method
    :param pe: Pixel Engine used for open the file
    :param num_images: Number of images in isyntax file
    :return: None
    """
    pe_input = pixel_engine["in"]

    # Iterating over all sub images present in the file
    for image in range(num_images):
        image_dimension_names = pe_input[image].source_view.dimension_names
        image_type = pe_input[image].image_type
        print("\n[properties of sub image - " + image_type + "]")
        print("image_type : " + image_type)
        print("lossy_image_compression_method : " + pe_input[
            image].lossy_image_compression_method)
        try:
            print("lossy_image_compression_ratio : "
                  + str(pe_input[image].lossy_image_compression_ratio))
        except RuntimeError:
            pass
        print("dimension_names : " + str(image_dimension_names))
        if image_type == "WSI":
            print("wavelet : " + str(pe_input["WSI"].pixel_transform))
            print("quality_preset : "+pe_input[image_type].quality_preset)
            print("colorspace_transform : "+pe_input[image_type].colorspace_transform)
            print("block_size : " + str(pe_input[image_type].block_size()))
            print("num_tiles : " + str(pe_input[image_type].num_tiles))

        dimensions(image_dimension_names, pe_input[image].source_view, image_type)

        if image_type == "WSI":
            image_valid_data_envelopes = pe_input[image].source_view.data_envelopes(0).\
as_extreme_vertices_model()
            check_data_envelopes(image_valid_data_envelopes, image_dimension_names)
            view_properties(pe_input[image].source_view,
                            pe_input[image].source_view.num_derived_levels + 1,
                            image_valid_data_envelopes, image_dimension_names)


def dimensions(image_dimension_names, view, image_type):
    """
    Dimension properties related to sub image are used in this method
    :param image_dimension_names: Dimension Name
    :param view: Source View
    :param image_type: Type of Image(WSI, Label, Macro)
    :return: None
    """
    # Printing properties of all types of dimensions
    count = 0
    for dim in enumerate(image_dimension_names):
        print("\n[properties of " + str(image_type)+" dimension " + str(count)+"]")
        count = count+1
        print("dimension_names : " + image_dimension_names[dim[0]])
        print("dimension_types : " + view.dimension_types[dim[0]])
        print("scale : " + str(view.scale[dim[0]]))
        print("dimension_units : " + view.dimension_units[dim[0]])
        print("dimension_discrete_values : " + str(view.dimension_discrete_values[dim[0]]))
        if dim[0] < len(view.origin):
            print("origin : " + str(view.origin[dim[0]]))
        print("dimension_ranges : " + str(view.dimension_ranges(0)[dim[0]]))


def check_data_envelopes(image_valid_data_envelopes, image_dimension_names):
    """
    This method checks the valid data envelopes in the sub image
    :param image_valid_data_envelopes: Valid Data Envelopes in Image
    :param image_dimension_names: Image Dimension Names
    :return: None
    """
    if image_valid_data_envelopes:
        print("\n[data envelope]")
        print("Number of data envelopes : " + str(len(image_valid_data_envelopes)))
    count = 0
    # Printing all image valid data envelopes
    for envelope in image_valid_data_envelopes:
        print("data_envelope - " + str(count) + "["
              + ', '.join(map(lambda i: image_dimension_names[i], envelope[0]))
              + "]:" + str(envelope[1]))
        count += 1


def view_dimensions(view):
    """
    This method prints the dimensions of view
    :param view: Source View
    :return: None
    """
    print("dimensions : " + str(len(view.dimension_names)))
    count = 0
    # Printing properties of all types of views dimension
    for dim in range(len(view.dimension_names)):
        print("\n[view dimensions " + str(count)+"]")
        count = count+1
        print("dimension_name : " + view.dimension_names[dim])
        print("dimension_types : " + view.dimension_types[dim])
        print("scale : " + (str(view.scale[dim])))
        print("dimension_units : " + (str(view.dimension_units[dim])))
        print("dimension_discrete_values : " + (str(view.dimension_discrete_values[dim])))
        print("dimension_ranges : " + str(view.dimension_ranges(0)[dim]))


def view_envelope(view, levels, image_valid_data_envelopes, image_dimension_names):
    """
    This method prints the data envelopes in view
    :param view: Source View
    :param levels: Max Levels in isyntax files
    :param image_valid_data_envelopes: Valid Data Envelopes
    :param image_dimension_names: Image Dimension Names
    :return: None
    """
    # Printing view data envelopes at all levels
    print("Number of data envelopes : " + str(len(image_valid_data_envelopes)))
    for level in range(levels):
        print("\n[view envelopes at level - " + str(level) + "]")
        x_dimension_range = dict(zip(['first', 'increment', 'last'], (view.dimension_ranges(level)[
            0])))
        y_dimension_range = dict(zip(['first', 'increment', 'last'], (view.dimension_ranges(level)[
            1])))
        print("dimension_range_at_level : [" + str(x_dimension_range) + ", " + str(
            y_dimension_range)+", " + str(view.dimension_ranges(level)[2]) + "]")
        if view.data_envelopes(level):
            count = 0
            for envelope in view.data_envelopes(level).as_extreme_vertices_model():
                print("data_envelope - " + str(count) +
                      "[" + ', '.join(map(lambda i: image_dimension_names[i], envelope[0]))+"]:" +
                      str(envelope[1]))
                count = count + 1


def view_properties(view, levels, image_valid_data_envelopes, image_dimension_names):
    """
    This method prints the view properties of sub image
    :param view: Source View
    :param levels: Max Levels in isyntax file
    :param image_valid_data_envelopes: Image valid data envelopes
    :param image_dimension_names: Image Dimension Names
    :return: None
    """
    print("\n[view properties]")
    print("bits_allocated : " + str(view.bits_allocated))
    print("bits_stored : " + str(view.bits_stored))
    print("high_bit : " + str(view.high_bit))
    print("pixel_representation : " + str(view.pixel_representation))
    print("planar_configuration : " + str(view.planar_configuration))
    print("samples_per_pixel : " + str(view.samples_per_pixel))
    print("number_of_levels : " + (str(levels) if levels else "1"))
    view_dimensions(view)
    view_envelope(view, levels, image_valid_data_envelopes, image_dimension_names)


def main(input_file=''):
    """
    main method
    If the input_file is defined when the function is called, the command line arguments are ignored
    :return: None
    """
    # To use properties of isyntax file, initialization of pixel engine is necessary.
    pixel_engine = PixelEngine()
    # parse commandline
    # Get path of input file as command line argument if not defined on the function call
    if input_file == '':
        parser = argparse.ArgumentParser(formatter_class=argparse.RawDescriptionHelpFormatter,
                                         description="""
Display properties of an iSyntax  file
The program demonstrates the properties of an iSyntax file.
The properties are structured in the following manner:
      -> Properties of image file : The common properties associated to the iSynatax file are
      displayed here.
      -> Properties of sub image : The specific properties associated to the sub image(WSI,
      LABEL,MACRO) are displayed here.
      -> View properties : View specific properties are only associated with WSI.
 To execute this program just pass the path of the iSynatx image file as command line argument.
 Eg:
       python isyntax_properties.py "<PATH_OF_ISYNTAX_FILE>"
""")
        parser.add_argument("input")
        args = parser.parse_args()
        input_file = args.input
    # Passing the input file for processing into pixel engine
    pe_input = pixel_engine["in"]
    # For optimization/performance purpose one can choose to generate/use
    # .fic file by changing the second argument as shown below,
    # Eg:
    # pe["in"].open(isyntax_image_path, "caching-ficom")
    # Hence, when the same isyntax file is reopened with "caching-ficom";
    # for faster performance pixelengine queries the metadata
    # associated with that isyntax file from .fic file
    # (which was generated first time).
    # pe["in"].open(isyntax_image_path, "ficom")
    # If you use ficom conatiner .fic file will not be created
    pe_input.open(input_file)

    # image_properties() method return sub images and levels associated with sub image
    num_images = image_properties(pixel_engine)
    sub_image_properties(pixel_engine, num_images)

if __name__ == "__main__":
    main()
