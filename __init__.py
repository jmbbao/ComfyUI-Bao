# 
# Created with the help of Gemini IA
#

from .chroma_3D import Chroma3DNode
from .load_image_output_name import LoadImageOutputName
from .save_image_webp import SaveImageWebp
from .load_image_folder_output_names import LoadImageFolderOutputNames

NODE_CLASS_MAPPINGS = {
    "Chroma3DNode": Chroma3DNode,
    "LoadImageOutputName": LoadImageOutputName,
    "SaveImageWebp": SaveImageWebp,
    "LoadImageFolderOutputNames": LoadImageFolderOutputNames,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "Chroma3DNode": "Chroma3D 🍿️",
    "LoadImageOutputName": "Load Image & Output Name 📁",
    "SaveImageWebp": "Save Image Webp 📷️",
    "LoadImageFolderOutputNames": "Load Image Folder & Output Names 📁",
}

