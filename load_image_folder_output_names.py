# 
# Created with the help of Gemini IA
# Load Image Folder & Output Names 📁 v0.1
# 

import os
import hashlib
import torch
import numpy as np
from PIL import Image, ImageOps, ImageSequence
import folder_paths

class LoadImageFolderOutputNames:
    @classmethod
    def INPUT_TYPES(s):
        return {
            "required": {
                "directory": ("STRING", {
                    "default": "", 
                    "tooltip": "Folder path"
                }),
            },
            "optional": {
                "name_filter": ("STRING", {
                    "default": "", 
                    "tooltip": "Optional: loads only images with this text in the name"
                }),
                "image_load_limit": ("INT", {
                    "default": 0, 
                    "min": 0, 
                    "max": 10000, 
                    "tooltip": "Limit on number of images to load (0 = no limit)"
                }),
            }
        }

    # IMAGE y MASK se devuelven como batch (False en OUTPUT_IS_LIST), 
    # y filenames como una lista de strings (True en OUTPUT_IS_LIST)
    RETURN_TYPES = ("IMAGE", "MASK", "STRING")
    RETURN_NAMES = ("IMAGE", "MASK", "filenames")
    OUTPUT_IS_LIST = (True, True, True)
    FUNCTION = "load_images_from_dir"
    CATEGORY = "image"

    def load_images_from_dir(self, directory, name_filter="", image_load_limit=0):
        # Resolver la ruta de la carpeta (soporta relativas a 'input' o absolutas)
        if not os.path.isabs(directory):
            input_dir = folder_paths.get_input_directory()
            dir_path = os.path.join(input_dir, directory)
        else:
            dir_path = directory

        if not os.path.exists(dir_path):
            raise FileNotFoundError(f"The specified directory does not exist: {dir_path}")

        valid_extensions = ('.png', '.jpg', '.jpeg', '.webp')
        files = sorted([f for f in os.listdir(dir_path) if f.lower().endswith(valid_extensions)])
        
        if name_filter:
            files = [f for f in files if name_filter in f]

        if image_load_limit > 0:
            files = files[:image_load_limit]

        if not files:
            raise ValueError(f"No valid images were found in the directory: {dir_path}")

        output_images = []
        output_masks = []
        filenames = []

        w, h = None, None

        for file in files:
            image_path = os.path.join(dir_path, file)
            base_filename = os.path.splitext(file)[0]
            
            try:
                img = Image.open(image_path)
            except Exception as e:
                continue

            for i in ImageSequence.Iterator(img):
                i = ImageOps.exif_transpose(i)
                if i.mode == 'I':
                    i = i.point(lambda p: p * (1 / 255))
                image_rgb = i.convert("RGB")
                
                if w is None:
                    w, h = image_rgb.size
                
                # Normalize the size to match that of the first image in order to create the batch of tensors.
                if image_rgb.size != (w, h):
                    image_rgb = image_rgb.resize((w, h))
                
                image_np = np.array(image_rgb).astype(np.float32) / 255.0
                image_tensor = torch.from_numpy(image_np)[None,]
                
                # Manage transparency channel (mask), if present
                if 'A' in i.getbands():
                    mask = np.array(i.getchannel('A')).astype(np.float32) / 255.0
                    mask = 1.0 - torch.from_numpy(mask)
                else:
                    mask = torch.zeros((h, w), dtype=torch.float32, device="cpu")
                
                output_images.append(image_tensor)
                output_masks.append(mask)
                filenames.append(base_filename)
                break  # We only take the first frame if it is a standard static image.

        if len(output_images) == 0:
            raise ValueError("No images could be loaded from the folder.")

        return (output_images, output_masks, filenames)

    @classmethod
    def IS_CHANGED(s, directory, name_filter="", image_load_limit=0):
        if not os.path.isabs(directory):
            dir_path = os.path.join(folder_paths.get_input_directory(), directory)
        else:
            dir_path = directory
            
        if not os.path.exists(dir_path):
            return ""
            
        m = hashlib.md5()
        for f in sorted(os.listdir(dir_path)):
            if f.lower().endswith(('.png', '.jpg', '.jpeg', '.webp')):
                fp = os.path.join(dir_path, f)
                if os.path.isfile(fp):
                    m.update(f.encode('utf-8'))
                    m.update(str(os.path.getmtime(fp)).encode('utf-8'))
        return m.hexdigest()

    @classmethod
    def VALIDATE_INPUTS(s, directory, name_filter="", image_load_limit=0):
        if not directory:
            return "You must specify a directory."
        return True

