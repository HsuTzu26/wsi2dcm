class imgfile_info():
    """
    這是圖片檔案的相關資訊，原始檔、output路徑等...
    """

    input_file:str = ""
    metadata_file:str = ""
    convert_status:str = "尚未開始"
    output_folder:str = ""
    output_filename:str = ""

    def __init__(self, i_file, m_file, o_folder, o_filename) -> None:
        self.input_file = i_file
        self.metadata_file = m_file
        self.output_folder = o_folder
        self.output_filename = o_filename
        pass