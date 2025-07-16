import os
import sys
from PIL import Image
import numpy as np
from sklearn.cluster import KMeans
import winreg
import json

class PixelGridConverter:
    def __init__(self, grid_width=100, grid_height=66, company_name="DefaultCompany", product_name="DrawPixels"):
        self.grid_width = grid_width
        self.grid_height = grid_height
        self.company_name = company_name
        self.product_name = product_name
        self.unity_registry_path = rf"SOFTWARE\Unity\UnityEditor\{company_name}\{product_name}"
        
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
    
    def extract_unique_colors(self, image):
        img_array = np.array(image)
        
        pixels = img_array.reshape(-1, 4)
        
        unique_pixels = np.unique(pixels, axis=0)
        
        palette = [tuple(color) for color in unique_pixels]
        
        return palette
    
    def create_color_texture(self, palette, texture_width=16):
        colors_per_row = texture_width
        texture_height = (len(palette) + colors_per_row - 1) // colors_per_row
        
        texture = Image.new('RGBA', (texture_width, texture_height), (0, 0, 0, 0))
        
        for i, color in enumerate(palette):
            x = i % colors_per_row
            y = i // colors_per_row
            texture.putpixel((x, y), color)
        
        return texture, texture_width, texture_height
    
    def find_exact_color_match(self, target_color, palette):
        try:
            return palette.index(target_color)
        except ValueError:
            return self.find_closest_color(target_color, palette)
        target = np.array(target_color)
        min_distance = float('inf')
        closest_index = 0
        
        for i, palette_color in enumerate(palette):
            distance = np.sqrt(np.sum((target - np.array(palette_color)) ** 2))
            if distance < min_distance:
                min_distance = distance
                closest_index = i
        
    def find_closest_color(self, target_color, palette):
        target = np.array(target_color)
        min_distance = float('inf')
        closest_index = 0
        
        for i, palette_color in enumerate(palette):
            distance = np.sqrt(np.sum((target - np.array(palette_color)) ** 2))
            if distance < min_distance:
                min_distance = distance
                closest_index = i
        
        return closest_index
    
    def convert_to_uv_coordinates(self, image, palette, texture_width, texture_height):
        img_array = np.array(image)
        uv_grid = []
        
        for y in range(self.grid_height):
            for x in range(self.grid_width):
                pixel_color = tuple(img_array[y, x])
                
                color_index = self.find_exact_color_match(pixel_color, palette)
                
                tex_x = color_index % texture_width
                tex_y = color_index // texture_width
                
                uv_x = tex_x / texture_width
                uv_y = tex_y / texture_height
                
                uv_grid.append(f"{uv_x}:{uv_y}")
        
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
        try:
            key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, self.unity_registry_path, 0, winreg.KEY_WRITE)
            
            binary_data = self.encode_unity_string(grid_data)
            
            winreg.SetValueEx(key, "flagGrid_h2263043443", 0, winreg.REG_BINARY, binary_data)
            
            winreg.CloseKey(key)
            print("Successfully saved to Unity registry!")
            return True
        except WindowsError as e:
            print(f"Failed to save to Unity registry: {e}")
    def save_to_unity_registry(self, grid_data):
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
            
            if preserve_colors:
                print("Extracting unique colors (preserving original image)")
                palette = self.extract_unique_colors(resized_image)
                print(f"Found {len(palette)} unique colors")
            else:
                print(f"Extracting color palette with clustering")
                palette = self.extract_color_palette(resized_image, max_colors)
                print(f"Reduced to {len(palette)} colors")
            
            print("Creating color texture")
            color_texture, tex_width, tex_height = self.create_color_texture(palette)
            
            print("Converting to UV coordinates")
            uv_grid = self.convert_to_uv_coordinates(resized_image, palette, tex_width, tex_height)
            
            print("Serializing grid data")
            grid_data = self.serialize_grid_data(uv_grid)
            
            color_texture.save("color_palette.png")
            print("Color palette saved as 'color_palette.png'")
            
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