# 
# Created with the help of Gemini IA
# Chroma3D 🍿️ v0.1
# 

import torch
import torch.nn.functional as F

class Chroma3DNode:
    @classmethod
    def INPUT_TYPES(s):
        return {
            "required": {
                "image": ("IMAGE",),
                "chroma_hex": ("STRING", {"default": "#66B45E", 
                   "tooltip": "Chroma color in HEX format"}
                ),
                "radius_Transp_100": ("INT", {"default": 10, "min": 0, "max": 255, "step": 1,
                   "tooltip": "Full transparency radius, value 0 to 255.\n"
                              "Using RGB as xyz coordinates, a sphere of this radius around your color,\n"
                              "all colors inside this sphere will have maximum transparency."}
                ),
                "radius_Transp_0": ("INT", {"default": 90, "min": 0, "max": 255, "step": 1,
                   "tooltip": "Zero transparency radius, value 0 to 255.\n"
                              "Transparency decreases on exiting previous sphere and will be zero reaching this radius.\n"
                              "The node will ensure this radius being bigger than previous radius."}
                ),
                "spill": ("FLOAT", {"default": 1.7, "min": 0.0, "max": 1.7, "step": 0.1,
                   "tooltip": "Removal of chroma spill. Automatically bypassed if the chroma color is neutral (gray/white/black)."}
                ),
            }
        }

    RETURN_TYPES = ("IMAGE", "MASK")
    FUNCTION = "remove_chroma"
    CATEGORY = "image/chroma"
    DESCRIPTION = "Creates a mask for any chroma color with intelligent spill suppression."

    def remove_chroma(self, image, chroma_hex, radius_Transp_100, radius_Transp_0, spill):
        # image shape: [B, H, W, 3] (Range 0.0 - 1.0 in ComfyUI)

        # 1. Parsing HEX colors 0-255 and normalize to 0.0-1.0
        hex_clean = chroma_hex.strip().lstrip('#')
        if len(hex_clean) != 6:
            hex_clean = "66B45E" # Fallback default value if the HEX is invalid
            
        try:
            chroma_R = int(hex_clean[0:2], 16)
            chroma_G = int(hex_clean[2:4], 16)
            chroma_B = int(hex_clean[4:6], 16)
        except ValueError:
            chroma_R, chroma_G, chroma_B = 102, 180, 94

        # 1. Normalize the chroma color from a 0–255 range to a 0.0–1.0 scale.
        c_r = chroma_R / 255.0
        c_g = chroma_G / 255.0
        c_b = chroma_B / 255.0
        
        # 2. Normalize the radii to the same scale
        r100 = radius_Transp_100 / 255.0
        r0 = radius_Transp_0 / 255.0
        
        if r0 <= r100:
            r0 = r100 + 0.001 # Avoid division by zero

        # 3. Calculate the Euclidean distance in 3D RGB space
        diff_r = image[..., 0] - c_r
        diff_g = image[..., 1] - c_g
        diff_b = image[..., 2] - c_b
        
        dist = torch.sqrt(diff_r**2 + diff_g**2 + diff_b**2)
        
        # 4. Calculate the Alpha mask (transparency)
        # Distance <= r100 -> Alpha 0.0 (100% transparent / 0% opaque)
        # Distance >= r0   -> Alpha 1.0 (0% transparent / 100% opaque)
        # Between the two -> Smooth, gradual transition
        alpha = torch.clamp((dist - r100) / (r0 - r100), 0.0, 1.0)
        
        # 5. Intelligent Spill Correction
        img_r = image[..., 0].clone()
        img_g = image[..., 1].clone()
        img_b = image[..., 2].clone()
        
        # Check whether the chroma color is neutral (gray, white, or black)
        # Calculate difference between max and min channels of the chosen chroma.
        chroma_max = max(c_r, c_g, c_b)
        chroma_min = min(c_r, c_g, c_b)
        is_neutral = (chroma_max - chroma_min) < 0.05 # Threshold for classifying as gray
        
        if spill > 0 and not is_neutral:
            # If it has a dominant color (Green, Blue or Royal Red), we apply spill
            if chroma_G >= chroma_R and chroma_G >= chroma_B:
                max_other = torch.max(img_r, img_b)
                spill_mask = torch.clamp(img_g - max_other, 0.0, 1.0) * spill * alpha
                img_g = img_g - spill_mask
            elif chroma_B >= chroma_R and chroma_B >= chroma_G:
                max_other = torch.max(img_r, img_g)
                spill_mask = torch.clamp(img_b - max_other, 0.0, 1.0) * spill * alpha
                img_b = img_b - spill_mask
            else:
                max_other = torch.max(img_g, img_b)
                spill_mask = torch.clamp(img_r - max_other, 0.0, 1.0) * spill * alpha
                img_r = img_r - spill_mask

        # 6. Prepare output images
        # ComfyUI expects a standard 3 channel RGB image in the "IMAGE" type
        rgb_image = torch.stack([img_r, img_g, img_b], dim=-1)
        
        # Standard ComfyUI mask (White = Opaque, Black = Transparent)
        mask = 1.0 - alpha
        
        return (rgb_image, mask)

