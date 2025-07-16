# Dependencies

## Installation

Must have python installed to use pip package manager.

```bash
pip install pillow numpy scikit-learn
```

# Usage
Run the following command:
```bash
python png_converter.py your_image.png
```
Make sure you cd into the scripts directory and also have your flag image in that same directory.

## Output
You will then get a text file output called ```pixel_grid_data``` in that same directory.

# Registry 
Open your **registry editor** by typing "reg" in the windows search bar or Windows + R and type "regedit".

Navigate to ```HKEY_CURRENT_USER\Software\jrsjams\MageArena```.

Inside you will find something along the lines of ```flagGrid_xxxxxxxxxx``` , copy that name and save it for later.
Delete the current entry and make a new one by right clicking -> new -> string value.
Give it the same name. Copy the contents of ```pixel_grid_data``` into the value input (it may not look like it pasted just click ok and it will be there.

Launch the game and **load** the flag, Saving a flag using the in game flag saver will revert the registry back into a binary value and youll have to repeat the steps.

# Current Issues:
- Registry does not automatically update.
- Images are all butchered for the moment.
