import xml.etree.ElementTree as ET
import gzip
import shutil
from pathlib import Path
import logging
from tqdm import tqdm
from time import perf_counter

start = perf_counter()

logging.basicConfig(filename='log.txt', filemode='w', level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

containers_and_items = ['steelcabinet',
                        'mediumsteelcabinet',
                        'medcabinet',
                        'toxcabinet',
                        'suppliescabinet',
                        'crateshelf',
                        'weaponholder',
                        'securesteelcabinet',
                        'divingsuitlocker',
                        'oxygentankshelf1',
                        'oxygentankshelf2',
                        'railgunshellrack',
                        'depthchargeloader',
                        'coilgunammoshelf',
                        'flakcannonloader',
                        'railgunloader',
                        'coilgunloader',
                        'chaingunloader',
                        'pulselaserloader',
                        'outpostreactor',
                        'reactor1']

item_ids = []


def recursive_search(item_id, items):
    recursive_ids = []
    for child in root.findall('Item'):
        if 'ID' in child.attrib:
            if child.attrib['ID'] == item_id:
                items.set_description(f'Scanning {child.attrib["identifier"]}')
                for container in child:
                    if container.tag == 'ItemContainer':
                        inspection_ids = container.attrib['contained'].split(',')
                        for item in inspection_ids:
                            if item == '':
                                continue
                            if ';' in item:
                                recursive_ids.extend(item.split(';'))
                                item_ids.extend(item.split(';'))
                            else:
                                recursive_ids.append(item)
                                item_ids.append(item)

                        for item in recursive_ids:
                            recursive_search(item, items)


if Path(r'Metallicor MK1.xml').exists():
    Path(r'Metallicor MK1.xml').unlink()

with gzip.open(r'Metallicor MK1.sub', 'rb') as f_in:
    with open(r'Metallicor MK1.xml', 'wb') as f_out:
        shutil.copyfileobj(f_in, f_out)

tree = ET.parse('Metallicor MK1.xml')

root = tree.getroot()

for child in root.iter():
    if child.tag == 'Item':
        if child.attrib['identifier'] in containers_and_items:
            for container in child:
                if container.tag == 'ItemContainer':
                    inspection_ids = container.attrib['contained'].split(',')
                    for item in inspection_ids:
                        if ';' in item:
                            item_ids.extend(item.split(';'))
                        else:
                            item_ids.append(item)

item_list = [i for i in item_ids if i]

print(item_list)
print(len(item_list))

items = tqdm(item_list)
for item in items:
    items.bar_format = '{l_bar}{bar:10}| {n_fmt}/{total_fmt} [{elapsed}<{remaining}]'
    recursive_search(item, items)

final_item_list = [i for i in item_ids if i]
final_item_list = list(set(final_item_list + item_list))
final_item_list.sort()
print(final_item_list)

i = 0
for child in root.findall('Item'):
    if 'ID' in child.attrib:
        if child.attrib['ID'] in final_item_list:
            root.remove(child)
            i += 1
            logging.info(f'Removed {child.attrib["ID"]} which is {child.attrib["identifier"]}')
            print(f'Removed {child.attrib["ID"]} which is {child.attrib["identifier"]}')


for child in root.iter():
    if child.tag == 'Item':
        if child.attrib['identifier'] in containers_and_items:
            for container in child:
                if container.tag == 'ItemContainer':
                    commas = container.attrib['contained'].count(',')
                    container.attrib['contained'] = ',' * commas


tree.write('Metallicor MK1 test.xml')

with open('Metallicor MK1 test.xml', 'rb') as f_in:
    with gzip.open('Metallicor MK1 test', 'wb') as f_out:
        shutil.copyfileobj(f_in, f_out)

if Path('Metallicor MK1 test.sub').exists():
    Path('Metallicor MK1 test.sub').unlink()
Path('Metallicor MK1 test').rename('Metallicor MK1 test.sub')

print(f'Removed {i} items and saved edited file. Took {perf_counter() - start} seconds.')
