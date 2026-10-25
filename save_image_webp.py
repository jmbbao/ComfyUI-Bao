# 
# Created with the help of Gemini IA
# Save Image Webp 📷️ v0.1
# 

import os
import torch
import json
import numpy as np
from PIL import Image
import folder_paths

class SaveImageWebp:
    def __init__(self):
        self.output_dir = folder_paths.get_output_directory()
        self.type = "output"

    @classmethod
    def INPUT_TYPES(s):
        return {
            "required": {
                "images": ("IMAGE", {"tooltip": 
                          "The image that will be saved"}),
                "filename": ("STRING", {"default": "ComfyUI", 
                            "tooltip": "Exact filename the image will have (without extension)"}),
                "folder": ("STRING", {"default": "", 
                          "tooltip": "Destination folder in /output (e.g.: /my_folder or my_folder)"}),
                "lossless": ("BOOLEAN", {"default": False, 
                            "tooltip": "If enabled, it uses lossless compression."}),
                "quality": ("INT", {"default": 85, "min": 0, "max": 100, "step": 1, 
                           "tooltip": "Compression (0 to 100, default 85)"}),
                "method": ("INT", {"default": 4, "min": 0, "max": 6, "step": 1, 
                          "tooltip": "Trade-off between encoding speed and compression efficiency (0 to 6, default 4)"}),
                "alpha_quality": ("INT", {"default": 100, "min": 0, "max": 100, "step": 1, 
                                 "tooltip": "Compression quality for the alpha channel/transparency (0 to 100, default 100)"}),
                "exact": ("BOOLEAN", {"default": False, 
                         "tooltip": "Preserve the RGB values ​​in transparent areas (false discards those values to get smaller file)"}),
                "save_json": ("BOOLEAN", {"default": False,
                             "tooltip": "Save workflow .json using same name"}),
            },
            "hidden": {"prompt": "PROMPT", "extra_pnginfo": "EXTRA_PNGINFO"},
        }

    RETURN_TYPES = ()
    FUNCTION = "save_images"
    OUTPUT_NODE = True
    CATEGORY = "image/save"

    def save_images(self, images, filename="ComfyUI", folder="", lossless=False, quality=85, method=4, alpha_quality=100, exact=False, save_json=False, prompt=None, extra_pnginfo=None):
        # Limpiar la ruta de la carpeta eliminando espacios y barras diagonales
        subfolder = folder.strip().strip("/\\")
        full_output_folder = os.path.join(self.output_dir, subfolder) if subfolder else self.output_dir
        
        # Crear la carpeta de destino solo si el nombre resultante no está vacío
        if subfolder:
            os.makedirs(full_output_folder, exist_ok=True)
        
        results = list()
        total_images = len(images)
        
        for batch_number, image in enumerate(images):
            i = 255. * image.cpu().numpy()
            img = Image.fromarray(np.clip(i, 0, 255).astype(np.uint8))
            
            # Definir el nombre base según el batch
            if total_images > 1:
                base_filename = f"{filename}_{batch_number}"
            else:
                base_filename = filename
                
            filename_with_ext = f"{base_filename}.webp"
            file = os.path.join(full_output_folder, filename_with_ext)
            
            # --- OPCIONAL: Evitar sobrescribir añadiendo un contador si ya existe ---
            counter = 1
            while os.path.exists(file):
                filename_with_ext = f"{base_filename}_{counter:05d}.webp"
                file = os.path.join(full_output_folder, filename_with_ext)
                counter += 1
            # ------------------------------------------------------------------------
            
            save_kwargs = {
                "lossless": lossless,
                "quality": quality,
                "method": method,
                "alpha_quality": alpha_quality,
                "exact": exact
            }
            
            img.save(file, "WEBP", **save_kwargs)
            
            # Guardar workflow en JSON con el mismo nombre que la imagen
            if save_json and extra_pnginfo is not None:
                json_file = os.path.splitext(file)[0] + ".json"

                workflow_data = extra_pnginfo.get("workflow", {})

                with open(json_file, "w", encoding="utf-8") as f:
                    json.dump(workflow_data, f, indent=2, ensure_ascii=False, default=str)
            
            results.append({
                "filename": filename_with_ext,
                "subfolder": subfolder,
                "type": self.type
            })

        return {"ui": {"images": results}}

