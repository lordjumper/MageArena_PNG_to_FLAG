import os
import sys
from skimage import color
from PIL import Image
import numpy as np
import json

pixel_color_map = {
    "C17171": "0.6539685:0.2339683",
    "C5A877": "0.5047622:0.2307937",
    "B9B16E": "0.3746034:0.2466667",
    "97C38F": "0.2031748:0.2593651",
    "79BABA": "0.06984138:0.2561905",
    "93ABCC": "0.9238097:0.3673016",
    "A96EBC": "0.7841271:0.2688888",
    "C43232": "0.6317463:0.3990476",
    "C7943C": "0.5047622:0.3895238",
    "C3B435": "0.346032:0.4053969",
    "60C34D": "0.2158732:0.4434921",
    "3AC1C0": "0.120635:0.4117461",
    "5688CD": "0.9555559:0.6244445",
    "9C34BD": "0.7777779:0.58",
    "C60000": "0.6920638:0.5768254",
    "C67E00": "0.4952383:0.6117461",
    "C7B300": "0.3396828:0.5895239",
    "21C600": "0.1714289:0.5990477",
    "00C6C4": "0.07619071:0.58",
    "0054C6": "0.9428573:0.7514286",
    "9200C1": "0.8222224:0.7704761",
    "6D0000": "0.6285716:0.7482539",
    "764C00": "0.4857144:0.7577777",
    "7F7200": "0.3746034:0.7704761",
    "1A9700": "0.2000002:0.7482539",
    "007B79": "0.07619071:0.7387301",
    "003E93": "0.9238097:0.9165078",
    "640084": "0.8000001:0.9069841",
    "300000": "0.657143:0.9292063",
    "462D00": "0.520635:0.9419048",
    "393300": "0.3682542:0.8974603",
    "0B4100": "0.2253971:0.9355555",
    "003736": "0.06349218:0.9800001",
    "001F4A": "0.9365081:0.1133333",
    "38004A": "0.7841271:0.100635",
    "FFFFFF": "0.5968254:0.09428576",
    "DFDFDF": "0.4857144:0.08158734",
    "BEBEBE": "0.3428572:0.1069841",
    "A6A6A6": "0.2158732:0.1165079",
    "7D7D7D": "0.08888912:0.100635",
    "464646": "0.904762:0.2434921",
    "000000": "0.7809526:0.2561905",
}

class PixelGridConverter:
    def __init__(self, grid_width=100, grid_height=66, company_name="DefaultCompany", product_name="DrawPixels"):
        self.grid_width = grid_width
        self.grid_height = grid_height
        self.company_name = company_name
        self.product_name = product_name
        self.unity_registry_path = rf"SOFTWARE\Unity\UnityEditor\{company_name}\{product_name}"

        self.palette_lab = {}
        for hex_key in pixel_color_map.keys():
            r = int(hex_key[0:2], 16) / 255.0
            g = int(hex_key[2:4], 16) / 255.0
            b = int(hex_key[4:6], 16) / 255.0
            rgb = np.array([[[r, g, b]]])  # shape (1,1,3)
            lab = color.rgb2lab(rgb)[0][0] # shape (3,)
            self.palette_lab[hex_key] = lab
        
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
        
    def find_closest_color(self, target_color):
        r, g, b, a = target_color
        if a < 255: return ("e2dfe0", pixel_color_map.get("e2dfe0", "0.9746034:0.9419048"))
        
        rgb = np.array([[[r/255.0, g/255.0, b/255.0]]])
        target_lab = color.rgb2lab(rgb)[0][0]

        min_distance = float('inf')
        closest_key = None

        for hex_key, lab in self.palette_lab.items():
            dist = np.linalg.norm(target_lab - lab)
            if dist < min_distance:
                min_distance = dist
                closest_key = hex_key

        if closest_key is None:
            raise ValueError(f"No closest color found for {target_color}")

        return (closest_key, pixel_color_map[closest_key])

    
    def convert_to_uv_coordinates(self, image, preserve_colors):
        img_array = np.array(image)
        uv_grid = []
        
        for x in range(self.grid_width):
            for y in range(self.grid_height - 1, -1, -1):
                pixel_color = tuple(img_array[y, x])
                
                closest, color_index = self.find_closest_color(pixel_color)
                uv_grid.append(f"{color_index}")
                if not preserve_colors:
                    hex_r = int(closest[0:2], 16)
                    hex_g = int(closest[2:4], 16)
                    hex_b = int(closest[4:6], 16)
                    image.putpixel([x, y], (hex_r, hex_g, hex_b))

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