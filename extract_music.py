#!/bin/env python3
import subprocess
import argparse
import sys
import zipfile
import os
import re
import io
import struct
import json
import shutil
import signal
from glob import glob
from pathlib import Path

forbidden_chars = r'[<>:"/\\|?*]'
linux_forbidden_chars = r'[/?\0~]'
replacement_char = '_'
encore_sample_rate_multiplier = 0.86471

album_order = [
    [ # Disc 1
        {'name': 'SE_GA_', 'source': ''},
        {'name': 'Fluvial Beat Deposits', 'source': ''},
        {'name': 'Open Ocean', 'source': ''},
        {'name': 'File Select (Reception Mix)', 'source': ''},
        {'name': 'Cascade Cave Zone, Act 1', 'source': ''},
        {'name': 'Cascade Cave Zone, Act 2 (Track A)', 'source': ''},
        {'name': 'Cascade Cave Zone, Act 2 (Track B)', 'source': ''},
        {'name': 'Across The World', 'source': ''},
        {'name': 'Back of the Box', 'source': ''},
        {'name': 'Lost in Recollection', 'source': ''},
        {'name': 'Live Studio Audience', 'source': ''},
        {'name': 'Rolling Jump (Arrange)', 'source': ''},
        {'name': 'Minor Boss (Dual PCM)', 'source': ''},
        {'name': 'Fluvial Beat Deposits (Invincibility Mix)', 'source': ''},
        {'name': 'Desert Area (Grow Mix)', 'source': ''},
        {'name': 'Level Lost', 'source': ''},
        {'name': 'Level Clear', 'source': ''},
        {'name': 'Robotnik Clear', 'source': ''},
        {'name': '[Alternate] Competition Menu', 'source': ''},
        {'name': 'Race Result', 'source': ''},
        {'name': 'Knuckles Victory Jingle', 'source': ''},
        {'name': 'Game Results (Ring Racers Mix)', 'source': ''},
        {'name': '[Alternate] Credits (Version B)', 'source': ''},
        {'name': '[Alternate] Credits (Version A)', 'source': ''},
        {'name': 'Fluvial Beat Deposits (Voting Mix)', 'source': ''},
        {'name': 'Decision (Track A)', 'source': ''},
        {'name': 'Decision (Track B)', 'source': ''},
        {'name': 'CHAO KEY FREE DDL WORKING 2014', 'source': ''},
        {'name': 'History (Ring Racers Mix)', 'source': ''},
        {'name': 'Overtime', 'source': ''},
        {'name': 'Last Stand!', 'source': ''},
        {'name': 'See Your Sunbeam', 'source': ''},
        {'name': 'Tidal Chamber', 'source': ''}
    ],
    [ # Disc 2
        {'name': 'Robotnik Coaster', 'source': ''},
        {'name': 'Broken Moon (Remix)', 'source': ''},
        {'name': 'Remaining Time', 'source': ''},
        {'name': 'Splash Wave (Edit)', 'source': ''},
        {'name': 'Green Hills (SMS)', 'source': ''},
        {'name': 'Tropic Turf Zone, Act 1', 'source': ''},
        {'name': 'Special Stage [US]', 'source': ''},
        {'name': 'Special Stage [JP_PAL]', 'source': ''},
        {'name': 'UFO Catcher', 'source': ''},
        {'name': 'All things upon the sine', 'source': ''},
        {'name': 'Azure Blue World (Edit)', 'source': ''},
        {'name': 'Windy and Ripply', 'source': ''},
        {'name': 'Big Fishes at Emerald Coast', 'source': ''},
        {'name': 'The Core of Distortion', 'source': ''},
        {'name': 'Lucid Pass Zone', 'source': ''},
        {'name': 'Sharp Eyes [twilight mix]', 'source': ''},
        {'name': 'Kronos', 'source': ''},
        {'name': 'Clockwork Orangeade', 'source': ''},
        {'name': 'untitled (snon faller)', 'source': ''},
        {'name': 'Stage 3_ Gratify', 'source': ''},
        {'name': 'Water Battle IN THE SNOW!', 'source': ''},
        {'name': 'Estra Nova', 'source': ''},
        {'name': 'Full-Steam VENGEANCE!!!', 'source': ''},
        {'name': 'Tower of Heaven -Full moon Revenge- (Edit)', 'source': ''},
        {'name': 'Platonic Attitude', 'source': ''},
        {'name': 'Disease Transport (Ring Racers Mix)', 'source': ''},
        {'name': 'Feverish Transport', 'source': ''},
        {'name': 'Angel Island (Good Future)', 'source': ''},
        {'name': 'Angel Island Zone Act 1', 'source': ''},
        {'name': '[Alternate] Angel Island Zone Act 1', 'source': ''},
        {'name': 'Instant Death Trap - BOT in the Underground Maze', 'source': ''},
        {'name': "Akutagawa Ryuunosuke's _Kappa_ _ Candid Friend", 'source': ''},
        {'name': 'Mirage Saloon Act 1', 'source': ''},
        {'name': 'Mirage Saloon Act 2', 'source': ''},
        {'name': 'Mirage Saloon Act 1 (Knuckles)', 'source': ''},
        {'name': 'Start Fanfare', 'source': ''},
        {'name': 'Back In Time', 'source': ''},
        {'name': 'Sanctuary Falls (Back in Time)', 'source': ''},
        {'name': 'BACK IN TIME ver. CYBERSPACE (Edit)', 'source': ''},
        {'name': 'Flash Train', 'source': ''},
        {'name': 'Crystal Lake', 'source': ''},
        {'name': 'Door Into Summer', 'source': ''},
        {'name': 'Gigapolis Zone (Ring Racers Mix)', 'source': ''},
        {'name': 'Thrashard In The Cave (Arrange Ver.)', 'source': ''},
        {'name': 'The Lake', 'source': ''},
        {'name': 'Collision Chaos (Present) [JP_PAL]', 'source': ''},
        {'name': 'Collision Chaos (Present) [US]', 'source': ''},
        {'name': 'Evening Star', 'source': ''},
        {'name': 'Emerald Hill Zone', 'source': ''},
        {'name': 'Emerald Hill Zone 2-Player Mode', 'source': ''},
        {'name': 'Actions in the Lower World', 'source': ''},
        {'name': 'Under Construction_ Complete Ver', 'source': ''},
        {'name': 'Leave it (_Take it!_ Re-Edit)', 'source': ''},
        {'name': "It's Gonna Happen (Gust Planet Zone Act 1)", 'source': ''},
        {'name': 'Treacle (Gust Planet Zone Act 3)', 'source': ''},
        {'name': 'Mystic Cave Zone (YM6212 Rearranged)', 'source': ''},
        {'name': 'Mystic Cave Zone', 'source': ''},
        {'name': 'Mystic Cave (Player 2)', 'source': ''},
        {'name': 'When We Reach For You -Could It Be Right-_ (Track A)',
         'source': ''},
        {'name': 'When We Reach For You -Could It Be Right-_ (Track B)',
         'source': ''},
        {'name': 'Saturn Start-Up Jingle [JP]', 'source': ''},
        {'name': 'Opening (US)', 'source': ''},
        {'name': 'Electoria', 'source': ''},
        {'name': 'Up And Forward', 'source': ''},
        {'name': 'Hill Top Zone (Alternate)', 'source': ''},
        {'name': '[Alternate] Marble Garden Zone Act 1', 'source': ''},
        {'name': 'Marble Garden Zone Act 2', 'source': ''},
        {'name': '[Alternate] Marble Garden Zone Act 2', 'source': ''},
        {'name': 'Fight and Flight (DE Ver.)', 'source': ''},
        {'name': "Frost Man's Stage (SEGA Genesis Remix)", 'source': ''},
        {'name': '[Alternate] Launch Base Zone Act 1', 'source': ''},
        {'name': 'Launch Base Zone Act 1', 'source': ''},
        {'name': 'Launch Base Zone Act 1 - Remastered', 'source': ''},
        {'name': 'Mystique Part Three', 'source': ''},
        {'name': 'With Great Intensity', 'source': ''},
        {'name': 'Track 10', 'source': ''},
        {'name': 'Voltage Drop', 'source': ''}
    ],
    [ # Disc 3
        {'name': 'Azure Lake', 'source': ''},
        {'name': 'Balloon Park', 'source': ''},
        {'name': 'Chrome Gadget', 'source': ''},
        {'name': 'Desert Palace', 'source': ''},
        {'name': 'Endless Mine', 'source': ''},
        {'name': 'Scorian Cant Zone', 'source': ''},
        {'name': 'Sprawling Shipyard', 'source': ''},
        {'name': 'UFO Smasher', 'source': ''},
        {'name': 'Hi-Spec Robo Go', 'source': ''},
        {'name': 'Crossing Venom Valley', 'source': ''},
        {'name': 'Tabloid Jargon', 'source': ''},
        {'name': 'Gumball Machine (Remix)', 'source': ''},
        {'name': 'Escape from the City (Arrange) (Track A)', 'source': ''},
        {'name': 'Escape from the City (Arrange) (Track B)', 'source': ''},
        {'name': "It Doesn't Matter (Ring Racers Cover)", 'source': ''},
        {'name': 'Bismuth Chambers', 'source': ''},
        {'name': "I'm a Spy", 'source': ''},
        {'name': 'Palmtree Panic (Present) [JP_PAL]', 'source': ''},
        {'name': 'Palmtree Panic (Present) [US]', 'source': ''},
        {'name': 'Empyrean Emerald Zone (Present)', 'source': ''},
        {'name': 'Stage 70 (Arranged)', 'source': ''},
        {'name': 'Scarlet Rose', 'source': ''},
        {'name': 'Green Hill Zone Remix', 'source': ''},
        {'name': 'Star Light Zone (Bad Future)', 'source': ''},
        {'name': 'Museum', 'source': ''},
        {'name': 'Track 2', 'source': ''},
        {'name': 'Mecha Factory', 'source': ''},
        {'name': 'Metropolis Zone', 'source': 'altmusic.pk3'},
        {'name': 'Cyan Sunset', 'source': ''},
        {'name': 'Dark Moon Castle', 'source': ''},
        {'name': 'Convert', 'source': ''},
        {'name': 'dream in blue water', 'source': ''},
        {'name': 'Kartophobia', 'source': ''},
        {'name': "You've Got to Eat Your Vegetables!!", 'source': ''},
        {'name': '[Alternate] Hydrocity Zone Act 2', 'source': ''},
        {'name': 'Hydropolis Act 2', 'source': ''},
        {'name': 'Hydrocity Zone Act 2', 'source': ''},
        {'name': 'fruitbat', 'source': ''},
        {'name': 'Crowded Grove', 'source': ''},
        {'name': 'Metropolis Zone', 'source': 'music.pk3'},
        {'name': '_Keep it Moving!__ Trap Tower Remix', 'source': ''},
        {'name': 'Diamond Dust Zone Act 1 (Genesis)', 'source': ''},
        {'name': 'Diamond Dust Zone Act 2 (Saturn)', 'source': ''},
        {'name': 'Tie a Link of ARCUS!', 'source': ''},
        {'name': 'Tie a Link of ARCUS! (Super Arrange)', 'source': ''},
        {'name': 'Speed Highway (KB Remix)', 'source': ''},
        {'name': "Goin' Down!_ (KB Remix)", 'source': ''},
        {'name': 'Capsaicin Blues', 'source': ''},
        {'name': 'tuulenvire', 'source': ''},
        {'name': 'Carnival Night Zone Act 2 - Remastered', 'source': ''},
        {'name': '[Alternate] Carnival Night Zone Act 2', 'source': ''},
        {'name': 'Carnival Night Zone Act 1 - Remastered', 'source': ''},
        {'name': 'Pluto', 'source': ''},
        {'name': 'Dark Fortress Zone', 'source': ''},
        {'name': 'Scarab of Glory No. 1', 'source': ''},
        {'name': 'Spring Yard Zone Act 1', 'source': ''},
        {'name': 'Labyrinth Soul', 'source': ''},
        {'name': 'Bust A Move! - Natsuki side -', 'source': ''},
        {'name': 'Lucky Lounge', 'source': ''},
        {'name': 'Red Barrage Area', 'source': ''},
        {'name': 'Bad Taste Aquarium', 'source': ''},
        {'name': 'Sky Sanctuary Zone (SEGA Genesis Remix)', 'source': ''},
        {'name': 'Trespasser', 'source': ''},
        {'name': 'DEATHEGG (Act 1 & 2 Mix)', 'source': ''},
        {'name': 'Space Trip Steps', 'source': ''},
        {'name': 'Last Area', 'source': ''},
        {'name': 'Dew Drop', 'source': ''}
    ],
    [ # Disc 4
        {'name': 'Jibun REST@RT (Edit)', 'source': ''},
        {'name': 'Exclusive Coupe', 'source': ''},
        {'name': 'Duel 1 R', 'source': ''},
        {'name': 'Smart Systems', 'source': ''},
        {'name': 'Sunset Hill Zone Act 1 (16 bit Remix)', 'source': ''},
        {'name': "Tails' Lab (Remix)", 'source': ''},
        {'name': 'Power Plant', 'source': ''},
        {'name': 'Savannah Citadel (Day)', 'source': ''},
        {'name': 'With Light Steps', 'source': ''},
        {'name': 'Searching (Edit)', 'source': ''},
        {'name': 'Queen of Rose II', 'source': ''},
        {'name': "Strollin' the City", 'source': ''},
        {'name': 'Indigo HELiX (Central02)', 'source': ''},
        {'name': 'Special Stage [Perfect Mix]', 'source': ''},
        {'name': 'YO-KAI Disco (Meikai Arrange Version)', 'source': ''},
        {'name': 'Aurora Atoll Zone (Ring Racers Mix)', 'source': ''},
        {'name': "Let's Go Away (Daytona International Speedway) (Edit)",
         'source': ''},
        {'name': 'Turquoise Hill Zone (YM2612 + SN76489 Arrange)', 'source': ''},
        {'name': "Shawn's Got The Shotgun", 'source': ''},
        {'name': "At Doom's Gate", 'source': ''},
        {'name': 'home stay', 'source': ''},
        {'name': 'Dungeon 1 (v2)', 'source': ''},
        {'name': 'Edenic Green Plus', 'source': ''},
        {'name': 'Ice Paradise Act 1 (Remastered)', 'source': ''},
        {'name': 'Network Transfer', 'source': ''},
        {'name': 'The Fate of the Fairies (Arrangement)', 'source': ''},
        {'name': 'SUBURB - Armored Green (Stage2)', 'source': ''},
        {'name': 'Chao Garden (Dark)', 'source': ''},
        {'name': 'Chao Garden (Hero)', 'source': ''},
        {'name': 'Move Out, Dust Chute Transformation Goraigo Mobilize!',
         'source': ''},
        {'name': 'Continuation of the Dream (Yume no Tsuzuki)', 'source': ''},
        {'name': 'Canyon Ride Act 2', 'source': ''},
        {'name': 'Gust of Wind', 'source': ''},
        {'name': 'Ice Brain (YM2612 Cover)', 'source': ''},
        {'name': 'Phantom Razor (Cytus II Edit)', 'source': ''},
        {'name': 'Ocean Rain', 'source': ''},
        {'name': 'Mazy Metroplex', 'source': ''},
        {'name': 'Green Hill Zone [8-bit]', 'source': ''},
        {'name': 'Bridge Zone Classic (Remix)', 'source': ''},
        {'name': 'Lava Reef Act 1 (1994 Album Remake)', 'source': ''},
        {'name': 'Lava Reef Zone (16-Bit)', 'source': ''},
        {'name': '_Frozen Paradise_ - Ice Cap Zone Act 1 Remix', 'source': ''},
        {'name': '_MEGA_ Scrap Brain Zone (Remix)', 'source': ''},
        {'name': 'Emerald Beach (Cover)', 'source': ''},
        {'name': 'Atlantic Criminal _ Labyrinth Zone (Remix)', 'source': ''},
        {'name': 'Special Stage - 80s Cover', 'source': ''},
        {'name': 'Special Stage (Sonic 3 & Knuckles Mix)', 'source': ''},
        {'name': 'Dimension Heist (Remix)', 'source': ''},
        {'name': 'Dimension Heist', 'source': ''},
        {'name': 'Rock the Blue Sphere!', 'source': ''}
    ],
    [ # Disc 5
        {'name': 'Lotus (Arrangement)', 'source': ''},
        {'name': 'Blood Drain -Again-', 'source': ''},
        {'name': 'Right There, Ride On (Edit)', 'source': ''},
        {'name': "Tyr's Stage (Fully Armored)", 'source': ''},
        {'name': 'Endless Mine Zone Act 2', 'source': ''},
        {'name': 'seen an angel', 'source': ''},
        {'name': 'Toy Kingdom Act 1 (Remastered)', 'source': ''},
        {'name': 'Killing Moon (Arranged)', 'source': ''},
        {'name': 'Quartz Quadrant Zone (Present) [JP _ PAL]', 'source': ''},
        {'name': 'Quartz Quadrant Zone (Present) [US]', 'source': ''},
        {'name': 'Aqua Tunnel 1', 'source': ''},
        {'name': 'Aqua Tunnel 2', 'source': ''},
        {'name': 'Back 2 Back', 'source': ''},
        {'name': 'Final Fall Act 2 (Unused)', 'source': ''},
        {'name': 'Blood Pain II', 'source': ''},
        {'name': 'Battle B2 (Boss Battle Theme)', 'source': ''},
        {'name': 'Haunted Ship (Act 1 & 2 Mix) Remastered', 'source': ''},
        {'name': 'Robotnik Winter Act 2', 'source': ''},
        {'name': 'Sewage Base Act 1', 'source': ''},
        {'name': 'gara[g]e', 'source': ''},
        {'name': 'Desert Area', 'source': ''},
        {'name': 'Blizzard Peaks Act 1', 'source': ''},
        {'name': 'The Crowd Goes Home', 'source': ''},
        {'name': 'ESP Overload', 'source': ''},
        {'name': 'Justice OR Voice (Instrumental)', 'source': ''},
        {'name': 'Cloaca Maxima', 'source': ''},
        {'name': "Satan's Theme", 'source': ''},
        {'name': 'Game Planet Starlight', 'source': ''},
        {'name': 'Monkey Mall', 'source': ''},
        {'name': 'Night Drips on Banana Leaves', 'source': ''},
        {'name': 'Game of Blades', 'source': ''},
        {'name': 'Gambling Turntable', 'source': ''},
        {'name': 'Sophisticated Fight', 'source': ''},
        {'name': 'The Praise (God In His Hand)', 'source': ''},
        {'name': 'Underground Hug', 'source': ''},
        {'name': "Agonizer's Return", 'source': ''},
        {'name': 'Massive X', 'source': ''},
        {'name': 'Neon Nights (LIGHTS UP EVOLUTION MIX) (Track A)', 'source': ''},
        {'name': 'Neon Nights (LIGHTS UP EVOLUTION MIX) (Track B)', 'source': ''},
        {'name': 'The Flutter VS The Gesellschaft', 'source': ''},
        {'name': 'ANCIENT CLOUDS', 'source': ''},
        {'name': 'Collision Chaos (Good Future) [JP_PAL]', 'source': ''},
        {'name': 'Collision Chaos (Good Future) [US]', 'source': ''},
        {'name': '_MEGA_ Star Light Zone (Remix)', 'source': ''},
        {'name': '_MEGA_ Sandopolis Zone (Remix)', 'source': ''},
        {'name': 'Aqua Lake (_Saturn_ Remix)', 'source': ''},
        {'name': 'Flying Battery Zone (8-bit version)', 'source': ''},
        {'name': "Marble Zone '12", 'source': ''},
        {'name': 'Sky Babylon (Act 1 & 2 Mix)', 'source': ''},
        {'name': 'Shooting Star', 'source': ''},
        {'name': 'Exotic AMATSU', 'source': ''},
        {'name': 'Stage 6', 'source': ''},
        {'name': 'Tsuihashi', 'source': ''},
        {'name': 'What U Need', 'source': ''},
        {'name': 'Vertigo (Stage 5)', 'source': ''},
        {'name': 'Anatat Tatanatat', 'source': ''}
    ],
    [ # Disc 6
        {'name': 'Midnight Freeze Zone', 'source': ''},
        {'name': "Hol Horse's Theme", 'source': ''},
        {'name': 'AINT NOTHING LIKE A FUNKY BEAT', 'source': ''},
        {'name': 'Snowboard Race', 'source': ''},
        {'name': 'End This Hate', 'source': ''},
        {'name': 'Meadow Match Zone', 'source': ''},
        {'name': "Mega Man X_ Armored Armadillo's Stage (Arranged)", 'source': ''},
        {'name': 'DN Bass (Track 11)', 'source': ''},
        {'name': 'Blizzard Peaks (Act 1 & 2 Mix)', 'source': ''},
        {'name': '[Alternate] Launch Base Zone Act 2', 'source': ''},
        {'name': "Al's Toy Barn", 'source': ''},
        {'name': "Khan's Theme", 'source': ''},
        {'name': "Zena-Lan's Stage (Fully Armored)", 'source': ''},
        {'name': 'Aqualung Zone (Ring Racers Mix)', 'source': ''},
        {'name': 'Menu Theme', 'source': ''},
        {'name': 'WRONG GAME_ WRONG GAME!', 'source': ''},
        {'name': 'Phantom Ruby Ambience', 'source': ''},
        {'name': 'A Journey in Modulating Time (Track A)', 'source': ''},
        {'name': 'A Journey in Modulating Time (Track B)', 'source': ''},
        {'name': 'Back Alley Clash', 'source': ''},
        {'name': 'Loser Club', 'source': ''},
        {'name': 'Qualified, Set, GO!', 'source': ''},
        {'name': 'worldsbe.st', 'source': ''},
        {'name': 'Hidden Palace Zone (Ring Racers Mix)', 'source': ''},
        {'name': 'Whisk Assessment', 'source': ''},
        {'name': 'Get That Guy Outta Here', 'source': ''},
        {'name': 'The Lacustrine Beat Machine', 'source': ''},
        {'name': 'Out Of Reach', 'source': ''},
        {'name': 'Retire', 'source': ''},
        {'name': 'Continue', 'source': ''}
    ]
]

def signal_handler(sig, frame):
    print('\nCancelled')
    # Perform any cleanup here
    sys.exit(0)

def get_track_number(file_name):
    for i in range(0, len(album_order)):
        for j in range(0, len(album_order[i])):
            if album_order[i][j]['name'] == file_name and addon.endswith(album_order[i][j]['source']):
                return {'disc': i+1, 'track': j+1}
    return None


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

def valid_positive_int(value):
    ivalue = int(value)
    if ivalue < 1:
        raise argparse.ArgumentTypeError(f"Invalid value: {value}. The value must be an integer greater than or equal to 1.")
    return ivalue

if __name__ == "__main__":
    signal.signal(signal.SIGINT, signal_handler)
    parser = argparse.ArgumentParser(description="Extract music from a PK3 file.")
    
    # Mandatory arguments
    parser.add_argument('addon', type=str, help='The PK3 file (music.pk3 or altmusic.pk3)')
    parser.add_argument('output_location', type=str, help='The location to output the extracted music')
    
    # Optional arguments
    parser.add_argument('-d', '--dry-run', action='store_true', help='Skip outputting any files (default: False)')
    parser.add_argument('-e', '--encore', action='store_true', help='Output Encore Mode Tuning (default: False)')
    parser.add_argument('-f', '--file-type', type=str, default='mp3', help='Specify the output file type (default: mp3)')
    parser.add_argument('-l', '--loop-count', type=valid_positive_int, default=1, help='Number of times the song loops (default: 1)')
    parser.add_argument('-n', '--no-fade', action='store_true', help='Skip fade out at end of song (default: False)')
    parser.add_argument('-o', '--original-volume', action='store_true', help='Skip game defined volume adjustments and output at source volume (default: False)')
    parser.add_argument('-v', '--verbose', action='store_true', help='Show more detailed logs (default: False)')
    
    args = parser.parse_args()

    # Now you can access the arguments using args
    addon = args.addon
    output_location = args.output_location
    encore_mode = args.encore
    no_fade = args.no_fade
    original_volume = args.original_volume
    file_type = args.file_type if args.file_type.startswith('.') else "." + args.file_type
    loop_count = args.loop_count
    verbose = args.verbose
    dry = args.dry_run

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
            progress = 1
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
                        if not dry:
                            output.write(binary)
                        for key in songs.keys():
                            parts = fname.split("O_")
                            if parts[len(parts)-1].lower() == key+fext:
                                song_name = os.path.join(output_location, key + file_type)
                                sanitized_name = key
                                volume = 1
                                title = ""
                                artist = ""
                                track = ""
                                track_num = ""
                                disc_num = ""
                                order_prefix = ""
                                release_date = "2024-04-24T05:47:00-05:00"
                                fade_length = "10" 
                                if no_fade:
                                    fade_length = "0"
                                if "track" in songs[key]:
                                    track = f' (Track {songs[key]["track"]})'
                                if "title" in songs[key]:
                                    sanitized_name = sanitize_filename(songs[key]["title"] + track)
                                    order = get_track_number(sanitized_name)
                                    if not order == None:
                                        track_num = order["track"]
                                        disc_num = order["disc"]
                                        order_prefix = f'{disc_num}-{track_num} '
                                    song_name = os.path.join(output_location, order_prefix + sanitized_name + track + file_type)
                                    title = songs[key]["title"] + track
                                if "volume" in songs[key] and not original_volume:
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
                                        "-l", f'{loop_count}',
                                        "-f", fade_length,
                                        os.path.join(output_location, "tmp" + fext)
                                ]
                                command2 = [
                                        "ffprobe",
                                        "-v", "error",
                                        "-select_streams", "a:0",
                                        "-show_entries", "stream=sample_rate",
                                        "-of", "default=noprint_wrappers=1:nokey=1",
                                        os.path.join(output_location, "tmp.wav")
                                ]
                                if verbose:
                                    cols = shutil.get_terminal_size().columns
                                    print("=" * cols)
                                print(f'[{progress}/{len(music_list)}]','Converting: \t', fparts[0]+fext, '=>', song_name)
                                progress+=1
                                if verbose:
                                    print(key, json.dumps(songs[key], indent=4))
                                if dry:
                                    continue
                                try:
                                    if verbose:
                                        print("Running: \t", ' '.join(command1))
                                    subprocess.run(command1, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                                    if verbose:
                                        print("Running: \t", ' '.join(command2))
                                    result = subprocess.run(command2, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
                                    sample_rate = result.stdout.strip()
                                    if verbose:
                                        print("Sample Rate: \t", sample_rate)
                                    asetrate = f',asetrate={sample_rate}*{encore_sample_rate_multiplier}' if encore_mode else ''
                                    command3 = [
                                            "ffmpeg",
                                            "-i", os.path.join(output_location, "tmp.wav"),
                                            "-metadata", f'title={title}',
                                            "-metadata", f'artist={artist}',
                                            "-metadata", f'track={track_num}',
                                            "-metadata", f'disc={disc_num}',
                                            "-metadata", f'date={release_date}',
                                            "-metadata", f'album_artist=Kart Krew',
                                            "-metadata", f'album=Dr. Robotnik\'s Ring Racers',
                                            "-filter:a", f'volume={volume}{asetrate}',
                                            "-y",
                                            "-q:a", "0",
                                            song_name
                                    ]
                                    if verbose:
                                        print("Running: \t", ' '.join(command3))
                                    subprocess.run(command3, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                                    os.remove(os.path.join(output_location, "tmp.wav"))
                                    if verbose:
                                        print('done')
                                except Exception as e:
                                    print('Error: ', "Could not convert with vgmstream-cli")
                                    print('Warning: ',"Falling back to ffmpeg")
                                    try:
                                        command2 = [
                                                "ffprobe",
                                                "-v", "error",
                                                "-select_streams", "a:0",
                                                "-show_entries", "stream=sample_rate",
                                                "-of", "default=noprint_wrappers=1:nokey=1",
                                                os.path.join(output_location, "tmp"+fext)
                                        ]
                                        if verbose:
                                            print("Running: \t", ' '.join(command2))
                                        result = subprocess.run(command2, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
                                        sample_rate = result.stdout.strip()
                                        if verbose:
                                            print("Sample Rate: \t", sample_rate)
                                        asetrate = f',asetrate={sample_rate}*{encore_sample_rate_multiplier}' if encore_mode else ''
                                        # print("Sample Rate:", sample_rate)
                                        command3 = [
                                                "ffmpeg",
                                                "-i", os.path.join(output_location, "tmp"+fext),
                                                "-metadata", f'title={title}',
                                                "-metadata", f'artist={artist}',
                                                "-metadata", f'track={track_num}',
                                                "-metadata", f'disc={disc_num}',
                                                "-metadata", f'date={release_date}',
                                                "-metadata", f'album_artist=Kart Krew',
                                                "-metadata", f'album=Dr. Robotnik\'s Ring Racers',
                                                "-filter:a", f'volume={volume}{asetrate}',
                                                "-y",
                                                "-q:a", "0",
                                                song_name
                                        ]
                                        if verbose:
                                            print("Running: \t", ' '.join(command3))
                                        subprocess.run(command3, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                                        if verbose:
                                            print('done')
                                    except:
                                        print('Error: \t', 'Could not convert with ffmpeg. Exiting program')
                                        sys.exit(0)
                                # break

                    os.remove(os.path.join(output_location, "tmp"+fext))
