import re
import os
import pydicom
import shutil
import traceback

from pixelengine import PixelEngine
from utils.Singleton import Singleton
from api.imgs2dcm import imgs2dcm
from api.imgfile_info import imgfile_info
from api.iSyntax.sdk.backends import Backends
from api.iSyntax.sdk.extract_pixel_data import extract_pixel_data
from api.iSyntax.sdk.patch_extraction import tiles_extraction_calculations, create_patch_list, create_folder



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
