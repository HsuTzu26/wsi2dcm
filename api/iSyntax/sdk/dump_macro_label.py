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
This sample code generates macro and label images in jpg format.
To execute this sample code ,
Command
    python dump_macro_label.py <isyntax_image_path>
Where,
      <isyntax_image_path> is the full path of the isyntax file
Hence the macro and label images associated with the isyntax file will
be generated in the same directory as that of iSyntax file as
LABELIMAGE.jpg and MACROIMAGE.jpg
For optimization/performance purpose one can choose to generate/use
.fic file by changing the second argument as shown below,
Eg:
pe["in"].open(isyntax_image_path, "caching-ficom")
Hence, when the same isyntax file is reopened with "caching-ficom";
for faster performance pixelengine queries the metadata
associated with that isyntax file from .fic file
(which was generated first time).
Dependencies:
    Pip modules: numpy
"""

from __future__ import absolute_import
import argparse
import traceback
from pixelengine import PixelEngine


def main():
    """
    Dump macro and label image associated with the isyntax file
    """
    try:
        # parse commandline
        parser = argparse.ArgumentParser(formatter_class=argparse.RawDescriptionHelpFormatter,
                                         description="""
This sample code generates macro and label images in jpg format.
To execute this sample code ,
Command
    python dump_macro_label.py <isyntax_image_path>
Where,
      <isyntax_image_path> is the full path of the isyntax file
Hence the macro and label images associated with the isyntax file will
be generated in the same directory as that of iSyntax file.
""")
        parser.add_argument("isyntax_image_path", help="isyntax_image_path")
        args = parser.parse_args()
        isyntax_image_path = args.isyntax_image_path
        print("Initializing PixelEngine, please wait...")
        pixel_engine = PixelEngine()
        # Use "ficom" container, if user does not want to create .fic cache file
        #pixel_engine["in"].open(isyntax_image_path, "ficom")
        pixel_engine["in"].open(isyntax_image_path)
        for index in range(pixel_engine["in"].num_images):
            image_type = pixel_engine["in"][index].image_type
            if image_type != "WSI":
                sub_image_data = pixel_engine["in"][index].image_data
                # One can change the file extension for writing
                # other file formats as supported by Pillow
                # e.g. ".jpg", ".png"...
                fname_wout_ext = isyntax_image_path[:isyntax_image_path.rfind('.')]
                sub_image_file = open(fname_wout_ext + '_' + image_type + ".jpg", "wb")
                sub_image_file.write(sub_image_data)
                print(str(image_type)+" Successfully Generated.")
    except RuntimeError:
        traceback.print_exc()


if __name__ == '__main__':
    main()
