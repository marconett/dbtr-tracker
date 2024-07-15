#!/usr/bin/python3

import sys
import glob
import json
import pprint
import uuid
import re
import argparse
from pathlib import Path, PureWindowsPath

pp = pprint.PrettyPrinter(indent=4, width=100)

WEAPONS = [
  'rogue_blaster',
  'rogue_crossbow',
  'rogue_egun',
  'rogue_heavymachinegun',
  'rogue_heavysniper',
  'rogue_machinegun',
  'rogue_rocketlauncher',
  'rogue_shaft',
  'rogue_submachinegun',
  'rogue_supershotgun',
  'rogue_revolver',
  'rogue_grenadelauncher',

  # secondaries
  'rogue_revolver_secondary',
  'rogue_voidcannon_secondary',
  'rogue_rocketlauncher_secondary',
  'rogue_blaster_secondary',
  'rogue_grenadelauncher_secondary',

  # referenced but not in the game yet
  'rogue_voidcannon',
  'rogue_hammerswing',
  'rogue_left_hand',
  'rogue_doublebarreled_shotgun',
  'rogue_bow',
  'rogue_pistol',
  'rogue_pncr',
  'rogue_sword',
  'rogue_tommygun',
  'arena_left_hand',
  'fists',
]

# DENYLIST = [
# ]

class bcolors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'

def line_starts_with_any(prefixes, line):
    for prefix in prefixes:
        if line.startswith(prefix):
            return True
    return False

def create_asset_json(src_dir, dst_dir):
    data = []
    # data = {}
    # can't do keyed objects because there are 60 duplicate asset_names :(

    for file in glob.iglob('./' + str(src_dir) + '/**/*.weapon', recursive=True):
        data = data + parse_assets(file)
        # data.update(parse_assets(file))

    # data = [d for d in data if d.get('weapon_id') not in DENYLIST]

    with open('./' + str(dst_dir) + '/weapons.json', 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

    # with open('./' + str(dst_dir) + '/weapons.min.json', 'w', encoding='utf-8') as f:
    #     json.dump(data, f, ensure_ascii=False)

    # for a in data:
    #     pp.pprint(a['asset_name'])

    # pp.pprint(data)
    # print(len(data))

def parse_assets(file):
    print(f'processing {file} ...')

    assets = []
    # assets = {}
    current_asset = None
    current_dynamic_rule = None

    with open(file, 'r') as file_object:
        lines = list(line.strip() for line in file_object) # all lines
        lines = list(line for line in lines if line) # filter blank lines
        lines = list(line for line in lines if not line.startswith('/')) # filter comments
        lines = list(re.sub(' +', ' ', line) for line in lines) # replace multi whitespaces
        lines = list(re.sub(' +', ' ', line) for line in lines) # replace multi whitespaces
        lines = list(re.sub('\t+', ' ', line) for line in lines) # replace tabs
        lines = list(re.sub('\u00A8', '', line) for line in lines) # remove ¨
        lines = list(re.sub('\u00A7', '', line) for line in lines) # remove §
        lines = list(line for line in lines if line) # filter blank lines

        for i, l in enumerate(lines):
            line = l.strip()
            next_line = None
            previous_line = None

            # print(line)
            # continue

            if i+1 < len(lines):
                next_line = lines[i+1].strip()

            if i > 1:
                previous_line = lines[i-1].strip()

            if line_starts_with_any(WEAPONS, line):

                if not next_line.startswith('{'):
                    print(f"{bcolors.FAIL}Error: asset next line is not bracket on line {i} in {file} {bcolors.ENDC}")
                    exit(1)

                weapon_id = line.split(' ')[0]
                weapon_type = line.split(' ')[1] if 1 < len(line.split(' ')) else "base"
                augment_id = line.split(' ')[2] if 2 < len(line.split(' ')) else ""
                parent_id = ""

                # is augment
                if augment_id != "":
                  parent_id = weapon_id
                  weapon_id = augment_id

                current_asset = {
                    'id': weapon_id,
                    'parent_id': parent_id,
                    'weapon_type': weapon_type,
                }

            elif line.startswith('{'):
                if previous_line and ((not line_starts_with_any(WEAPONS, previous_line)) and (not previous_line.startswith('dynamic_rule'))):
                    print(f"{bcolors.WARNING}WARNING: opening bracket without a top level context on line {i} in {file} {bcolors.ENDC}")
                    if current_asset is not None:
                        print(f"{bcolors.WARNING}assuming new dynamic_rule{bcolors.ENDC}")
                        current_dynamic_rule = {
                            'conditions': []
                        }
                    else:
                        name = str(uuid.uuid4())
                        print(f"{bcolors.WARNING}assuming new asset with random name {name}{bcolors.ENDC}")
                        current_asset = {
                            'asset_name': name,
                            'dynamic_rules': []
                        }

                if not previous_line and current_asset is None:
                    name = str(uuid.uuid4())
                    print(f"{bcolors.WARNING}WARNING: opening bracket without a top level context on line {i} in {file} {bcolors.ENDC}")
                    print(f"{bcolors.WARNING}assuming new asset with random name {name}{bcolors.ENDC}")
                    current_asset = {
                        'asset_name': name,
                        'dynamic_rules': []
                    }

                continue

            # work around syntax error in some files
            elif line.startswith('xmin'):
                continue

            elif line.startswith('}'):
                if current_dynamic_rule is not None:
                    current_asset['dynamic_rules'].append(current_dynamic_rule)
                    current_dynamic_rule = None
                elif current_asset is not None:
                    assets.append(current_asset)
                    # assets[current_asset['asset_name']] = current_asset
                    current_asset = None
                elif i+1 == len(lines):
                    print(f"{bcolors.WARNING}WARNING: couldn't match closing bracket on last line in (ignoring) {file} {bcolors.ENDC}")
                else:
                    print(f"{bcolors.FAIL}Error: couldn't match closing bracket on line {i} in {file} {bcolors.ENDC}")
                    exit(1)

            # any other line apart from the structure ones
            else:
                key = line.split(' ', 1)[0]

                if len(line.split(' ', 1)) == 1:
                    print(f"{bcolors.WARNING}WARNING: key without a value, ignoring line {i} {file} {bcolors.ENDC}")
                    continue
                else:
                    value = line.split(' ', 1)[1]

                    if len(value.split(' ', 1)) > 1:
                        value = value.split(' ')

                if key == 'dynamic_dimensions':
                    value = {
                        'xmin': value.split(' ')[0],
                        'ymin': value.split(' ')[1],
                        'zmin': value.split(' ')[2],
                        'xmax': value.split(' ')[3],
                        'ymax': value.split(' ')[4],
                        'zmax': value.split(' ')[5],
                    }

                if current_dynamic_rule is not None:
                    if key == 'if':
                        current_dynamic_rule['conditions'].append(value)
                    elif key == 'select':
                        current_dynamic_rule['select'] = value.split(',')
                    elif key == 'pick':
                        current_dynamic_rule['pick'] = value.split(',')
                    else:
                        current_dynamic_rule[key] = value
                elif current_asset is not None:
                    current_asset[key] = value

            # print(f"{i}\t{line}")

    # if there's still open contexts, close them
    if current_dynamic_rule is not None:
        current_asset['dynamic_rules'].append(current_dynamic_rule)
        current_dynamic_rule = None

    if current_asset is not None:
        assets.append(current_asset)
        # assets[current_asset['asset_name']] = current_asset
        current_asset = None

    return assets

if __name__ == '__main__':
    parser = argparse.ArgumentParser(prog='weapon-parser.py', description='.weapon file parser for Diabotical')
    parser.add_argument('src_directory', type=Path, help="this directory will be recursively searched for .weapon files")
    parser.add_argument('dest_directory', type=Path, help="put the resulting json into this directory")

    if len(sys.argv)==1:
        parser.print_help(sys.stderr)
        sys.exit(1)

    args = parser.parse_args()

    create_asset_json(args.src_directory, args.dest_directory)