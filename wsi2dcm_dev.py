import glob
import traceback
import os
import shutil
import re
import argparse
import time  # Import time module
from api.Openslide.Openslide2Dcm import Openslide2Dcm
from api.imgfile_info import imgfile_info
from api.convert_api_type import convert_api_type
from api.convert_mode_type import convert_mode_type
from api.imgs2dcm import parse_tag_file, imgs2dcm
from api.iSyntax.sdk.backends import Backends
from api.iSyntax.sdk.patch_extraction import tiles_extraction_calculations, create_patch_list, create_folder
from api.iSyntax.sdk.extract_pixel_data import extract_pixel_data
from pixelengine import PixelEngine
from utils.Singleton import Singleton
from utils.generateRandomStr import generate_random_string
import pydicom

class iSyntax2Dcm(Singleton):
    pixel_engine: PixelEngine = None
    tile_size = [1024, 1024]
    tmp_folder = "./temp/"

    def __init__(self):
        super().__init__()
        
        if self.pixel_engine is None:
            print("Initializing PixelEngine...")  # Debug information
            backends = Backends()
            render_backend, render_context = backends.initialize_backend("GLES2") #SOFTWARE
            self.pixel_engine = PixelEngine(render_backend, render_context)
        else:
            print("PixelEngine already initialized.")  # Debug information

    def convert(self, file_info: imgfile_info, tmp_folder):
        try:
            # Check if the file exists
            if not os.path.exists(file_info.input_file):
                raise FileNotFoundError(f"File not found: {file_info.input_file}")

            self.tmp_folder = tmp_folder
            input_file = file_info.input_file
            output_file = file_info.output_filename
            raw_outputFolder = file_info.output_folder

            pe_input = self.pixel_engine["in"]
            image_name = os.path.splitext(os.path.basename(input_file))[0]
            
            processing_file = image_name + os.path.splitext(input_file)[1]
            # Output file path to ensure the path is correct
            print(f"Processing file: {processing_file}")

            pe_input.open(input_file)
            view = pe_input["WSI"].source_view
            image_type = pe_input[0].image_type
            file_info.convert_status = f"Image Type: {image_type}"
            print(file_info.convert_status)

            if image_type == "WSI":
                raw_size = [view.dimension_ranges(0)[1][2], view.dimension_ranges(0)[0][2]]
                # for i in range(view.num_derived_levels, view.num_derived_levels-1, -1):
                for i in range(1, 0, -1):
                    x_dimension_range = dict(zip(['first', 'increment', 'last'], (view.dimension_ranges(i)[0])))
                    y_dimension_range = dict(zip(['first', 'increment', 'last'], (view.dimension_ranges(i)[1])))
                    dimensions = [0, 0, raw_size[0], raw_size[1], self.tile_size[0] * x_dimension_range['increment'], self.tile_size[1] * y_dimension_range['increment']]

                    if os.path.exists(tmp_folder):
                        shutil.rmtree(tmp_folder)
                    os.mkdir(tmp_folder)

                    ### Check for duplicate files ###
                    dcm_path = os.path.join(raw_outputFolder, str(i), output_file)
                    try:
                        # Check if file exists and is a valid DICOM file
                        dcm_file = pydicom.dcmread(dcm_path)
                        # If valid, return and do not convert this file
                        print('Duplicate file, skipping conversion')
                        print(dcm_path)
                        # shutil.rmtree(tmp_folder)
                        # pe_input.close()
                        continue 
                    except Exception as e:
                        # print(e)
                        # If not valid, continue
                        print(f"Corrupt file or file not exist, reconverting {dcm_path}")

                    file_info.convert_status = f"Converting image file to PNG"
                    # print(file_info.convert_status)
                    image_folder_name = self.tiles_extraction(str(dimensions).replace("[", "").replace("]", ""), i, image_name, view, self.pixel_engine, False, file_info)
                    self.rename_patches(image_folder_name)

                    file_info.convert_status = f"Converting PNG image files to DICOM"
                    # print(file_info.convert_status)
                    file_info.output_folder = f"{raw_outputFolder}/{i}/"
                    os.makedirs(file_info.output_folder, exist_ok=True)
                    imgs2dcm(tmp_folder, file_info, "png", print)
                    file_info.convert_status = f"Completed ({output_file}_{i})"
                    # print(file_info.convert_status)

                for index in range(pe_input.num_images):
                    image_type = pe_input[index].image_type
                    if image_type != "WSI":
                        sub_image_data = pe_input[index].image_data
                        sub_image_file = open(f"{raw_outputFolder}/{image_type}.jpg", "wb")
                        sub_image_file.write(sub_image_data)
                        print(f"{image_type} Successfully Generated.")

            pe_input.close()
            shutil.rmtree(tmp_folder)
        except Exception as e:
            file_info.convert_status = f"Error during conversion: {e}"
            print(file_info.convert_status)
            if os.path.exists(tmp_folder):
                shutil.rmtree(tmp_folder)

    def rename_patches(self, folder_name):
        file_name_list = os.listdir(folder_name)
        file_replace_list = []

        for i in range(len(file_name_list)):
            old_name_data = re.split(r'[._]', file_name_list[i])
            x_index = int(int(old_name_data[-5]) / self.tile_size[0]) if old_name_data[-5] != '0' else 0
            y_index = int(int(old_name_data[-6]) / self.tile_size[0]) if old_name_data[-6] != '0' else 0
            new_file_name = f"layer_{old_name_data[-2]}_region_{x_index}_{y_index}.png"
            file_replace_list.append([file_name_list[i], new_file_name])

        for i in range(len(file_replace_list)):
            os.rename(os.path.join(folder_name, file_replace_list[i][0]), os.path.join(self.tmp_folder, file_replace_list[i][1]))

        shutil.rmtree(folder_name)

    def tiles_extraction(self, dimensions, level, image_name, view, pixel_engine, async_yes_no, file_info: imgfile_info):
        x_start, x_end, y_start, y_end, tile_width, tile_height = tiles_extraction_calculations(dimensions, level)
        num_x_tiles = int((x_end - x_start) / tile_width)
        num_y_tiles = int((y_end - y_start) / tile_height)

        if (x_end - x_start) % tile_width > 0:
            num_x_tiles += 1
        if (y_end - y_start) % tile_height > 0:
            num_y_tiles += 1

        try:
            patches = create_patch_list(num_y_tiles, num_x_tiles, [tile_width, tile_height], [x_start, y_start], level)
            isyntax_file_name = image_name
            image_name = f"{image_name}_{len(patches)}"
            create_folder(image_name)

            data_envelopes = view.data_envelopes(level)
            regions = view.request_regions(patches, data_envelopes, async_yes_no, [254, 254, 254])
            extract_pixel_data(view, regions, pixel_engine, image_name, isyntax_file_name, file_info, print)
            return image_name
        except RuntimeError:
            traceback.print_exc()

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

def main():
    parser = argparse.ArgumentParser(description='WSI Converter')
    parser.add_argument('--source_path', required=True, help='Source path of the input files')
    parser.add_argument('--output_path', required=True, help='Output path for the converted files')
    parser.add_argument('--metadata_path', help='Path to metadata files if required')
    parser.add_argument('--convert_mode', choices=['single_file', 'folder', 'metadata'], required=True, help='Conversion mode')
    parser.add_argument('--convert_api', choices=['iSyntax', 'Openslide'], required=True, help='Conversion API')
    
    args = parser.parse_args()

    converter = wsi_converter()
    converter.source_path = args.source_path
    converter.output_path = args.output_path
    if args.metadata_path:
        converter.metadata_path = args.metadata_path

    converter.convert_mode = convert_mode_type[args.convert_mode]
    converter.convert_api = convert_api_type[args.convert_api]

    status = converter.check_valid()
    if status == "OK":
        converter.convert()
        print("All files have been converted")
    else:
        print(f"Conversion failed: {status}")

if __name__ == "__main__":
    main()

""" Openslide """
## python wsi2dcm_dev.py --source_path "D:\AUUFFC_data\_WSI\_ncku_wsi_nash\send1\batch_1" --output_path "D:\AUUFFC_data\_WSI\_ncku_wsi_nash\send1\output" --metadata_path "D:\AUUFFC_data\_WSI\_ncku_wsi_nash\send1\metadata" --convert_mode metadata --convert_api OpenSlide

""" iSyntax """
## python wsi2dcm_dev.py --source_path "D:\AUUFFC_data\_WSI\_vghtpe_wsi_nsclc\iSyntax" --output_path "D:\AUUFFC_data\_WSI\_vghtpe_wsi_nsclc\iSyntax\output" --metadata_path "D:\AUUFFC_data\_WSI\_vghtpe_wsi_nsclc\iSyntax\metadata" --convert_mode metadata --convert_api iSyntax