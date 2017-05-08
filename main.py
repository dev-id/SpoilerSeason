# -*- coding: utf-8 -*-
import spoilers
import sys
#import configparser
import json
#import urllib

setinfos = {
    "setname": "AKH",
    "setlongname": "Amonkhet",
    "blockname": "Amonkhet",
    "setsize": 269,
    "setreleasedate": "2017-04-28",
    "settype": "expansion",
    "masterpieces": {
        "setname": "MPS_AKH",
        "setlongname": "Masterpiece Series: Amonkhet Invocations",
        "setreleasedate": "2017-04-28",
        "alternativeNames": ["Amonkhet Invocations"],
        "galleryURL": "http://magic.wizards.com/en/articles/archive/card-preview/masterpiece-series-amonkhet-invocations-2017-03-29",
        "additionalCardNames": [],
        "mtgsurl": "http://www.mtgsalvation.com/spoilers/181-amonkhet-invocations",
        "mtgscardpath": "http://www.mtgsalvation.com/cards/amonkhet-invocations/"
    }
}

presets = {
    "isfullspoil": True,
    "includeMasterpieces": True
}


#TODO insert configparser to add config.ini file

for argument in sys.argv:
    for setinfo in setinfos:
        if setinfo in argument.split("=")[0]:
            setinfos[setinfo] = argument.split("=")[0]
    for preset in presets:
        if preset in argument.split("=")[0]:
            presets[preset] = argument.split("=")[1]

def save_allsets(AllSets):
    print "Saving AllSets"

def save_masterpieces(masterpieces):
    print "Saving Masterpieces"

def save_setjson(mtgs):
    print "Saving Set MTGJSON"

if __name__ == '__main__':
    AllSets = spoilers.get_allsets()
    mtgs = spoilers.scrape_mtgs('http://www.mtgsalvation.com/spoilers.rss')
    mtgs = spoilers.parse_mtgs(mtgs)
    #scryfall = spoilers.get_scryfall('https://api.scryfall.com/cards/search?q=++e:' + setinfos['setname'].lower())
    mtgs = spoilers.get_image_urls(mtgs, presets['isfullspoil'], setinfos['setname'], setinfos['setlongname'], setinfos['setsize'])
    spoilers.write_xml(mtgs, setinfos['setname'], setinfos['setlongname'], setinfos['setreleasedate'])
    mtgs = spoilers.add_headers(mtgs, setinfos)
    AllSets = spoilers.make_allsets(AllSets, mtgs, setinfos['setname'])
    if 'masterpieces' in setinfos:
        masterpieces = spoilers.make_masterpieces(setinfos['masterpieces'], AllSets, mtgs)
        spoilers.write_xml(masterpieces, setinfos['masterpieces']['setname'], setinfos['masterpieces']['setlongname'], setinfos['masterpieces']['setreleasedate'])
        AllSets = spoilers.make_allsets(AllSets, masterpieces, setinfos['masterpieces']['setname'])
        save_masterpieces(masterpieces)
    save_allsets(AllSets)
    save_setjson(mtgs)

#outline
#set variables
#open files
#enable/disable features
#call spoilers
#save files
