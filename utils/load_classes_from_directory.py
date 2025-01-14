import os
import importlib.util

def load_classes_from_directory(directory):
    """
    從一個資料夾底下讀取所有檔案內與檔案名稱相同的class
    """

    classes = {}
    for filename in os.listdir(directory):
        if filename.endswith('.py'):
            module_name = filename[:-3]  # 去掉副檔名
            module_path = os.path.join(directory, filename)
            spec = importlib.util.spec_from_file_location(module_name, module_path)
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            # 取得與檔名相同名稱的class
            #class_name = module_name.capitalize()  # 假设类名与文件名相同且首字母大写
            class_name = module_name  # 假設class名與檔名相同
            if hasattr(module, class_name) and callable(getattr(module, class_name)):
                classes[module_name] = getattr(module, class_name)
    return classes
