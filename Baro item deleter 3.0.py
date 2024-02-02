import xml.etree.ElementTree as ET
import json

# Parse the XML file
tree = ET.parse('Metallicor MK1.xml')
root = tree.getroot()

# Load container identifiers from JSON file
with open('searchable_containers.json', 'r') as f:
    container_identifiers = json.load(f)


# Function to recursively find items in a container
def find_items_in_container(container):
    items = []
    item_container = container.find('ItemContainer')
    if item_container is not None:
        contained_ids = item_container.get('contained', '').split(',')
        for id in contained_ids:
            item = root.find(f".//*[@ID='{id}']")
            if item is not None:
                items.append(item)
                items.extend(find_items_in_container(item))
    return items


# Find all containers and the items in them
containers = [elem for elem in root.findall('.//Item') if elem.get('identifier') in container_identifiers]
items_to_delete = [item for container in containers for item in find_items_in_container(container)]

# Now you have a list of all items to delete
# You can delete them, reset their values, etc.
for item in items_to_delete:
    # Delete the item
    root.remove(item)
    # Or reset its values
    # item.set('attribute', 'new value')

# Write the modified XML back to the file
tree.write('Metallicor MK1.xml')
