#!/bin/env python3
import subprocess
import sys
import zipfile
import os
import re
import io
import struct
import json
from glob import glob
from pathlib import Path

forbidden_chars = r'[<>:"/\\|?*]'
linux_forbidden_chars = r'[/?\0~]'
replacement_char = '_'

def sanitize_filename(filename):
    """
    Replace forbidden characters in a filename with a specified replacement character.
    Also ensure filenames do not end with a space or a period.
    """
    # Replace forbidden characters
    sanitized_name = re.sub(forbidden_chars, replacement_char, filename)
    sanitized_name = re.sub(linux_forbidden_chars, replacement_char, sanitized_name)
    
    # Remove trailing spaces and periods
    sanitized_name = sanitized_name.rstrip(' .')
    
    return sanitized_name

def get_file_extension(binary_data):
    # File signatures (magic numbers) and their corresponding file extensions
    magic_numbers = {
        b'IMPM': 'it',  # IT (Impulse Tracker) at offset 0
        b'Extended Module: ': 'xm',  # XM (FastTracker 2 Extended Module) at offset 0
        b'SCRM': 's3m',  # S3M (ScreamTracker 3 Module) at offset 44
        # MOD files have various formats
        b'M.K.': 'mod',  # Protracker at offset 1080
        b'M!K!': 'mod',
        b'4CHN': 'mod',
        b'6CHN': 'mod',
        b'8CHN': 'mod',
        b'OggS': 'ogg',
    }

    for signature, extension in magic_numbers.items():
        if binary_data.startswith(signature):
            return extension

    return 's3m'  # default to 'bin' if unknown

def number_to_letter(n):
    if 0 <= n < 26:
        return chr(ord('A') + n)
    else:
        return None

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
            if line.startswith('Lump '):
                currentLevel = line.split(' ')[1].lower().replace('\\', '').split(",")
                # currentLevel = line.replace('=', ' ').strip().split(' ')[-1]
                i = 0
                for level in currentLevel:
                    levels[level] = {}
                    if len(currentLevel) > 1:
                        levels[level]["track"] = number_to_letter(i)
                    i = i + 1
                continue
            elif not currentLevel or line.startswith('#') or '=' not in line:
                continue
            for level in currentLevel:
                [key, value] = line.split('=', 1)
                levels[level][key.strip().lower()] = value.strip()
            # print(currentLevel)
    return levels

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python extract_music.py <music.pk3|altmusic.pk3> <output_location>")
        sys.exit(1)
    addon = sys.argv[1]
    output_location = sys.argv[2]
    print(Path(addon).suffix)

    if Path(addon).suffix == ".pk3":
        with zipfile.ZipFile(addon, 'r') as pk3:
            all_entries = pk3.namelist()

            musicdef_files = set()
            music_files = set()

            
            for entry in all_entries:
                if "MUSICDEF" in entry:
                    musicdef_files.add(entry)
                if "/O_" in entry:
                    music_files.add(entry)
            def_list = list(musicdef_files)
            music_list = list(music_files)

            # file_paths = [
            #     "Music/Sekhedsu/O_KOVOZ",
            #     "Music/Tape/O_CACRZ",
            #     "Music/Tape/O_CHSEZ",
            #     "Music/Tape/O_WHWAZ",
            #     "Music/Tape/O_NOSHZ.it",
            #     "Music/Tape/O_DOPE1.it",
            #     "Music/Tape/O_CRISZ.mod",
            #     "Music/Tape/O_MYGAZ",
            #     "Music/Tape/O_BAFOZ",
            #     "Music/Tape/O_TIARZ",
            #     "Music/Tape/O_HOHOZ",
            #     "Music/Tape/O_HYPLZ",
            #     "Music/Tape/O_THTOZ",
            #     "Music/Tape/O_TRMAZ.xm"
            # ]


            songs = {}
            for soc_name in def_list:
                levels = get_level_names(pk3, songs, soc_name)

            # print(json.dumps(songs, indent=4))
            # print(music_list)
            os.makedirs(os.path.join(output_location), exist_ok=True)
            for file in music_list:
                fparts = file.split('.')
                fname = fparts[0]
                fext = ''
                with pk3.open(file) as song:
                    binary = song.read()
                    if len(fparts) > 1:
                        fext = "." + fparts[1]
                    else:
                        fext = "." + get_file_extension(binary)
                    fname = fname.split('.')[0] + fext
                    with open(os.path.join(output_location, "tmp" + fext), "wb") as output:
                        output.write(binary)
                        for key in songs.keys():
                            parts = fname.split("O_")
                            if parts[len(parts)-1].lower() == key+fext:
                                song_name = os.path.join(output_location, key + ".mp3")
                                # print(key, json.dumps(songs[key], indent=4))
                                volume = 1
                                title = ""
                                artist = ""
                                track = ""
                                if "track" in songs[key]:
                                    track = f' (Track {songs[key]["track"]})'
                                if "title" in songs[key]:
                                    song_name = os.path.join(output_location, sanitize_filename(songs[key]["title"]) + track + ".mp3")
                                    title = songs[key]["title"] + track
                                if "volume" in songs[key]:
                                    volume = int(songs[key]["volume"].split(' #')[0])/100.0
                                if "author" in songs[key]:
                                    artist = songs[key]["author"]
                                if "originalcomposers" in songs[key]:
                                    if not artist == "":
                                        artist += ", "
                                    artist += songs[key]["originalcomposers"]
                                command1 = [
                                        "vgmstream-cli",
                                        "-o", os.path.join(output_location, "tmp.wav"),
                                        "-l", "1",
                                        "-f", "10",
                                        os.path.join(output_location, "tmp" + fext)
                                ]
                                command2 = [
                                        "ffmpeg",
                                        "-i", os.path.join(output_location, "tmp.wav"),
                                        "-metadata", f'title={title}',
                                        "-metadata", f'artist={artist}',
                                        "-metadata", f'album_artist=Kart Krew',
                                        "-metadata", f'album=Dr. Robotnik\'s Ring Racers',
                                        "-filter:a", f'volume={volume}',
                                        "-y",
                                        "-q:a", "0",
                                        song_name
                                ]
                                print(song_name)
                                try:
                                    subprocess.run(command1, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                                    subprocess.run(command2, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                                    os.remove(os.path.join(output_location, "tmp.wav"))
                                except:
                                    command3 = [
                                            "ffmpeg",
                                            "-i", os.path.join(output_location, "tmp"+fext),
                                            "-metadata", f'title={title}',
                                            "-metadata", f'artist={artist}',
                                            "-metadata", f'album_artist=Kart Krew',
                                            "-metadata", f'album=Dr. Robotnik\'s Ring Racers',
                                            "-filter:a", f"volume={volume}",
                                            "-y",
                                            "-q:a", "0",
                                            song_name
                                    ]
                                    print(fparts[0]+fext)
                                    subprocess.run(command3, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                                break

                    os.remove(os.path.join(output_location, "tmp"+fext))
