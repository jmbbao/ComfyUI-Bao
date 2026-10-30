# 
# Created with the help of Gemini AI
# 
# Folder to Webp Converter 📁️ -> 📷️
# 

import os
import json
from PIL import Image
import folder_paths

class FolderToWebpConverter:
    def __init__(self):
        self.output_dir = folder_paths.get_output_directory()
        self.type = "output"

    @classmethod
    def IS_CHANGED(cls, **kwargs):
        return float("nan")

    @classmethod
    def INPUT_TYPES(s):
        return {
            "required": {
                "directory": ("STRING", {"default": "", 
                             "tooltip": "Absolute path to the folder containing the source images"}),
                "filename": ("STRING", {"default": "", 
                            "tooltip": "Overriding name for the images (let blank to use same name as the original)"}),
                "folder": ("STRING", {"default": "images2webp", 
                          "tooltip": "Destination subfolder in /output"}),
                "lossless": ("BOOLEAN", {"default": False, 
                            "tooltip": "If enabled, it uses lossless compression"}),
                "quality": ("INT", {"default": 85, "min": 0, "max": 100, "step": 1, 
                           "tooltip": "Compression (0 to 100, default 85)"}),
                "method": ("INT", {"default": 4, "min": 0, "max": 6, "step": 1, 
                          "tooltip": "Trade-off between encoding speed and compression (0 to 6, default 4)"}),
                "alpha_quality": ("INT", {"default": 100, "min": 0, "max": 100, "step": 1, 
                                 "tooltip": "Compression quality for the alpha channel (0 to 100, default 100)"}),
                "exact": ("BOOLEAN", {"default": False, 
                         "tooltip": "Preserve the RGB values ​​in transparent areas (false discards those values to get smaller file)"}),
                "save_json": ("BOOLEAN", {"default": True, 
                             "tooltip": "Save workflow (if exists) as .json using same name"}),
            },
        }

    RETURN_TYPES = ()
    FUNCTION = "convert_folder"
    OUTPUT_NODE = True
    CATEGORY = "image/processing"

    def convert_folder(self, directory, filename="", folder="images2webp", lossless=False, quality=85, method=4, alpha_quality=100, exact=False, save_json=True):
        
        # Validar directorio de origen
        if not directory or not os.path.exists(directory):
            raise ValueError(f"Source folder doesn't exist: {directory}")

        # Limpiar la ruta de la carpeta eliminando espacios y barras diagonales
        subfolder = folder.strip().strip("/\\")
        full_output_folder = os.path.join(self.output_dir, subfolder) if subfolder else self.output_dir
        
        # Crear la carpeta de destino solo si el nombre resultante no está vacío
        if subfolder:
            os.makedirs(full_output_folder, exist_ok=True)

        # Extensiones de imagen soportadas
        valid_extensions = (".png", ".jpg", ".jpeg", ".webp")
        
        # Buscar todas las imágenes en la carpeta
        files = sorted([f for f in os.listdir(directory) if f.lower().endswith(valid_extensions)])
        
        if not files:
            print(f"No compatible images found in source folder: {directory}")
            return {"ui": {"images": []}}

        results = list()

        for index, file_name in enumerate(files):
            input_path = os.path.join(directory, file_name)
            
            try:
                # Abrir imagen individualmente con PIL (mantiene proporción nativa)
                with Image.open(input_path) as img:
                    # Asegurar conversión a RGB/RGBA si es necesario
                    if img.mode not in ("RGB", "RGBA"):
                        img = img.convert("RGBA" if "A" in img.getbands() else "RGB")

                    # Definir nombre de salida
                    custom_name = filename.strip()

                    if custom_name:
                        # Nombre personalizado + contador de 5 cifras
                        base_name = f"{custom_name}_{index + 1:05d}"
                    else:
                        # Usar nombre original de la imagen
                        base_name = os.path.splitext(file_name)[0]

                    filename_with_ext = f"{base_name}.webp"
                    output_file_path = os.path.join(full_output_folder, filename_with_ext)

                    # Evitar sobrescribir si ya existe
                    #counter = 1
                    #while os.path.exists(output_file_path):
                    #    filename_with_ext = f"{base_name}_{counter:05d}.webp"
                    #    output_file_path = os.path.join(full_output_folder, filename_with_ext)
                    #    counter += 1

                    # Parámetros de guardado WebP
                    save_kwargs = {
                        "lossless": lossless,
                        "quality": quality,
                        "method": method,
                        "alpha_quality": alpha_quality,
                        "exact": exact
                    }

                    # Guardar imagen procesada
                    img.save(output_file_path, "WEBP", **save_kwargs)

                    # Guardar workflow en JSON si está activado y la imagen lo contiene en sus metadatos
                    if save_json:
                        workflow_raw = img.info.get("workflow") or img.info.get("prompt")
                        if workflow_raw:
                            json_file = os.path.splitext(output_file_path)[0] + ".json"
                            try:
                                if isinstance(workflow_raw, str):
                                    workflow_data = json.loads(workflow_raw)
                                else:
                                    workflow_data = workflow_raw

                                with open(json_file, "w", encoding="utf-8") as f:
                                    json.dump(workflow_data, f, indent=2, ensure_ascii=False, default=str)
                            except Exception as json_err:
                                print(f"Can't extract JSON from {file_name}: {json_err}")

                    results.append({
                        "filename": filename_with_ext,
                        "subfolder": subfolder,
                        "type": self.type
                    })
            except Exception as e:
                print(f"Error processing file {file_name}: {e}")

        return {"ui": {"images": results}}
