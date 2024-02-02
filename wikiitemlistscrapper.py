import requests
import json
from bs4 import BeautifulSoup

url = "https://barotraumagame.com/baro-wiki/index.php?title=Category:Items&pageuntil=Harmonica#mw-pages"

# Send a GET request to the URL
response = requests.get(url)

# Parse the HTML content using BeautifulSoup
soup = BeautifulSoup(response.content, "html.parser")

# Find all the item names inside the mw-pages class
item_names = []
mw_pages = soup.find(id="mw-pages")
if mw_pages:
    item_links = mw_pages.find_all("a")
    # Remove the first and last items from the list
    item_links = item_links[1:-1]
    for link in item_links:
        item_url = "https://barotraumagame.com" + link['href']
        item_response = requests.get(item_url)
        item_soup = BeautifulSoup(item_response.content, "html.parser")
        infobox = item_soup.find(class_="infobox responsive-table")
        if infobox:
            last_tr = infobox.find_all("tr")[-3]
            last_td = last_tr.find_all("td")[-1]
            item_name = last_td.text.replace('\n', '')
            item_names.append(item_name)

print(item_names)

# Write the item names to a json file
with open('item_names.json', 'w') as f:
    json.dump(item_names, f)
