import sys
import zipfile
import os
import re
import struct
import io
import subprocess, json
from PIL import Image
from pathlib import Path

skincolors = {
        "white":          [  0,   0,   0,   0,   1,   2,   5,   8,   9,  11,  14,  17,  20,  22,  25,  28],
        "silver":         [  0,   1,   2,   3,   5,   7,   9,  12,  13,  15,  18,  20,  23,  25,  27,  30],
        "grey":           [  1,   3,   5,   7,   9,  11,  13,  15,  17,  19,  21,  23,  25,  27,  29,  31],
        "nickel":         [  3,   5,   8,  11,  15,  17,  19,  21,  23,  24,  25,  26,  27,  29,  30,  31],
        "black":          [  4,   7,  11,  15,  20,  22,  24,  27,  28,  28,  28,  29,  29,  30,  30,  31],
        "skunk":          [  0,   1,   2,   3,   4,  10,  16,  21,  23,  24,  25,  26,  27,  28,  29,  31],
        "fairy":          [  0,   0, 252, 252, 200, 201, 211,  14,  16,  18,  20,  22,  24,  26,  28,  31],
        "popcorn":        [  0,  80,  80,  81,  82, 218, 240,  11,  13,  16,  18,  21,  23,  26,  28,  31],
        "artichoke":      [ 80,  88,  89,  98,  99,  91,  12,  14,  16,  18,  20,  22,  24,  26,  28,  31],
        "pigeon":         [  0, 128, 129, 130, 146, 170,  14,  15,  17,  19,  21,  23,  25,  27,  29,  31],
        "sepia":          [  0,   1,   3,   5,   7,   9, 241, 242, 243, 245, 247, 249, 236, 237, 238, 239],
        "beige":          [  0, 208, 216, 217, 240, 241, 242, 243, 245, 247, 249, 250, 251, 237, 238, 239],
        "caramel":        [208,  48, 216, 217, 218, 220, 221, 223, 224, 226, 228, 230, 232, 234, 236, 239],
        "peach":          [  0, 208,  48, 216, 218, 221, 212, 213, 214, 215, 206, 207, 197, 198, 199, 254],
        "brown":          [216, 217, 219, 221, 224, 225, 227, 229, 230, 232, 234, 235, 237, 239,  29,  30],
        "leather":        [218, 221, 224, 227, 229, 231, 233, 235, 237, 239,  28,  28,  29,  29,  30,  31],
        "pink":           [  0, 208, 208, 209, 209, 210, 211, 211, 212, 213, 214, 215,  41,  43,  45,  46],
        "rose":           [209, 210, 211, 211, 212, 213, 214, 215,  41,  42,  43,  44,  45,  71,  46,  47],
        "cinnamon":       [216, 221, 224, 226, 228,  60,  61,  43,  44,  45,  71,  46,  47,  29,  30,  31],
        "ruby":           [  0, 208, 209, 210, 211, 213,  39,  40,  41,  43, 186, 186, 169, 169, 253, 254],
        "raspberry":      [  0, 208, 209, 210,  32,  33,  34,  35,  37,  39,  41,  43,  44,  45,  46,  47],
        "red":            [209, 210,  32,  34,  36,  38,  39,  40,  41,  42,  43,  44 , 45,  71,  46,  47],
        "crimson":        [210,  33,  35,  38,  40,  42,  43,  45,  71,  71,  46,  46,  47,  47,  30,  31],
        "maroon":         [ 32,  33,  35,  37,  39,  41,  43, 237,  26,  26,  27,  27,  28,  29,  30,  31],
        "lemonade":       [  0,  80,  81,  82,  83, 216, 210, 211, 212, 213, 214, 215,  43,  44,  71,  47],
        "scarlet":        [ 48,  49,  50,  51,  53,  34,  36,  38, 184, 185, 168, 168, 169, 169, 254,  31],
        "ketchup":        [ 72,  73,  64,  51,  52,  54,  34,  36,  38,  40,  42,  43,  44,  71,  46,  47],
        "dawn":           [  0, 208, 216, 209, 210, 211, 212,  57,  58,  59,  60,  61,  63,  71,  47,  31],
        "sunslam":        [ 82,  72,  73,  64,  51,  53,  55, 213, 214, 195, 195, 173, 174, 175, 253, 254],
        "creamsicle":     [  0,   0, 208, 208,  48,  49,  50,  52,  53,  54,  56,  57,  58,  60,  61,  63],
        "orange":         [208,  48,  49,  50,  51,  52,  53,  54,  55,  57,  59,  60,  62,  44,  71,  47],
        "rosewood":       [ 50,  52,  55,  56,  58,  59,  60,  61,  62,  63,  44,  45,  71,  46,  47,  30],
        "tangerine":      [ 80,  81,  82,  83,  64,  51,  52,  54,  55,  57,  58,  60,  61,  63,  71,  47],
        "tan":            [  0,  80,  81,  82,  83,  84,  85,  86,  87, 245, 246, 248, 249, 251, 237, 239],
        "cream":          [  0,  80,  80,  81,  81,  49,  51, 222, 224, 227, 230, 233, 236, 239,  29,  31],
        "gold":           [  0,  80,  81,  83,  64,  65,  66,  67,  68, 215,  69,  70,  44,  71,  46,  47],
        "royal":          [ 80,  81,  83,  64,  65, 223, 229, 196, 196, 197, 197, 198, 199,  29,  30,  31],
        "bronze":         [ 83,  64,  65,  66,  67, 215,  69,  70,  44,  44,  45,  71,  46,  47,  29,  31],
        "copper":         [  0,  82,  64,  65,  67,  68,  70, 237, 239,  28,  28,  29,  29,  30,  30,  31],
        "yellow":         [  0,  80,  81,  82,  83,  73,  84,  74,  64,  65,  66,  67,  68,  69,  70,  71],
        "mustard":        [ 80,  81,  82,  83,  64,  65,  65,  76,  76,  77,  77,  78,  79, 237, 239,  29],
        "banana":         [ 80,  81,  83,  72,  73,  74,  75,  76,  77,  78,  79, 236, 237, 238, 239,  30],
        "olive":          [ 80,  82,  73,  74,  75,  76,  77,  78,  79, 236, 237, 238, 239,  28,  29,  31],
        "crocodile":      [  0,  80,  81,  88,  88, 188, 189,  76,  76,  77,  78,  79, 236, 237, 238, 239],
        "peridot":        [  0,  80,  81,  88, 188, 189, 190, 191,  94,  94,  95,  95, 109, 110, 111,  31],
        "vomit":          [  0, 208, 216, 209, 218,  51,  65,  76, 191, 191, 126, 143, 138, 175, 169, 254],
        "garden":         [ 81,  82,  83,  73,  64,  65,  66,  92,  92,  93,  93,  94,  95, 109, 110, 111],
        "lime":           [  0,  80,  81,  88, 188, 189, 114, 114, 115, 115, 116, 116, 117, 118, 119, 111],
        "handheld":       [ 83,  72,  73,  74,  75,  76, 102, 104, 105, 106, 107, 108, 109, 110, 111,  31],
        "tea":            [  0,  80,  80,  81,  88,  89,  90,  91,  92,  93,  94,  95, 109, 110, 111,  31],
        "pistachio":      [  0,  80,  88,  88,  89,  90,  91, 102, 103, 104, 105, 106, 107, 108, 109, 110],
        "moss":           [ 88,  89,  90,  91,  91,  92,  93,  94, 107, 107, 108, 108, 109, 109, 110, 111],
        "camouflage":     [208,  84,  85, 240, 241, 243, 245,  94, 107, 108, 108, 109, 109, 110, 110, 111],
        "mint":           [  0,  88,  88,  89,  89, 100, 101, 102, 125, 126, 143, 143, 138, 175, 169, 254],
        "green":          [ 96,  97,  98,  99, 100, 101, 102, 103, 104, 105, 106, 107, 108, 109, 110, 111],
        "pinetree":       [ 97,  99, 101, 102, 103, 104, 105, 106, 107, 108, 109, 110, 111,  30,  30,  31],
        "turtle":         [ 96, 112, 112, 113, 113, 114, 114, 115, 115, 116, 116, 117, 117, 118, 119, 111],
        "swamp":          [ 96, 112, 113, 114, 115, 116, 117, 118, 119, 119,  29,  29,  30,  30,  31,  31],
        "dream":          [  0,   0, 208, 208,  48,  89,  98, 100, 148, 148, 172, 172, 173, 173, 174, 175],
        "plague":         [ 80,  88,  96, 112, 113, 124, 142, 149, 149, 173, 174, 175, 169, 253, 254,  31],
        "emerald":        [  0, 120, 121, 112, 113, 114, 115, 125, 125, 126, 126, 127, 138, 175, 253, 254],
        "algae":          [128, 129, 130, 131, 132, 133, 134, 115, 115, 116, 116, 117, 118, 119, 110, 111],
        "aquamarine":     [  0, 128, 120, 121, 122, 123, 124, 125, 126, 126, 127, 127, 118, 118, 119, 111],
        "turquoise":      [128, 120, 121, 122, 123, 141, 141, 142, 142, 143, 143, 138, 138, 139, 139,  31],
        "teal":           [  0, 120, 120, 121, 140, 141, 142, 143, 143, 138, 138, 139, 139, 254, 254,  31],
        "robin":          [  0,  80,  81,  82,  83,  88, 121, 140, 133, 133, 134, 135, 136, 137, 138, 139],
        "cyan":           [  0,   0, 128, 128, 255, 131, 132, 134, 142, 142, 143, 127, 118, 119, 110, 111],
        "jawz":           [  0,   0, 128, 128, 129, 146, 133, 134, 135, 149, 149, 173, 173, 174, 175,  31],
        "cerulean":       [  0, 128, 129, 130, 131, 132, 133, 135, 136, 136, 137, 137, 138, 138, 139,  31],
        "navy":           [128, 129, 130, 132, 134, 135, 136, 137, 137, 138, 138, 139, 139,  29,  30,  31],
        "platinum":       [  0,   0,   0, 144, 144, 145,   9,  11,  14, 142, 136, 137, 138, 138, 139,  31],
        "slate":          [  0,   0, 144, 144, 144, 145, 145, 145, 170, 170, 171, 171, 172, 173, 174, 175],
        "steel":          [  0, 144, 144, 145, 145, 170, 170, 171, 171, 172, 172, 173, 173, 174, 175,  31],
        "thunder":        [ 80,  81,  82,  83,  64,  65,  11, 171, 172, 173, 173, 157, 158, 159, 254,  31],
        "nova":           [  0,  83,  49,  50,  51,  32, 192, 148, 148, 172, 173, 174, 175,  29,  30,  31],
        "rust":           [208,  48, 216, 217, 240, 241, 242, 171, 172, 173,  24,  25,  26,  28,  29,  31],
        "wristwatch":     [ 48, 218, 221, 224, 227, 231, 196, 173, 173, 174, 159, 159, 253, 253, 254,  31],
        "jet":            [145, 146, 147, 148, 149, 173, 173, 174, 175, 175,  28,  28,  29,  29,  30,  31],
        "sapphire":       [  0, 128, 129, 131, 133, 135, 149, 150, 152, 154, 156, 158, 159, 253, 254,  31],
        "ultramarine":    [  0,   0, 120, 120, 121, 133, 135, 149, 149, 166, 166, 167, 168, 169, 254,  31],
        "periwinkle":     [  0,   0, 144, 144, 145, 146, 147, 149, 150, 152, 154, 155, 157, 159, 253, 254],
        "blue":           [144, 145, 146, 147, 148, 149, 150, 151, 152, 153, 155, 156, 158, 253, 254,  31],
        "midnight":       [146, 148, 149, 150, 152, 153, 155, 157, 159, 253, 253, 254, 254,  31,  31,  31],
        "blueberry":      [  0, 144, 145, 146, 147, 171, 172, 166, 166, 167, 167, 168, 168, 175, 169, 253],
        "thistle":        [  0,   0,   0, 252, 252, 160, 161, 162, 163, 164, 165, 166, 167, 168, 169, 254],
        "purple":         [  0, 252, 160, 161, 162, 163, 164, 165, 166, 167, 168, 168, 169, 169, 253, 254],
        "pastel":         [  0, 128, 128, 129, 129, 146, 170, 162, 163, 164, 165, 166, 167, 168, 169, 254],
        "moonset":        [  0, 144, 145, 146, 170, 162, 163, 184, 184, 207, 207,  44,  45,  46,  47,  31],
        "dusk":           [252, 200, 201, 192, 193, 194, 172, 172, 173, 173, 174, 174, 175, 169, 253, 254],
        "violet":         [176, 177, 178, 179, 180, 181, 182, 183, 184, 165, 165, 166, 167, 168, 169, 254],
        "magenta":        [252, 200, 177, 177, 178, 179, 180, 181, 182, 183, 183, 184, 185, 186, 187,  31],
        "fuchsia":        [208, 209, 209,  32,  33, 182, 183, 184, 185, 185, 186, 186, 187, 253, 254,  31],
        "toxic":          [  0,   0,  88,  88,  89,   6,   8,  10, 193, 194, 195, 184, 185, 186, 187,  31],
        "mauve":          [ 80,  81,  82,  83,  64,  50, 201, 192, 193, 194, 195, 173, 174, 175, 253, 254],
        "lavender":       [252, 177, 179, 192, 193, 194, 195, 196, 196, 197, 197, 198, 198, 199,  30,  31],
        "byzantium":      [145, 192, 193, 194, 195, 196, 197, 198, 199, 199,  29,  29,  30,  30,  31,  31],
        "pomegranate":    [208, 209, 210, 211, 212, 213, 214, 195, 195, 196, 196, 197, 198, 199,  29,  30],
        "lilac":          [  0,   0,   0, 252, 252, 176, 200, 201, 179, 192, 193, 194, 195, 196, 197, 198],
        "blossom":        [  0, 252, 252, 176, 200, 177, 201, 202, 202,  34,  36,  38,  40,  42,  45,  46],
        "taffy":          [  0, 252, 252, 200, 200, 201, 202, 203, 204, 204, 205, 206, 207,  43,  45,  47],
    }
lua_prefix = """
  function addHook() end
  function freeslot(name)
    _ENV[name] = name
  end
  function to_json(tbl)
    local json = "{"
    first = true
    for k, v in pairs(tbl) do
      if first then
        first = false
      else
        json = json .. ","
      end
      if type(v) == "table" then 
        json = json .. string.format('%q: %s', tostring(k), to_json(v))
      else
        json = json .. string.format('%q: %q', tostring(k), v)
      end
    end
    json = json .. "}"
    return json
  end
  skincolors = {}
  setmetatable(_ENV, {
    __index = function(tbl, key) return key end
  })
"""

lua_suffix = """
  print(to_json(skincolors))
"""

def clean_blua(blua):
  lines = re.sub(r'(?<!^)\s+\n', '\n', blua).split('\n')
  cleaned = ''
  for line in lines:
    line = line.split('//')[0]
    # print(line, re.search(r'if ', line), re.search(r'\sthen', line))
    if re.search(r'if\s', line) and not re.search(r'\sthen', line):
      line = line + ' then'
    cleaned += line + '\n'
  return cleaned

def get_lua_skincolors(path=None, file=None):
    if not file:
        file = open(path, 'rb')
    base_script = clean_blua(file.read().decode())
    script = lua_prefix + base_script + lua_suffix
    lua = subprocess.run('lua', input=script.encode(), capture_output=True)
    if len(lua.stderr):
        raise Exception(lua.stderr.decode() + "\n\n" + base_script)
    return json.loads(lua.stdout.decode())
  
# print(get_lua_skincolors("test.lua"))

class WadFile(object):
    def __init__(self, source=None, filename=None):
        self._files = {}
        if not source:
            source = open(filename, 'rb')
        self._source = source
        header = source.read(12)
        (magic, numFiles, dirOffset) = struct.unpack('<III', header)
        source.seek(dirOffset)
        for i in range(numFiles):
            dirent = source.read(16)
            (pos, size, name) = struct.unpack('<II8s', dirent)
            name = name.replace(b'\0', b'').decode()
            self._files[name] = { "pos": pos, "size": size }

    def namelist(self):
        return self._files.keys()
    
    def open(self, name, mode='r'):
        dirent = self._files[name]
        self._source.seek(dirent['pos'])
        return io.BytesIO(self._source.read(dirent['size']))

def extract_startcolor(pk3, file_path):
    try:
        with pk3.open(os.path.join(file_path, 'S_SKIN')) as file:
            # Read the entire file content as bytes
            file_content_bytes = file.read()
            # Decode bytes to string using UTF-8 encoding (or appropriate encoding for your file)
            file_content = file_content_bytes.decode('utf-8')

            # Use regular expression to find the startcolor value
            match = re.search(r'startcolor\s*=\s*(\d+)', file_content)
            if match:
                startcolor_value = int(match.group(1))
                if startcolor_value != 96:
                    print("Startcolor value:", startcolor_value)
                return startcolor_value
            else:
                return 96
    except FileNotFoundError:
        print("File not found.")
        return 96

def extract_prefcolor(pk3, file_path):
    try:
        with pk3.open(os.path.join(file_path, 'S_SKIN')) as file:
            # Read the entire file content as bytes
            file_content_bytes = file.read()
            # Decode bytes to string using UTF-8 encoding (or appropriate encoding for your file)
            file_content = file_content_bytes.decode('utf-8')

            # Use regular expression to find the startcolor value
            match = re.search(r'prefcolor\s*=\s*(\w+)', file_content)
            if match:
                prefcolor_value = match.group(1).lower();
                if prefcolor_value != "green":
                    print("Prefcolor value:", prefcolor_value)
                return prefcolor_value
            else:
                return "green"
    except FileNotFoundError:
        print("File not found.")
        return "green"

def extract_name(pk3, character_folder):
    try:
        with pk3.open(os.path.join(character_folder, 'S_SKIN')) as file:
            # Read the entire file content as bytes
            file_content_bytes = file.read()
            # Decode bytes to string using UTF-8 encoding (or appropriate encoding for your file)
            file_content = file_content_bytes.decode('utf-8')

            # Use regular expression to find the startcolor value
            match = re.search(r'name\s*=\s*(\w+)', file_content)
            if match:
                prefcolor_value = match.group(1).lower();
                if prefcolor_value != character_folder:
                    print("Prefcolor value:", prefcolor_value)
                return prefcolor_value
            else:
                return character_folder
    except FileNotFoundError:
        print("File not found.")
        return character_folder

def convert_doom_to_png(bios, image, output_location, startcolor, color, size, default = False):
    palette = []
    with bios.open('PLAYPAL', 'r') as f:
        for i in range(256):
            [r, g, b] = f.read(3)
            palette.append([r, g, b])
    colormap = list(range(256))

    # Open the Doom image file in binary mode
    f = image
    f.seek(0)
    # Read width, height, left, and top from the Doom image
    width = int.from_bytes(f.read(2), byteorder='little')
    height = int.from_bytes(f.read(2), byteorder='little')
    left = int.from_bytes(f.read(2), byteorder='little')
    top = int.from_bytes(f.read(2), byteorder='little')

    # Create column_array with width number of elements
    column_array = [0] * width

    # Read column_array from the Doom image
    for i in range(width):
        column_array[i] = int.from_bytes(f.read(4), byteorder='little')

    # Create a new image with 8-bit pixel format and Doom palette
    doom_image = Image.new('P', (width, height))
    scolor = startcolor
    for i in skincolors[color]:
        colormap[scolor] = i
        scolor += 1
    pal = []
    for i in colormap:
        pal.append(palette[i][0])
        pal.append(palette[i][1])
        pal.append(palette[i][2])
    doom_image.putpalette(pal)

    # Read pixels from the Doom image and write to the PNG image
    for i in range(width):
        f.seek(column_array[i])
        rowstart = 0
        while rowstart != 255:
            rowstart = int.from_bytes(f.read(1), byteorder='little')
            if rowstart == 255:
                break
            pixel_count = int.from_bytes(f.read(1), byteorder='little')
            dummy_value = int.from_bytes(f.read(1), byteorder='little')
            for j in range(pixel_count):
                pixel = int.from_bytes(f.read(1), byteorder='little')
                doom_image.putpixel((i, j + rowstart), pixel)
            dummy_value = int.from_bytes(f.read(1), byteorder='little')

    # Save the PNG image
    output_path = os.path.join(output_location, color + '.png')
    if (default):
        output_path = os.path.join(output_location, 'default' + '.png')
    resized_image = doom_image.resize((32 * size, 32 * size), Image.BILINEAR)
    resized_image.save(output_path)
    print(output_path)

def open_addon(bios, addon, output_location, size):
    # Get the list of all files and directories in the zip archive
    all_entries = addon.namelist()

    # Set to collect unique folder names
    folder_set = set()

    for entry in all_entries:
        if entry.endswith('S_SKIN'):
            # Handle root directory case
            if '/' in entry:
                folder_name = '/'.join(entry.split('/')[:-1])  # Get the directory path
            else:
                folder_name = ''
            folder_set.add(folder_name)
        if Path(entry).suffix.lower() == ".lua":
            for obj in get_lua_skincolors(file=addon.open(entry)).values():
                skincolors[obj['name'].lower()] = list(obj['ramp'].values())
    # Iterate over each file and directory in the zip archive
    # for entry in all_entries:
    #     # Check if the entry is a directory within the specified parent directory
    #     if entry.startswith(parent_directory) and '/' in entry[len(parent_directory):]:
    #         folder_name = os.path.dirname(entry)[len(parent_directory):]
    #         folder_set.add(folder_name)

    # Convert the set of folder names to a list
    folder_list = list(folder_set)

    os.makedirs(os.path.join(output_location, "characters"), exist_ok=True)

    # Print the list of folder names
    for folder_name in folder_list:
        character_name = extract_name(addon, folder_name).lower()
        folder_path = os.path.join(output_location, "characters", character_name.lower())
        os.makedirs(folder_path, exist_ok=True)
        with addon.open(os.path.join(folder_name, 'XTRAB0'), 'r') as image:
            startcolor = extract_startcolor(addon, folder_name)
            for color in skincolors:
                convert_doom_to_png(bios, image, folder_path, startcolor, color, size)
            c = extract_prefcolor(addon, folder_name)
            convert_doom_to_png(bios, image, folder_path, startcolor, c, size, True)

if __name__ == "__main__":
    if len(sys.argv) < 4 or len(sys.argv) > 5:
        print("Usage: python extract_skins.py <bios.pk3 file> <character pack> <output folder> <size multiplier>")
        sys.exit(1)
    bios_arg = sys.argv[1]
    addon = sys.argv[2]
    output_location = sys.argv[3]
    size = 1 if len(sys.argv) == 4 else int(sys.argv[4])
    # for color in skincolors:
    #     convert_doom_to_png(doom_file, output_location, color)
    with zipfile.ZipFile(bios_arg, 'r') as bios:
        print(Path(addon).suffix)

        if Path(addon).suffix == ".pk3":
            with zipfile.ZipFile(addon, 'r') as pk3:
                open_addon(bios, pk3, output_location, size)
        if Path(addon).suffix == ".wad":
            wad = WadFile(open(addon, 'rb'))
            open_addon(bios, wad, output_location, size)
