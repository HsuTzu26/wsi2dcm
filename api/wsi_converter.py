import glob
import os

from api.Openslide.Openslide2Dcm import Openslide2Dcm
from api.imgfile_info import imgfile_info
from api.convert_api_type import convert_api_type
from api.convert_mode_type import convert_mode_type
from api.imgs2dcm import parse_tag_file
from api.iSyntax.iSyntax2Dcm import iSyntax2Dcm
from utils.generateRandomStr import generate_random_string

class wsi_converter():

    convert_mode: convert_mode_type = convert_mode_type.single_file
    convert_api: convert_api_type = convert_api_type.iSyntax

    tmp_folder:str = "./temp/"

    source_path: str = ''
    output_path: str = ''
    metadata_path: str = ''

    level:int = 4
    tile_size:int = 10000

    file_list: list = []

    def __init__(self) -> None:
        pass

    def check_vaild(self) -> str:
        """
        檢查是否可以開始轉換
        """
        if not os.path.exists(self.source_path):
            return "原始路徑不存在"
        if not os.path.exists(self.output_path) and not os.path.isdir(self.output_path):
            return "輸出路徑不存在"

        self.get_file_list()

        if len(self.file_list) <= 0:
            return "無符合條件的檔案"

        return "OK"
    
    def get_file_list(self):
        """
        根據所選路徑取得要轉換的所有原檔案
        """
        self.file_list.clear()
        if os.path.exists(self.source_path) and os.path.exists(self.output_path):
            if self.convert_mode == convert_mode_type.single_file: # 如果是轉換單一檔案
                if os.path.isfile(self.source_path):
                    filename, extension = os.path.splitext(os.path.basename(self.source_path))
                    if f"*{extension}" in self.convert_api.ext_name:
                        file_info = imgfile_info(self.source_path,self.metadata_path,f"{self.output_path}/{filename}", f"{filename}.dcm")
                        self.file_list.append(file_info)
                        
            elif self.convert_mode == convert_mode_type.folder: # 如果是轉換資料夾內所有檔案
                if os.path.isdir(self.source_path):
                    img_files = []
                    for ext in self.convert_api.ext_name:
                        img_files.extend(glob.glob(os.path.join(self.source_path, "**", ext), recursive=True))
                    for file_path in img_files:
                        filename, extension = os.path.splitext(os.path.basename(file_path))
                        file_info = imgfile_info(file_path,"",f"{self.output_path}/{filename}", f"{filename}.dcm")
                        self.file_list.append(file_info)

            elif self.convert_mode == convert_mode_type.metadata: # 如果是根據metadata資料夾尋找檔案
                if os.path.isdir(self.metadata_path) and os.path.isdir(self.source_path):
                    metadata_files = glob.glob(os.path.join(self.metadata_path, "**", '*.txt'), recursive=True)
                    img_files = []
                    for ext in self.convert_api.ext_name:
                        img_files.extend(glob.glob(os.path.join(self.source_path, "**", ext), recursive=True))
                    for metafile_path in metadata_files:
                        metadata_tags = parse_tag_file(metafile_path)
                        container_id = metadata_tags["Container Identifier"]
                        # 假設檔案名稱會包含一個Container Identifier，先暫定找到檔案名稱內包含這段Container Identifier的就是該檔案。  
                        for file_path in img_files:
                            if file_path.find(container_id) != -1:
                                filename, extension = os.path.splitext(os.path.basename(file_path))
                                file_info = imgfile_info(file_path,metafile_path,f"{self.output_path}/{filename}", f"{filename}.dcm")
                                self.file_list.append(file_info)
        return self.file_list

    def convert(self, file_info, update_signal):
        """
        開始進行轉換單個檔案
        """
        
        if self.convert_api == convert_api_type.iSyntax:
            iSyntax2Dcm()._instance.convert(file_info,self.tmp_folder + "/" + generate_random_string(8),update_signal)
            pass
        elif self.convert_api == convert_api_type.Openslide:
            Openslide2Dcm()._instance.convert(file_info,self.tmp_folder + "/" + generate_random_string(8),update_signal)
            pass
        pass

    def reset(self):
        self.source_path = ''
        self.output_path = ''
        self.metadata_path = ''

    pass
