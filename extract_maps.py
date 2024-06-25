import sys
import zipfile
import os
import re
import io
import struct
from PIL import Image, ImageOps
from pathlib import Path

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

def get_level_names(pk3, levels, soc):
    currentLevel = None
    with pk3.open(soc) as file:
        # Read the entire file content as bytes
        file_content_bytes = file.read()
        # Decode bytes to string using UTF-8 encoding (or appropriate encoding for your file)
        file_content = file_content_bytes.decode('utf-8')
        for line in file_content.splitlines():
            # print(line)
            # print(line, line.startswith('Level'), line.startswith('#'), '=' in line)
            if line.startswith('Level '):
                currentLevel = line.split(' ')[1].lower()
                # currentLevel = line.replace('=', ' ').strip().split(' ')[-1]
                levels[currentLevel] = {}
                continue
            elif not currentLevel or line.startswith('#') or '=' not in line:
                continue
            [key, value] = line.split('=')
            levels[currentLevel][key.strip().lower()] = value.strip()
            # print(currentLevel)
    return levels

if __name__ == "__main__":
    if len(sys.argv) < 4 or len(sys.argv) > 5:
        print("Usage: python extract_skins.py <bios.pk3 file> <pack> <output folder> <size multiplier>")
        sys.exit(1)
    bios_arg = sys.argv[1]
    doom_file = sys.argv[2]
    output_location = sys.argv[3]
    scale = 1 if len(sys.argv) == 4 else int(sys.argv[4])


    with zipfile.ZipFile(bios_arg, 'r') as bios:
        palette = []
        with bios.open('PLAYPAL', 'r') as f:
            for i in range(256):
                [r, g, b] = f.read(3)
                palette.append([r, g, b])
        colormap = list(range(256))
        pal = []
        for i in colormap:
            pal.append(palette[i][0])
            pal.append(palette[i][1])
            pal.append(palette[i][2])

        with zipfile.ZipFile(doom_file, 'r') as pk3:
            # Get the list of all files and directories in the zip archive
            all_entries = pk3.namelist()

            # Specify the parent directory you want to search within
            parent_directory = 'maps/'

            # Set to collect unique folder names
            wad_set = set()
            soc_set = set()

            # Iterate over each file and directory in the zip archive
            for entry in all_entries:
                # print(entry)
                # Check if the entry is a directory within the specified parent directory
                if entry.startswith(parent_directory) and entry.endswith('.wad'):
                    wad_set.add(entry)
                if entry.startswith('soc/'):
                    soc_set.add(entry)

            # Convert the set of folder names to a list
            wad_list = list(wad_set)
            soc_list = list(soc_set)
            # print(wad_list)

            levels = {}
            for soc_name in soc_list:
                levels = get_level_names(pk3, levels, soc_name)
            os.makedirs(os.path.join(output_location, "maps"), exist_ok=True)

            # Print the list of folder names
            for wad_name in wad_list:
                # if wad_name == "maps/race/RR_CoastalTemple.wad":
                #     continue
                true_name = Path(wad_name).stem
                map_type = ""
                # print(true_name)
                if true_name.lower() in levels:
                    level = levels[true_name.lower()]
                    if 'zonetitle' in level:
                        true_name = '%s %s' % (level['levelname'], level['zonetitle'])
                    elif 'nozone' in level and level['nozone'] == 'True':
                        true_name = level['levelname']
                    else:
                        true_name = '%s Zone' % (level['levelname'])
                    if 'act' in level:
                        true_name += ' %s' % (level['act'])
                    elif 'menutitle' in level:
                        true_name += ' %s' % (level['menutitle'])

                    if 'typeoflevel' in level:
                        map_type = level['typeoflevel'].lower()
                output_path = os.path.join(output_location, 'maps', true_name.replace(" ", "_") + '.png')
                encore_output_path = os.path.join(output_location, 'maps', true_name.replace(" ", "_") + '_Encore.png')
                # if os.path.isfile(output_path):
                #     output_path = os.path.join(output_location, Path(wad_name).stem + '.png')
                # _name = extract_name(pk3, folder_name).lower()
                # folder_path = os.path.join(output_location, "s", character_name.lower())
                # os.makedirs(folder_path, exist_ok=True)
                # print(wad_name)
                wad = WadFile(pk3.open(wad_name, 'r'))

                all_entries = wad.namelist()

                enpal = pal
                encore_colormap = list()
                for entry in all_entries:
                    if entry == 'ENCORE':
                        enpalette = []
                        en = wad.open('ENCORE')
                        encore_colormap = en.read(256)
                        # for i in range(256):
                        #     r = en.read(1)
                        #     g = en.read(1)
                        #     b = en.read(1)
                        #     enpalette.append([r, g, b])
                        colormap = list(range(256))
                        # print("Colormap")
                        # print(colormap)
                        # print("Encore Colormap")
                        # print(encore_colormap)
                        enpal = []
                        for i in encore_colormap:
                            enpal.append(palette[i][0])
                            enpal.append(palette[i][1])
                            enpal.append(palette[i][2])

                # print("Palette")
                # print(pal)
                # print("Encore Palette")
                # print(enpal)
                # print(encore_colormap)
                f = wad.open('PICTURE')
                # print(file)
                # print(wad_name)
                # print(data.hex())

                # Read width, height, left, and top from the Doom image
                # width = int.from_bytes(f.read(2), byteorder='little')
                # height = int.from_bytes(f.read(2), byteorder='little')
                imgheader = f.read(4)
                if imgheader == b'\x89PNG':
                    doom_image = Image.open(io.BytesIO(imgheader + f.read()))
                    resized_image = doom_image.resize((320 * scale, 200 * scale), Image.BILINEAR)
                    resized_image.save(output_path)
                    if map_type == 'race' or map_type == 'versus':
                        encore_resized_image = ImageOps.mirror(resized_image)
                        encore_resized_image.save(encore_output_path)
                    continue
                else:
                    [width, height] = struct.unpack('<HH', imgheader)
                left = int.from_bytes(f.read(2), byteorder='little')
                top = int.from_bytes(f.read(2), byteorder='little')

                # Create column_array with width number of elements
                column_array = [0] * width

                # Read column_array from the Doom image
                for i in range(width):
                    column_array[i] = int.from_bytes(f.read(4), byteorder='little')

                # Create a new image with 8-bit pixel format and Doom palette
                doom_image = Image.new('P', (width, height))
                doom_image.putpalette(pal)
                if map_type == 'race' or map_type == 'versus':
                    encore_image = Image.new('P', (width, height))
                    encore_image.putpalette(enpal)

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
                            if map_type == 'race' or map_type == 'versus':
                                encore_image.putpixel((i, j + rowstart), pixel)
                        dummy_value = int.from_bytes(f.read(1), byteorder='little')

                # Save the PNG image
                resized_image = doom_image.resize((320 * scale, 200 * scale), Image.BILINEAR)
                resized_image.save(output_path)
                print(output_path)
                if map_type == 'race' or map_type == 'versus':
                    encore_resized_image = ImageOps.mirror(encore_image.resize((320 * scale, 200 * scale), Image.BILINEAR))
                    encore_resized_image.save(encore_output_path)
                    print(encore_output_path)
