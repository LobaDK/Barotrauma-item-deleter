import xml.etree.ElementTree as ET
import gzip
import shutil
from pathlib import Path
import logging
from tqdm import tqdm
from time import perf_counter

submarine_input = Path(input("Drag and drop .sub file into this window to quickly and easily specify it's location and filename: "))
if str(submarine_input).startswith("'") or str(submarine_input).startswith('"'):
    submarine_input = Path(str(submarine_input)[1:-1])
if str(submarine_input).endswith("'") or str(submarine_input).endswith('"'):
    submarine_input = Path(str(submarine_input)[:-1])

if not Path('warningacknowledged').exists():
    warninginput = input("\nWARNING: While the program won't delete or mess with any of the original files "
                         "it will recursively delete any and all items that are in containers, "
                         "and items that are inside those items, and so on, until it can't find any more items. "
                         "While it is limited to certain container types, I cannot guarantee that it won't delete anything important."
                         "\n\nWrite 'yes' to acknowledge and dissmiss this warning: ")

    if warninginput.lower() == 'yes':
        Path('warningacknowledged').touch()
    else:
        input("'yes' was not written, press enter to exit.")
        exit()

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
                        'reactor1',
                        'battery',
                        'oxygenerator',
                        'opdeco_medcompartment1',
                        'opdeco_medcompartment2',
                        'opdeco_medcompartment3',
                        'opdeco_cabinetsdorm',
                        'loosevent',
                        'opdeco_trashcan']

item_ids = []


def recursive_search(item_id, items):
    recursive_ids = []
    for child in root.findall('Item'):
        if 'ID' in child.attrib:
            if child.attrib['ID'] == item_id:
                items.set_description(f'Scanning {child.attrib["identifier"]}')
                for container in child:
                    if container.tag == 'ItemContainer':
                        logging.info(f'Found container: {child.attrib["identifier"]} '
                                     f'with item IDs: {container.attrib["contained"] if container.attrib["contained"] else "None"} '
                                     f'from item with ID: {item_id}')
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


if Path(submarine_input.parent / (f'{submarine_input.stem}.xml')).exists():
    logging.info('Deleting already existing file')
    print('Deleting already existing file')
    Path(submarine_input.parent / (f'{submarine_input.stem}.xml')).unlink()

logging.info('Extracting sub file')
print('Extracting sub file')
with gzip.open(submarine_input, 'rb') as f_in:
    with open(Path(submarine_input.parent / (f'{submarine_input.stem}.xml')), 'wb') as f_out:
        shutil.copyfileobj(f_in, f_out)

tree = ET.parse(Path(submarine_input.parent / (f'{submarine_input.stem}.xml')))

root = tree.getroot()

for child in root.iter():
    if child.tag == 'Item':
        if child.attrib['identifier'] in containers_and_items:
            for container in child:
                if container.tag == 'ItemContainer':
                    logging.info(f'Found container: {child.attrib["identifier"]} with item IDs: {container.attrib["contained"]}')
                    inspection_ids = container.attrib['contained'].split(',')
                    for item in inspection_ids:
                        if ';' in item:
                            item_ids.extend(item.split(';'))
                        else:
                            item_ids.append(item)

item_list = [i for i in item_ids if i]

items = tqdm(item_list)
for item in items:
    logging.info(f'Recursively searching item with ID: {item}')
    recursive_search(item, items)

final_item_list = [i for i in item_ids if i]
final_item_list = list(set(final_item_list + item_list))
final_item_list.sort()

i = 0
for child in root.findall('Item'):
    if 'ID' in child.attrib:
        if child.attrib['ID'] in final_item_list:
            root.remove(child)
            i += 1
            logging.info(f'Removed item with ID: {child.attrib["ID"]} ({child.attrib["identifier"]})')
            print(f'Removed item with ID: {child.attrib["ID"]} ({child.attrib["identifier"]})')

logging.info('Resetting container contained values')
print('Resetting container contained values')
for child in root.iter():
    if child.tag == 'Item':
        if child.attrib['identifier'] in containers_and_items:
            for container in child:
                if container.tag == 'ItemContainer':
                    commas = container.attrib['contained'].count(',')
                    container.attrib['contained'] = ',' * commas


logging.info('Saving edited XML file')
print('Saving edited XML file')
root.attrib['name'] = f'{submarine_input.stem} (no items)'
tree.write(Path(submarine_input.parent / (f'{submarine_input.stem} (no items).xml')))

logging.info('Compressing XML file back into gzip .sub file')
print('Compressing XML file back into gzip .sub file')
with open(Path(submarine_input.parent / (f'{submarine_input.stem} (no items).xml')), 'rb') as f_in:
    with gzip.open(Path(submarine_input.parent / (f'{submarine_input.stem} (no items)')), 'wb') as f_out:
        shutil.copyfileobj(f_in, f_out)

if Path(Path(submarine_input.parent / (f'{submarine_input.stem} (no items).sub'))).exists():
    logging.info('Deleting already existing .sub file')
    print('Deleting already existing .sub file')
    Path(Path(submarine_input.parent / (f'{submarine_input.stem} (no items).sub'))).unlink()

logging.info('Renaming .sub file')
print('Renaming .sub file')
Path(Path(submarine_input.parent / (f'{submarine_input.stem} (no items)'))).rename(Path(submarine_input.parent / (f'{submarine_input.stem} (no items).sub')))

logging.info(f'Removed {i} items and saved edited file. Took {perf_counter() - start} seconds.')
print(f'Removed {i} items and saved edited file. Took {perf_counter() - start} seconds.')
input('Press enter to exit.')
