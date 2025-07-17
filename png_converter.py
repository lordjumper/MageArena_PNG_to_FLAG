import os
import sys
from skimage import color
from PIL import Image
import numpy as np
import json

pixel_color_map = {
    "cd5455": "0.9460317:0.08793658",
    "caa215": "0.787302:0.05619055",
    "bbad07": "0.6603174:0.06571439",
    "7bc254": "0.4825399:0.07523811",
    "0ebebc": "0.3333334:0.08793658",
    "7aabcd": "0.209524:0.07206351",
    "c12fd4": "0.06031764:0.05619055",
    "c50000": "0.9396828:0.2784127",
    "cc8d00": "0.809524:0.2561905",
    "beb200": "0.6857144:0.2784127",
    "00c800": "0.5619048:0.2879366",
    "00c8c1": "0.3650795:0.2593651",
    "008ade": "0.257143:0.2911112",
    "b600dc": "0.03174627:0.2530159",
    "c70000": "0.9555559:0.3863491",
    "cf6d00": "0.8000001:0.427619",
    "c0af00": "0.6476193:0.4180952",
    "00c200": "0.5238097:0.4212698",
    "00cdc8": "0.3587303:0.4307936",
    "78E6E6": "0.3587303:0.4307936",
    "0000e5": "0.2285715:0.4244444",
    "9100de": "0.06031764:0.4339682",
    "610000": "0.9174606:0.5704762",
    "6c2e00": "0.8285716:0.5831746",
    "6b5f00": "0.6539685:0.5546032",
    "009700": "0.5142859:0.5831746",
    "00787c": "0.3777779:0.564127",
    "0007b9": "0.2285715:0.6022222",
    "4700a4": "0.08571446:0.58",
    "230000": "0.9777781:0.7450794",
    "341500": "0.7555556:0.7355555",
    "241f00": "0.6349207:0.7736508",
    "003200": "0.5269845:0.7609525",
    "00262b": "0.3841273:0.7609525",
    "000b50": "0.2507938:0.78",
    "240050": "0.03174627:0.7546031",
    "e2dfe0": "0.9746034:0.9419048",
    "d5d3d4": "0.8000001:0.9196825",
    "bdbdbc": "0.6317463:0.9196825",
    "a4a49f": "0.5238097:0.9038095",
    "696e77": "0.3587303:0.9133333",
    "293034": "0.2063494:0.9038095",
    "020202": "0.0476191:0.9196825",
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
        
        for y in range(self.grid_height):
            for x in range(self.grid_width):
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