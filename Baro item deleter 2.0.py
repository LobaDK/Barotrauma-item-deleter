from pathlib import Path
from time import perf_counter
import logging
import gzip
import shutil
import xml.etree.ElementTree as ET
from json import loads
from tqdm import tqdm


def iterate_elements(elem):
    if elem.tag != 'LinkedSubmarine':  # Check if the current element is not "LinkedSubmarine". This will ignore items inside linked submarines (drones/shuttles and such)
        if elem.tag == 'Item':
            if elem.attrib['identifier'] in containers_and_items:
                for container in elem:
                    if container.tag == 'ItemContainer':
                        # Log the container and its contained items.
                        logging.info(f'Found container: {elem.attrib["identifier"]} with item IDs: {container.attrib["contained"] if any(i.isdigit() for i in container.attrib["contained"]) else "None"}')
                        inspection_ids = container.attrib['contained'].split(',')
                        for item in inspection_ids:
                            # If there are multiple items in the container, split them up and add them to the recursive search list
                            if ';' in item:
                                cleanedContainers.append(elem.attrib['ID'])
                                item_ids.extend(item.split(';'))
                            elif item == '':  # Check if the item is empty
                                continue
                            # If there is only one item in the container, add it to the recursive search list
                            else:
                                cleanedContainers.append(elem.attrib['ID'])
                                item_ids.append(item)

        # Iterate through the children elements
        for child in elem:
            iterate_elements(child)  # Recursively call the function for children


# Recursively search for items in containers, and items that are inside those items, and so on, until it can't find any more items
# TODO: Add something to check and stop an infinite loop?
def recursive_search(item_id, items):
    recursive_ids = []
    for child in root.findall('Item'):
        if 'ID' in child.attrib:
            if child.attrib['ID'] == item_id:
                # Let the user know what item is being scanned
                items.set_description(f'Scanning {child.attrib["identifier"].ljust(description_padding)}')
                for container in child:
                    if container.tag == 'ItemContainer':
                        matching_items = tree.findall(f".//*[@ID='{item_id}']")
                        item_container = matching_items[0].get('identifier')
                        # Log the container and its contained items. If it has no contained items, log that instead
                        logging.info(f'Found item IDs: {container.attrib["contained"] if any(i.isdigit() for i in container.attrib["contained"]) else "None"} '
                                     f'from {item_container} with ID: {item_id}')
                        inspection_ids = container.attrib['contained'].split(',')
                        for item in inspection_ids:
                            # If there are multiple items in the container, split them up and add them to the recursive search list
                            if ';' in item:
                                cleanedContainers.append(item_id)
                                item_ids.extend(item.split(';'))
                                recursive_ids.extend(item.split(';'))
                            # If there are no items in the container, skip it
                            if item == '':
                                continue
                            # If there is only one item in the container, add it to the recursive search list
                            else:
                                cleanedContainers.append(item_id)
                                item_ids.append(item)
                                recursive_ids.append(item)

                        # If there are items in the container, recursively search them for more items
                        for item in recursive_ids:
                            recursive_search(item, items)


def deleteItems():
    i = 0
    for item_id in item_ids:
        item = tree.findall(f".//*[@ID='{item_id}']")
        if item:
            root.remove(item[0])
            logging.info(f'Removed {item[0].get("identifier")} with ID: {item_id}')
            print(f'Removed {item[0].get("identifier")} with ID: {item_id}')
            i += 1
    return i


def cleanContainers():
    for container_id in cleanedContainers:
        container = tree.findall(f".//*[@ID='{container_id}']")
        if container:
            for child in container[0]:
                if child.tag == 'ItemContainer':
                    commas = child.attrib['contained'].count(',')
                    child.attrib['contained'] = ',' * commas
                    logging.info(f'Reset {container[0].get("identifier")} with ID: {container_id}')
                    print(f'Reset {container[0].get("identifier")} with ID: {container_id}')


while True:
    # Prompt user for input file and remove quotes if they were added by dragging and dropping the file into the window
    submarine_input = Path(input("Drag and drop .sub/.xml file into this window to quickly and easily specify the file: "))
    if str(submarine_input).startswith("'") or str(submarine_input).startswith('"'):
        submarine_input = Path(str(submarine_input)[1:-1])
    if str(submarine_input).endswith("'") or str(submarine_input).endswith('"'):
        submarine_input = Path(str(submarine_input)[:-1])

    # Check if the file exists
    if not submarine_input.exists():
        print('File does not exist, please try again.\n')
        continue

    # Check if the file is a .sub or .xml file
    if submarine_input.suffix not in ['.sub', '.xml']:
        print('File is not a .sub or .xml file, please try again.\n')
        continue

    break

# Check if the user has already acknowledged the warning
if not Path('warningacknowledged').exists():
    warninginput = input("\nWARNING: While the program won't delete or mess with the input submarine file, "
                         "The following files will be overwriten/deleted if they already exist: "
                         f"\n* '{submarine_input.stem}.xml'"
                         f"\n* '{submarine_input.stem} (no items).xml'"
                         f"\n* '{submarine_input.stem} (no items).sub'\n"
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
logging.basicConfig(filename='BaroItemDeleter2.txt', filemode='w', level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Define list of containers and items that the program will recursively search for items in
containers_and_items = loads(open('searchable_containers.json').read())

# Define the padding for the tqdm description
description_padding = 25

if submarine_input.suffix == '.sub':  # Check if the input file is a .sub file
    # Check if a .xml file with the same name as the input .sub file already exists, and delete it if it does
    if Path(submarine_input.parent / (f'{submarine_input.stem}.xml')).exists():
        logging.info('Deleting already existing XML file')
        print('Deleting already existing XML file')
        Path(submarine_input.parent / (f'{submarine_input.stem}.xml')).unlink()

    # Extract the .sub file into a .xml file
    logging.info(f'Extracting sub file: {submarine_input}')
    print('Extracting sub file')
    with gzip.open(submarine_input, 'rb') as f_in:
        with open(Path(submarine_input.parent / (f'{submarine_input.stem}.xml')), 'wb') as f_out:
            shutil.copyfileobj(f_in, f_out)
else:
    logging.info(f'Using xml file: {submarine_input}')
    print('Using xml file')

tree = ET.parse(Path(submarine_input.parent / (f'{submarine_input.stem}.xml')))

root = tree.getroot()

item_ids = []

cleanedContainers = []

iterate_elements(root)

item_list = item_ids.copy()

# Iterate over all items in the list and recursively search them for more items
items = tqdm(item_list)
for item in items:
    matching_items = tree.findall(f".//*[@ID='{item}']")
    item_container = matching_items[0].get('identifier')
    logging.info(f'Recursively searching {item_container} with ID: {item}')
    recursive_search(item, items)

item_ids = list(set(item_ids))  # Remove duplicates from the list
cleanedContainers = list(set(cleanedContainers))  # Remove duplicates from the list

itemsDeleted = deleteItems()

cleanContainers()

logging.info('Saving edited XML file')
print('Saving edited XML file')
root.attrib['name'] = f'{submarine_input.stem} (no items)'
tree.write(Path(submarine_input.parent / (f'{submarine_input.stem} (no items).xml')))

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
logging.info(f'Removed {itemsDeleted} items and saved edited file. Took {perf_counter() - start} seconds.')
print(f'Removed {itemsDeleted} items and saved edited file. Took {perf_counter() - start} seconds.')
input('Press enter to exit.')
