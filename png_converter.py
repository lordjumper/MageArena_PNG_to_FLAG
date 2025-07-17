import os
import sys
from skimage import color
from PIL import Image
import numpy as np
import json

# Seperated them by color so we can read it better
pixel_color_map = {
    # Row 1
    "C17171": "0.0:0.31",    # Light red 
    "C5A877": "0.2:0.32",    # Light orange/tan 
    "B9B16E": "0.35:0.33",   # Light yellow/beige 
    "97C38F": "0.5:0.34",    # Light green
    "79BABA": "0.615:0.35",  # Light cyan 
    "93ABCC": "0.65:0.36",   # Light blue 
    "A96EBC": "0.8:0.37",    # Light purple 
    
    # Row 2 
    "C43232": "0.0:0.51",    # Medium red 
    "C7943C": "0.2:0.52",    # Medium orange 
    "C3B435": "0.35:0.53",   # Medium yellow 
    "60C34D": "0.5:0.54",    # Medium green 
    "3AC1C0": "0.615:0.55",  # Medium cyan 
    "5688CD": "0.65:0.56",   # Medium blue 
    "9C34BD": "0.8:0.37",    # Medium purple 
    
    # Row 3
    "C60000": "0.0:0.71",    # Dark red 
    "C67E00": "0.2:0.72",    # Dark orange 
    "C7B300": "0.35:0.73",   # Dark yellow 
    "21C600": "0.5:0.74",    # Dark green 
    "00C6C4": "0.615:0.75",  # Dark cyan 
    "0054C6": "0.65:0.76",   # Dark blue 
    "9200C1": "0.8:0.77",    # Dark purple 
    
    # Row 4 
    "6D0000": "0.0:0.81",    # Very dark red 
    "764C00": "0.2:0.82",    # Very dark orange 
    "7F7200": "0.35:0.83",   # Very dark yellow 
    "1A9700": "0.5:0.84",    # Very dark green 
    "007B79": "0.615:0.85",  # Very dark cyan
    "003E93": "0.65:0.86",   # Very dark blue
    "640084": "0.8:0.87",    # Very dark purple

    # Row 5
    "300000": "0.0:0.91",    # Darkest red 
    "462D00": "0.2:0.92",    # Darkest orange 
    "393300": "0.35:0.93",   # Darkest yellow
    "0B4100": "0.5:0.94",    # Darkest green 
    "003736": "0.615:0.95",  # Darkest cyan
    "001F4A": "0.65:0.96",   # Darkest blue 
    "38004A": "0.8:0.97",    # Darkest purple

    # Row 6
    "FFFFFF": "0.0:0.0",    # White (lightest)
    "DFDFDF": "0.2:0.0",    # Light gray
    "BEBEBE": "0.4:0.0",    # Medium light gray
    "A6A6A6": "0.6:0.0",    # Medium gray
    "7D7D7D": "0.8:0.0",    # Medium dark gray
    "464646": "0.9:0.0",    # Dark gray
    "000000": "1.0:0.0",    # Black (darkest)
}

def get_rgb(hex_str):
    return (int(hex_str[0:2], 16), int(hex_str[2:4], 16), int(hex_str[4:6], 16))

class PixelGridConverter:
    def __init__(self, grid_width=100, grid_height=66, company_name="jrsjams", product_name="MageArena"):
        self.grid_width = grid_width
        self.grid_height = grid_height
        self.company_name = company_name
        self.product_name = product_name
        self.unity_registry_path = rf"SOFTWARE\Unity\UnityEditor\{company_name}\{product_name}"

        self.pil_palette = []
        for color in pixel_color_map:
            rgb = get_rgb(color)
            self.pil_palette.append(rgb[0])
            self.pil_palette.append(rgb[1])
            self.pil_palette.append(rgb[2])

    def load_png_image(self, png_path):
        if not os.path.exists(png_path):
            raise FileNotFoundError(f"PNG file not found: {png_path}")
        
        try:
            image = Image.open(png_path)
            if image.mode != 'RGBA':
                image = image.convert('RGBA')
            return image
        except Exception as e:
            raise ValueError(f"Failed to load PNG image: {e}")
    
    def resize_image_to_grid(self, image):
        return image.resize((self.grid_width, self.grid_height), Image.NEAREST)

    def convert_to_uv_coordinates(self, image, preserve_colors):
        img_array = np.array(image)
        uv_grid = []
        
        palettized = Image.new('P', (16, 16))
        palettized.putpalette(self.pil_palette)
        image = image.convert("RGB").quantize(palette=palettized, dither=0) 
        px = image.convert("RGB").load()
        
        for x in range(0, image.width):
            for y in range(image.height -1, -1, -1):
                r, g, b = px[x, y]
                hex_code = f'{r:02x}{g:02x}{b:02x}'.upper()
                uv = pixel_color_map.get(hex_code)
                if uv == None:
                    raise ValueError(f"Faield to find UV for '{hex_code}'")
                
                uv_grid.append(uv)

        return uv_grid
    
    def serialize_grid_data(self, uv_grid):
        return ",".join(uv_grid)
    
    def encode_unity_string(self, data):
        utf8_bytes = data.encode('utf-8')
        length = len(utf8_bytes)
        
        binary_data = bytearray()
        binary_data.extend(length.to_bytes(4, byteorder='little'))
        binary_data.extend(utf8_bytes)
        
        return bytes(binary_data)
    
    def find_unity_registry_keys(self):
        import winreg

        try:
            base_key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"SOFTWARE\Unity\UnityEditor")
            companies = []
            
            i = 0
            while True:
                try:
                    company = winreg.EnumKey(base_key, i)
                    companies.append(company)
                    i += 1
                except WindowsError:
                    break
            
            winreg.CloseKey(base_key)
            
            print("Found Unity companies:")
            for company in companies:
                print(f"  - {company}")
                try:
                    company_key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, rf"SOFTWARE\Unity\UnityEditor\{company}")
                    j = 0
                    while True:
                        try:
                            product = winreg.EnumKey(company_key, j)
                            print(f"    - {product}")
                            j += 1
                        except WindowsError:
                            break
                    winreg.CloseKey(company_key)
                except WindowsError:
                    pass
            
            return companies
        except WindowsError:
            print("No Unity registry keys found")
            return []
    
    def save_to_unity_registry(self, grid_data):
        import winreg
        try:
            key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, self.unity_registry_path, 0, winreg.KEY_WRITE)
            
            binary_data = self.encode_unity_string(grid_data)
            
            winreg.SetValueEx(key, "flagGrid_h2263043443", 0, winreg.REG_BINARY, binary_data)
            
            winreg.CloseKey(key)
            print("Successfully saved to Unity registry!")
            return True
        except WindowsError as e:
            print(f"Failed to save to Unity registry: {e}")
            print("Try running with --find-registry to locate the correct path")
            return False
    
    def save_to_file(self, grid_data, output_path="pixel_grid_data.txt"):
        try:
            with open(output_path, 'w') as f:
                f.write(grid_data)
            print(f"Grid data saved to file: {output_path}")
            return True
        except Exception as e:
            print(f"Failed to save to file: {e}")
            return False
    
    def convert_png_to_pixel_grid(self, png_path, save_to_registry=True, save_to_file=True, 
                                 output_file="pixel_grid_data.txt", preserve_colors=True):
        try:
            print(f"Loading PNG image: {png_path}")
            image = self.load_png_image(png_path)
            
            print(f"Resizing image to {self.grid_width}x{self.grid_height}")
            resized_image = self.resize_image_to_grid(image)
                                    
            print("Converting to UV coordinates")
            uv_grid = self.convert_to_uv_coordinates(resized_image, preserve_colors)
            
            print("Serializing grid data")
            grid_data = self.serialize_grid_data(uv_grid)
            
            resized_image.save("resized_image.png")
            print("Resized image saved as 'resized_image.png'")
            
            success = False
            
            if save_to_registry and os.name == 'nt':
                success = self.save_to_unity_registry(grid_data)
            
            if save_to_file:
                file_success = self.save_to_file(grid_data, output_file)
                success = success or file_success
            
            if success:
                print("Conversion completed successfully!")
                print(f"Image will appear as a {self.grid_width}x{self.grid_height} pixel version of your original")
            else:
                print("Conversion completed but failed to save data!")
                
            return grid_data
            
        except Exception as e:
            print(f"Conversion failed: {e}")
            return None

def main():
    if len(sys.argv) < 2:
        print("Usage: python png_converter.py <png_file_path> [--no-registry] [--no-file] [--find-registry] [--use-clustering]")
        print("       python png_converter.py --find-registry  (to find Unity registry paths)")
        print("Example: python png_converter.py my_image.png")
        print("         python png_converter.py my_image.png --use-clustering  (for too many colors)")
        sys.exit(1)
    
    if sys.argv[1] == "--find-registry":
        converter = PixelGridConverter()
        converter.find_unity_registry_keys()
        sys.exit(0)
    
    png_path = sys.argv[1]
    save_to_registry = True
    save_to_file = True
    preserve_colors = True
    
    for i, arg in enumerate(sys.argv[2:], 2):
        if arg == "--no-registry":
            save_to_registry = False
        elif arg == "--no-file":
            save_to_file = False
        elif arg == "--find-registry":
            converter = PixelGridConverter()
            converter.find_unity_registry_keys()
            continue
        elif arg == "--use-clustering":
            preserve_colors = False
    
    converter = PixelGridConverter()
    result = converter.convert_png_to_pixel_grid(
        png_path, 
        save_to_registry=save_to_registry,
        save_to_file=save_to_file,
        preserve_colors=preserve_colors
    )
    
    if result:
        print("\nGrid data preview (first 200 characters):")
        print(result[:200] + "..." if len(result) > 200 else result)

if __name__ == "__main__":
    main()