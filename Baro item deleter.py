import xml.etree.ElementTree as ET
import gzip
import shutil
from pathlib import Path
import logging
from tqdm import tqdm
from time import perf_counter

# Prompt user for input file and remove quotes if they were added by dragging and dropping the file into the window
submarine_input = Path(input("Drag and drop .sub file into this window to quickly and easily specify it's location and filename: "))
if str(submarine_input).startswith("'") or str(submarine_input).startswith('"'):
    submarine_input = Path(str(submarine_input)[1:-1])
if str(submarine_input).endswith("'") or str(submarine_input).endswith('"'):
    submarine_input = Path(str(submarine_input)[:-1])

# Check if the user has already acknowledged the warning
if not Path('warningacknowledged').exists():
    warninginput = input("\nWARNING: While the program won't delete or mess with the input submarine file, "
                         "It will create a new file with the same name, but with '(no items)' appended to the end. "
                         "If a file with the same name already exists, It will delete that file before creating the new one. "
                         "The program works by recursively scanning for items in containers, "
                         "and items that are inside those items, and so on, until it can't find any more items. "
                         "While it is limited to certain container types, I cannot guarantee that it won't delete anything important."
                         "\n\nWrite 'yes' to acknowledge and dissmiss this warning: ")

    if warninginput.lower() == 'yes':
        Path('warningacknowledged').touch()
    else:
        input("'yes' was not written, press enter to exit.")
        exit()

# Start timer
start = perf_counter()

# Set up logging
logging.basicConfig(filename='BaroItemDeleter1.txt', filemode='w', level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Define list of containers and items that the program will recursively search for items in
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


# Recursively search for items in containers, and items that are inside those items, and so on, until it can't find any more items
# TODO: Add something to check and stop an infinite loop?
def recursive_search(item_id, items):
    recursive_ids = []
    for child in root.findall('Item'):
        if 'ID' in child.attrib:
            if child.attrib['ID'] == item_id:
                # Let the user know what item is being scanned
                # TODO: Currently tqdm keeps making the progress bar jump around depending on the length of the item ID
                items.set_description(f'Scanning {child.attrib["identifier"]}')
                for container in child:
                    if container.tag == 'ItemContainer':
                        # Log the container and its contained items. If it has no contained items, log that instead
                        logging.info(f'Found container: {child.attrib["identifier"]} '
                                     f'with item IDs: {container.attrib["contained"] if container.attrib["contained"] else "None"} '
                                     f'from item with ID: {item_id}')
                        inspection_ids = container.attrib['contained'].split(',')
                        for item in inspection_ids:
                            # If there are no items in the container, skip it
                            if item == '':
                                continue
                            # If there are multiple items in the container, split them up and add them to the recursive search list
                            if ';' in item:
                                recursive_ids.extend(item.split(';'))
                                item_ids.extend(item.split(';'))
                            # If there is only one item in the container, add it to the recursive search list
                            else:
                                recursive_ids.append(item)
                                item_ids.append(item)

                        # If there are items in the container, recursively search them for more items
                        for item in recursive_ids:
                            recursive_search(item, items)


# Check if a .xml file with the same name as the input .sub file already exists, and delete it if it does
if Path(submarine_input.parent / (f'{submarine_input.stem}.xml')).exists():
    logging.info('Deleting already existing file')
    print('Deleting already existing file')
    Path(submarine_input.parent / (f'{submarine_input.stem}.xml')).unlink()

# Extract the .sub file into a .xml file
logging.info('Extracting sub file')
print('Extracting sub file')
with gzip.open(submarine_input, 'rb') as f_in:
    with open(Path(submarine_input.parent / (f'{submarine_input.stem}.xml')), 'wb') as f_out:
        shutil.copyfileobj(f_in, f_out)

tree = ET.parse(Path(submarine_input.parent / (f'{submarine_input.stem}.xml')))

root = tree.getroot()

# Iterate over all elements in the XML file and find all Item elements that is in the containers_and_items list
for child in root.iter():
    if child.tag == 'Item':
        if child.attrib['identifier'] in containers_and_items:
            for container in child:
                if container.tag == 'ItemContainer':
                    # Log the container and its contained items.
                    logging.info(f'Found container: {child.attrib["identifier"]} with item IDs: {container.attrib["contained"]}')
                    inspection_ids = container.attrib['contained'].split(',')
                    for item in inspection_ids:
                        # If there are multiple items in the container, split them up and add them to the recursive search list
                        if ';' in item:
                            item_ids.extend(item.split(';'))
                        # If there is only one item in the container, add it to the recursive search list
                        else:
                            item_ids.append(item)

# Remove empty strings from the list
# TODO: This is cursed, but it's 3:44AM right now, and I have no idea why I did it like this in the first place
item_list = [i for i in item_ids if i]

# Iterate over all items in the list and recursively search them for more items
items = tqdm(item_list)
for item in items:
    logging.info(f'Recursively searching item with ID: {item}')
    recursive_search(item, items)

# Remove empty strings from the list
# TODO: Also cursed.
final_item_list = [i for i in item_ids if i]
# Remove duplicates from the list
# TODO: Also also cursed
final_item_list = list(set(final_item_list + item_list))
final_item_list.sort()

# Once more iterate over all elements in the XML file, and delete all Item elements that have an ID that is in the final_item_list
i = 0
for child in root.findall('Item'):
    if 'ID' in child.attrib:
        if child.attrib['ID'] in final_item_list:
            root.remove(child)
            i += 1
            # Log the removed item
            logging.info(f'Removed item with ID: {child.attrib["ID"]} ({child.attrib["identifier"]})')
            print(f'Removed item with ID: {child.attrib["ID"]} ({child.attrib["identifier"]})')

# You guessed it, iterate over all elements in the XML file, but this time reset the contained attribute value of all containers we found earlier.
# I'm pretty sure the game actually handles this either automatically, or just doesn't care, but here we are
# TODO: Currently this assumes that we deleted all items in the containers. Redo this to have a list of containers that we know we deleted items from, and only reset those
logging.info('Resetting container contained values')
print('Resetting container contained values')
for child in root.iter():
    if child.tag == 'Item':
        if child.attrib['identifier'] in containers_and_items:
            for container in child:
                if container.tag == 'ItemContainer':
                    commas = container.attrib['contained'].count(',')
                    container.attrib['contained'] = ',' * commas


# Save the edited XML file
# TODO: Try/Catch this?
logging.info('Saving edited XML file')
print('Saving edited XML file')
root.attrib['name'] = f'{submarine_input.stem} (no items)'
tree.write(Path(submarine_input.parent / (f'{submarine_input.stem} (no items).xml')))

# Compress the edited XML file back into a .sub file
# TODO: Try/Catch this?
logging.info('Compressing XML file back into gzip .sub file')
print('Compressing XML file back into gzip .sub file')
with open(Path(submarine_input.parent / (f'{submarine_input.stem} (no items).xml')), 'rb') as f_in:
    with gzip.open(Path(submarine_input.parent / (f'{submarine_input.stem} (no items)')), 'wb') as f_out:
        shutil.copyfileobj(f_in, f_out)

# Check if a .sub file with the same name as the input .sub file already exists, and delete it if it does
if Path(Path(submarine_input.parent / (f'{submarine_input.stem} (no items).sub'))).exists():
    logging.info('Deleting already existing .sub file')
    print('Deleting already existing .sub file')
    Path(Path(submarine_input.parent / (f'{submarine_input.stem} (no items).sub'))).unlink()

# Rename the .sub file to have the .sub extension
logging.info('Renaming .sub file')
print('Renaming .sub file')
Path(Path(submarine_input.parent / (f'{submarine_input.stem} (no items)'))).rename(Path(submarine_input.parent / (f'{submarine_input.stem} (no items).sub')))

# Log and print how many items were removed and how long it took
logging.info(f'Removed {i} items and saved edited file. Took {perf_counter() - start} seconds.')
print(f'Removed {i} items and saved edited file. Took {perf_counter() - start} seconds.')
input('Press enter to exit.')
