import os
import glob
import time
import string
import random

from api.imgfile_info import imgfile_info
from api.convert_api_type import convert_api_type
from api.convert_mode_type import convert_mode_type
from api.imgs2dcm import parse_tag_file, generate_random_string

from iSyntax2Dcm import iSyntax2Dcm
from Openslide2Dcm import Openslide2Dcm

class wsi_converter:

    convert_mode: convert_mode_type = convert_mode_type.single_file
    convert_api: convert_api_type = convert_api_type.iSyntax
    tmp_folder: str = "./temp/"

    source_path: str = ''
    output_path: str = ''
    metadata_path: str = ''
    level: int = 4
    tile_size: int = 10000

    file_list: list = []

    def __init__(self) -> None:
        pass

    def check_valid(self) -> str:
        if not os.path.exists(self.source_path):
            return "Source path does not exist"
        if not os.path.exists(self.output_path) and not os.path.isdir(self.output_path):
            return "Output path does not exist"
        if self.convert_mode == convert_mode_type.metadata and not os.path.exists(self.metadata_path):
            return "Metadata path does not exist"
        self.get_file_list()
        if len(self.file_list) <= 0:
            return "No valid files found"
        return "OK"
    
    def get_file_list(self):
        self.file_list.clear()
        if os.path.exists(self.source_path) and os.path.exists(self.output_path):
            if self.convert_mode == convert_mode_type.single_file:
                if os.path.isfile(self.source_path):
                    filename, extension = os.path.splitext(os.path.basename(self.source_path))
                    if f"*{extension}" in self.convert_api.ext_name:
                        file_info = imgfile_info(self.source_path, self.metadata_path, f"{self.output_path}/{filename}", f"{filename}.dcm")
                        self.file_list.append(file_info)
            elif self.convert_mode == convert_mode_type.folder:
                if os.path.isdir(self.source_path):
                    img_files = []
                    for ext in self.convert_api.ext_name:
                        img_files.extend(glob.glob(os.path.join(self.source_path, "**", ext), recursive=True))
                    for file_path in img_files:
                        filename, extension = os.path.splitext(os.path.basename(file_path))
                        file_info = imgfile_info(file_path, "", f"{self.output_path}/{filename}", f"{filename}.dcm")
                        self.file_list.append(file_info)
            elif self.convert_mode == convert_mode_type.metadata:
                if os.path.isdir(self.metadata_path) and os.path.isdir(self.source_path):
                    metadata_files = glob.glob(os.path.join(self.metadata_path, "**", '*.txt'), recursive=True)
                    img_files = []
                    for ext in self.convert_api.ext_name:
                        img_files.extend(glob.glob(os.path.join(self.source_path, "**", ext), recursive=True))
                    for metafile_path in metadata_files:
                        metadata_tags = parse_tag_file(metafile_path)
                        container_id = metadata_tags["Container Identifier"]
                        for file_path in img_files:
                            if file_path.find(container_id) != -1:
                                filename, extension = os.path.splitext(os.path.basename(file_path))
                                file_info = imgfile_info(file_path, metafile_path, f"{self.output_path}/{filename}", f"{filename}.dcm")
                                self.file_list.append(file_info)
        return self.file_list

    def convert(self):
        for file_info in self.file_list:
            start_time = time.time()  # Record start time for each image
            try:
                # print(f"Processing file: {file_info.input_file}")
                if self.convert_api == convert_api_type.iSyntax:
                    iSyntax2Dcm()._instance.convert(file_info, self.tmp_folder + "/" + generate_random_string(8))
                elif self.convert_api == convert_api_type.Openslide:
                    Openslide2Dcm()._instance.convert(file_info, self.tmp_folder + "/" + generate_random_string(8))
                print(f"File processing completed")
            except Exception as e:
                print(f"Error during file conversion: {e}, File path: {file_info.input_file}")

            end_time = time.time()  # Record end time for each image
            time_taken = end_time - start_time  # Calculate time difference for each image
            print(f"started at: {time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(start_time))}")
            print(f"ended at: {time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(end_time))}")
            print(f"Time taken: {time_taken:.2f} seconds")
            print("================================================")

    def reset(self):
        self.source_path = ''
        self.output_path = ''
        self.metadata_path = ''
