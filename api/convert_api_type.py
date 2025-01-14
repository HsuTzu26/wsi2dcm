from enum import Enum

class convert_api_type(Enum):
    iSyntax = 0,
    Openslide = 1
    pass

convert_api_type.iSyntax.ext_name = ["*.isyntax"]
convert_api_type.Openslide.ext_name = ["*.tiff","*.tif", "*.mrxs"]