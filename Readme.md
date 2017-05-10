## SpoilerSeason ##
SpoilerSeason is a python script to scrape MTGS, Scryfall, and Wizards.com to compile a cockatrice-friendly XML file as well as json files.

## Running ##

### Requirements ###
 * Python 2.7
 * Python Modules:
    requests==2.13.0
    feedparser
    lxml
    Pillow
    datetime

```
pip install -r requirements.txt
```

### Usage ###
    
```
$> python main.py
```

Outputs out/{SETCODE}.xml, out/MPS\_{SETCODE}.xml, out/{SETCODE}.json, out/{MPS\_{SETCODE}.json

errors are logged to out/errors.json

Add the set xml file to your `customsets` folder for Cockatrice.

When run by travis, uploads all files to [files branch](https://github.com/tritoch/SpoilerSeason/tree/files)
