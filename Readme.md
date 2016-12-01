## Creating a set.xml file ##

### Requirements ###
 * Python 2.7
 * Python Modules:
    datetime
    requests
    feedparser
    re
    json
    shutil
    sys
    urllib
    os
    zipfile

...
pip install requests feedparser
...

### Usage ###
    
```
$> python spoilers.py
```

Outputs {SETCODE}.json, {SETCODE}.xml, AllSets.json.zip, and Images.zip (containing {SETCODE}\{IMAGE NAMES}.jpg)

Create the set xml file and add it to your `customsets` folder for Cockatrice.

Scraper code by robtandy @ https://github.com/robtandy/CockatriceSpoilerXML

All other code is MIT License
