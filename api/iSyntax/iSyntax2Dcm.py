from __future__ import absolute_import
import re
import os
import glob
import shutil
import traceback
from PySide6.QtCore import Signal
from api.imgfile_info import imgfile_info
from pixelengine import PixelEngine
from api.iSyntax.sdk.backends import Backends
from api.iSyntax.sdk.patch_extraction import tiles_extraction_calculations,create_patch_list,create_folder
from api.iSyntax.sdk.extract_pixel_data import extract_pixel_data
from api.imgs2dcm import imgs2dcm, parse_tag_file
from utils.Singleton import Singleton

"""
iSyntax2Dcm

將iSyntax的WSI轉換成DICOM WSI
需先安裝Philips Pathology SDK

"""

class iSyntax2Dcm(Singleton):


    # sdk的pixel engine，只能初始化一次並且需重複使用。
    pixel_engine:PixelEngine = None
    tile_size = [1024,1024]
    tmp_folder = ""
    def __init__(self):
        super().__init__()
        
        if self.pixel_engine == None:
            # 初始化sdk
            backends = Backends()

            # sdk要使用哪個圖形api解出png圖片
            #render_backend, render_context = backends.initialize_backend("SOFTWARE")
            render_backend, render_context = backends.initialize_backend("GLES2")
            #render_backend, render_context = backends.initialize_backend("GLES3")

            self.pixel_engine = PixelEngine(render_backend, render_context)

    def convert(self, file_info:imgfile_info, tmp_folder, update_signal:Signal):
        try:
            self.tmp_folder = tmp_folder
            input_file:str = file_info.input_file
            metadata_file:str = file_info.metadata_file
            output_file:str = file_info.output_filename
            raw_outputFolder = file_info.output_folder

            pe_input = self.pixel_engine["in"]
            image_name = os.path.splitext(os.path.basename(input_file))[0]
            pe_input.open(input_file)
            view = pe_input["WSI"].source_view

            # 0. 檢查圖片類型是否為"WSI"
            image_type = pe_input[0].image_type
            file_info.convert_status = f"圖片類型:{image_type}"
            #update_signal.emit(0)
            if image_type == "WSI":

                # 1. 取得原圖大小[x,y]
                # 參考isyntax_properties.py的
                # properties of WSI dimension 1 的 dimension_ranges 的第三個數值為 x大小
                # properties of WSI dimension 2 的 dimension_ranges 的第三個數值為 y大小
                raw_size = [view.dimension_ranges(0)[1][2],view.dimension_ranges(0)[0][2]] # 原始圖片的 x,y 大小
                print(str(view.dimension_ranges(0)))
                # 2. 產生分割後的圖片檔案
                # 使用及參考範例程式的patch_extraction_display_view.py
                for i in range(view.num_derived_levels,view.num_derived_levels-1,-1):
                    x_dimension_range = dict(zip(['first', 'increment', 'last'], (view.dimension_ranges(i)[0])))
                    y_dimension_range = dict(zip(['first', 'increment', 'last'], (view.dimension_ranges(i)[1])))
                    dimensions = [0,0,raw_size[0],raw_size[1],self.tile_size[0] * x_dimension_range['increment'],self.tile_size[1] * y_dimension_range['increment']] # x_start, y_start, x_end, y_end, tile_width, tile_height

                    if os.path.exists(tmp_folder):
                        shutil.rmtree(tmp_folder)
                    os.mkdir(tmp_folder)
                    file_info.convert_status = f"轉換圖片檔案為png"
                    #update_signal.emit(0)
                    image_folder_name = self.tiles_extraction(str(dimensions).replace("[","").replace("]",""), i, image_name, view, self.pixel_engine, False, file_info, update_signal)
                    self.rename_patches(image_folder_name)

                    # 3. 產生DICOM檔案
                    #if os.path.exists(output_folder):
                    #    shutil.rmtree(output_folder)

                    file_info.convert_status = f"轉換png圖片檔案為dcm"
                    #update_signal.emit(0)
                    file_info.output_folder = f"{raw_outputFolder}/{i}/"
                    os.makedirs(file_info.output_folder, exist_ok=True)
                    imgs2dcm(tmp_folder, file_info, "png", update_signal)
                    file_info.convert_status = f"已完成({output_file}_{i})"
                    #update_signal.emit(0)
                pass

                # 3.輸出label與macro圖
                for index in range(pe_input.num_images):
                    image_type = pe_input[index].image_type
                    if image_type != "WSI":
                        sub_image_data = pe_input[index].image_data
                        """
                        # One can change the file extension for writing
                        # other file formats as supported by Pillow
                        # e.g. ".jpg", ".png"...
                        """
                        #fname_wout_ext = isyntax_image_path[:isyntax_image_path.rfind('.')]
                        #sub_image_file = open(fname_wout_ext + '_' + image_type + ".jpg", "wb")
                        sub_image_file = open(f"{raw_outputFolder}/{image_type}.jpg", "wb")
                        sub_image_file.write(sub_image_data)
                        print(str(image_type)+" Successfully Generated.")
            
            pe_input.close()

            # 全數轉換完畢後刪除暫存檔
            shutil.rmtree(tmp_folder)
        except Exception as e:
            file_info.convert_status = f"轉換時發生錯誤:{e}"
            #update_signal.emit(0)

    # 將產生分割的圖片檔案改名(x,y對調)
    def rename_patches(self, folder_name):
        # 取得檔案名稱
        file_name_list = os.listdir(folder_name)
        file_replace_list = []

        # 產生修改後的名稱
        for i in range(0, len(file_name_list)):
            old_name_data = re.split(r'[._]',file_name_list[i])
            x_index = 0
            y_index = 0
            if(old_name_data[-5] != '0'):
                x_index = int(int(old_name_data[-5]) / self.tile_size[0])
            if(old_name_data[-6] != '0'):
                y_index = int(int(old_name_data[-6]) / self.tile_size[0])
            new_file_name = f"layer_{old_name_data[-2]}_region_{x_index}_{y_index}.png"
            file_replace_list.append([file_name_list[i],new_file_name])
        # 開始對照及修改
        for i in range(0, len(file_replace_list)):
            os.rename(os.path.join(folder_name, file_replace_list[i][0]), os.path.join(self.tmp_folder, file_replace_list[i][1]))

        shutil.rmtree(folder_name)

    # pylint: disable=too-many-arguments, too-many-locals
    def tiles_extraction(self, dimensions, level, image_name, view, pixel_engine, async_yes_no, file_info:imgfile_info, update_signal:Signal):
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
        # Divide the ROI Width by patch Width to calculate the number of patches in X direction
        num_x_tiles = int((x_end - x_start) / tile_width)
        # Divide the ROI Height by patch Width to calculate the number of patches in Y direction
        num_y_tiles = int((y_end - y_start) / tile_height)
        print("Number of Tiles in X and Y directions " + str(num_x_tiles) + "," + str(num_y_tiles))

        """
        # Uncomment to Pad with an extra patch to cover the ROI
        # As the ROI width and height may not be an integer multiple of the
        # patch width and height
        # We can either choose to drop some region of the ROI or cover a
        # slightly bigger region
        """
        if ((x_end - x_start) % tile_width) > 0:
            num_x_tiles += 1
        if (y_end - y_start) % tile_height > 0:
            num_y_tiles += 1
        try:
            #print(f'切成幾塊:{num_x_tiles},{num_y_tiles}')
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
            print(patches)
            regions = view.request_regions(patches, data_envelopes, async_yes_no, [254, 254, 254])
            print("Request Complete. Patch definitions ready.")
            extract_pixel_data(view, regions, pixel_engine, image_name, isyntax_file_name, file_info, update_signal)
            return image_name
        except RuntimeError:
            traceback.print_exc()
