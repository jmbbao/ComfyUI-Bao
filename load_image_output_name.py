# 
# Created with the help of Gemini IA
# Load Image & Output Name 📁 v0.1
# 

import os
import hashlib
import torch
import numpy as np
from PIL import Image, ImageOps, ImageSequence
import folder_paths

class LoadImageOutputName:
    @classmethod
    def INPUT_TYPES(s):
        input_dir = folder_paths.get_input_directory()
        files = [f for f in os.listdir(input_dir) if os.path.isfile(os.path.join(input_dir, f))]
        return {
            "required": {
                "image": (sorted(files), {"image_upload": True, 
                         "tooltip": "Image to load"})
            },
        }

    # Añadimos "STRING" a los tipos de salida para el filename
    RETURN_TYPES = ("IMAGE", "MASK", "STRING")
    RETURN_NAMES = ("IMAGE", "MASK", "filename")
    FUNCTION = "load_image"
    CATEGORY = "image"

    def load_image(self, image):
        image_path = folder_paths.get_annotated_filepath(image)
        
        # Extraer el nombre del fichero sin extensión (ej: "mi_foto.png" -> "mi_foto")
        base_filename = os.path.splitext(os.path.basename(image_path))[0]

        img = Image.open(image_path)
        
        output_images = []
        output_masks = []
        w, h = None, None

        for i in ImageSequence.Iterator(img):
            i = ImageOps.exif_transpose(i)
            if i.mode == 'I':
                i = i.point(lambda p: p * (1 / 255))
            image_rgb = i.convert("RGB")
            
            if w is None:
                w, h = image_rgb.size
            
            if image_rgb.size != (w, h):
                image_rgb = image_rgb.resize((w, h))
            
            image_np = np.array(image_rgb).astype(np.float32) / 255.0
            image_tensor = torch.from_numpy(image_np)[None,]
            
            # Gestionar canales de transparencia (máscara) si la imagen los tiene
            if 'A' in i.getbands():
                mask = np.array(i.getchannel('A')).astype(np.float32) / 255.0
                mask = 1.0 - torch.from_numpy(mask)
            else:
                mask = torch.zeros((h, w), dtype=torch.float32, device="cpu")
            
            output_images.append(image_tensor)
            output_masks.append(mask)

        if len(output_images) > 1:
            output_image = torch.cat(output_images, dim=0)
            output_mask = torch.cat(output_masks, dim=0)
        else:
            output_image = output_images[0]
            output_mask = output_masks[0]

        # Retornamos la imagen, la máscara y el nombre base extraído
        return (output_image, output_mask, base_filename)

    @classmethod
    def IS_CHANGED(s, image):
        image_path = folder_paths.get_annotated_filepath(image)
        m = hashlib.md5()
        with open(image_path, 'rb') as f:
            m.update(f.read())
        return m.hexdigest()

    @classmethod
    def VALIDATE_INPUTS(s, image):
        if not folder_paths.exists_annotated_filepath(image):
            return f"Invalid image file: {image}"
        return True

