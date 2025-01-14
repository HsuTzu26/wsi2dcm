import argparse

from api.convert_api_type import convert_api_type
from api.convert_mode_type import convert_mode_type
from wsi_converter import wsi_converter


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Convert WSI to DICOM WSI")
    parser.add_argument("-s", "--source", required=True, help='Source path of the input files')
    parser.add_argument("-o", "--output", required=True, help='Output path for the converted files')
    parser.add_argument("-m", "--metadata", help='Path to metadata files if required')
    parser.add_argument("-mode", "--convert_mode", choices=['single_file', 'folder', 'metadata'], required=True, help='Conversion mode')
    parser.add_argument("-api", "--convert_api", choices=['iSyntax', 'Openslide'], required=True, help='Conversion API')

    args = parser.parse_args()

    converter = wsi_converter()
    converter.source_path = args.source
    converter.output_path = args.output
    if args.metadata:
        converter.metadata_path = args.metadata

    converter.convert_mode = convert_mode_type[args.convert_mode]
    converter.convert_api = convert_api_type[args.convert_api]

    valid = converter.check_valid()
    if valid == "OK":
        converter.convert()
    else:
        print(valid)

"""
Openslide

python wsi2dcm.py -s "source_path" -o "output_path" -m "metadata_path" -mode metadata -api Openslide
python wsi2dcm.py -s "D:\AUUFFC_data\_WSI\_ncku_wsi_nash\send1\batch_1" -o "D:\AUUFFC_data\_WSI\_ncku_wsi_nash\send1\output" -m "D:\AUUFFC_data\_WSI\_ncku_wsi_nash\send1\metadata" -mode metadata -api Openslide

iSyntax

python wsi2dcm.py -s "source_path" -o "output_path" -m "metadata_path" -mode metadata -api iSyntax

"""
