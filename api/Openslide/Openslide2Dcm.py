import shutil
import json

from api.imgs2dcm import imgs2dcm
from utils.Singleton import Singleton
# 讀取 config.json 檔案
with open('config.json', 'r', encoding='utf-8') as config_file:
    config = json.load(config_file)
OPENSLIDE_PATH = config["OPENSLIDE_PATH"] + "\\bin"

import os
import gc
from PIL import Image
import numpy as np

if hasattr(os, 'add_dll_directory'):
    # Python >= 3.8 on Windows
    with os.add_dll_directory(OPENSLIDE_PATH):
        from openslide import OpenSlide
else:
    os.environ['PATH'] = OPENSLIDE_PATH + ";" + os.environ['PATH']
    from openslide import OpenSlide

from api.imgfile_info import imgfile_info
from PySide6.QtCore import Signal


class Openslide2Dcm(Singleton):
    
    split_blocks = 100
    tileSize = 1024
    tmp_folder = ""

    def convert(self, file_info:imgfile_info, tmp_folder, update_signal:Signal):
        try:
            self.tmp_folder = tmp_folder
            input_file:str = file_info.input_file

            slide = OpenSlide(input_file)

            raw_outputFolder = file_info.output_folder

            # 依序將每個level都轉換
            for i in range(slide.level_count - 1, 0, -1):
                # 取得level資訊
                #level_TileSize = int(self.tileSize // slide.level_downsamples[i])
                level_TileSize = self.tileSize
                print(f'downsample 0:{slide.level_downsamples[i]}, tile = {level_TileSize}')

                # 1. 圖片轉jpg
                file_info.convert_status = "讀取原始檔"
                #update_signal.emit(0)
                self.split_tiff_layers_to_jpg_files_slice(slide, self.tmp_folder, file_info, update_signal, i, level_TileSize)

                # 2. jpg轉dcm
                file_info.output_folder = f"{raw_outputFolder}/{i}/"
                os.makedirs(file_info.output_folder, exist_ok=True)
                imgs2dcm(self.tmp_folder, file_info, "bmp", update_signal)
            pass
            
            if 'macro' in slide.associated_images:
                macro_im = np.asarray(slide.associated_images['macro'])[:,:,:3]
                Image.fromarray(macro_im).save(f"{raw_outputFolder}/macro.jpeg")
            pass

            if 'label' in slide.associated_images:
                label_im = np.asarray(slide.associated_images['label'])[:,:,:3]
                Image.fromarray(label_im).save(f"{raw_outputFolder}/label.jpeg")
            pass

            slide.close()

            # 全數轉換完畢後刪除暫存檔
            shutil.rmtree(tmp_folder)

        except Exception as e:
            file_info.convert_status = f"轉換時發生錯誤:{e}"
            #update_signal.emit(0)


    def split_tiff_layers_to_jpg_files_slice(self, slide, output_folder, file_info:imgfile_info, update_signal:Signal, target_layer=0, block_size=512):
        """
        input_file: 輸入的TIFF檔案路徑。
        output_folder: 輸出JPG檔案的資料夾路徑。
        target_layer: 從TIFF檔案中提取的層索引。
        num_blocks: 將圖像分割成的方塊數量。
        """

        # 建立輸出資料夾
        os.makedirs(output_folder, exist_ok=True)

        # 刪除輸出資料夾底下的所有檔案
        file_list = os.listdir(output_folder)

        for file_name in file_list:
            file_path = os.path.join(output_folder, file_name)
            os.remove(file_path)
        pass

        # 獲取指定層的尺寸
        width, height = slide.level_dimensions[target_layer]
        print(f"全圖大小為:[{width}, {height}]")
        
        # 取得第0層的大小(位置用到)
        fwidth, fheight = slide.level_dimensions[0]
        print(f"第0層全圖大小為:[{fwidth}, {fheight}]")
        
        # 計算每個區塊的寬度和高度
        block_count = [max(int(width // block_size),1), max(int(height // block_size),1)]
        fblock_count =  [max(int(fwidth // self.tileSize),1), max(int(fheight // self.tileSize),1)]
        fblock_size = [int(self.tileSize * (fblock_count[0] / block_count[0])), int(self.tileSize * (fblock_count[1] / block_count[1]))]

        # 逐個區塊處理
        loaded_image_count = 0
        for j in range(block_count[1]):
            for i in range(block_count[0]):        
                loaded_image_count += 1
                file_info.convert_status = f"讀取圖檔為bmp({loaded_image_count}/{block_count[0]*block_count[1]})"
                update_signal.emit(0)

                # 計算當前區塊的位置和尺寸
                x_position = i * fblock_size[0]
                y_position = j * fblock_size[1]
                block_dimensions = (block_size, block_size)
                # 讀取對應於當前區塊的區域
                region = np.array(slide.read_region((x_position, y_position), target_layer, block_dimensions))
                
                # 將區域轉換為RGBA格式
                region_rgba = Image.fromarray(region, 'RGBA')
                
                # 如果輸出資料夾不存在，則創建之
                os.makedirs(output_folder, exist_ok=True)
                
                # 定義輸出檔案路徑
                output_file = os.path.join(output_folder, f"layer_{target_layer}_region_{j}_{i}.bmp")
                
                # 用白色填充透明部分
                region_rgba = self.fill_transparent_with_white(region_rgba)
                
                # 將區塊保存為JPG檔案
                region_rgba.save(output_file, "BMP")
                print(f"已保存區塊({j}, {i})至{output_file}")

                del region_rgba
                gc.collect()

            pass
        pass

        # 關閉病理切片圖像
        #slide.close()

    
    def fill_transparent_with_white(self, img):
        """
        使用白色填充RGBA圖片的透明部分。
        img: RGBA模式的PIL圖片對象。
        返回填充透明部分後的新PIL圖片對象。
        """

        # 創建白色背景圖片
        background = Image.new('RGBA', img.size, (255, 255, 255, 255))
        
        # 在白色背景上合成原始圖片
        new_img = Image.alpha_composite(background, img)
        
        # 轉換為RGB模式
        new_img = new_img.convert('RGB')
        
        return new_img
