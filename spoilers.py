# -*- coding: utf-8 -*-
import datetime
import requests
import feedparser
import re
import json
import shutil
import sys
import urllib
import os
import zipfile
import time

requests.packages.urllib3.disable_warnings()

#variables for xml & json
blockname = 'Kaladesh'
setname = 'KLD'
setlongname = 'Kaladesh'
setreleasedate = '2016-09-30'

#if there's no new cards, the default option is to kill the program
#if you want to do updates, you can force the program to run with this variable
forcerun = False

#you can create a AllSets.json.zip by grabbing the current one from mtgjson
#and slapping the current set on the end of it. disabled by default
makezip = True

#you can download a local copy of images (to images/Card Name.jpg)
#yes, we call it .jpg no matter - it's more cockatrice-friendly
downloadimages = False

#once we're at full spoil, we'll turn off mythic to prefer wotc's images
#they're preferred anyway, but just in case ;)
mythicenabled = True

#we may want to back up files before scraping
#in case the scraping goes wrong like the
#rss feed being overwritten by blank or a new set coming out
#this is a destructive backup, so it's only good for one oops
#if we turn this off, we can remove the shutil dependency
backupfiles = True

#the two files that will be generated in program directory
#default is SETCODE.json and SETCODE.xml
setjson = setname + '.json'
cardsxml = setname + '.xml'

#for maintaining an html page with changes.
#format is
#line 23: number of cards in xml
#line 27: latest card added
#line 29: date of last add
#line 31: time of last add
html = 'index.html'

#once mtgs removes or changes their spoilers.rss, this program will stop working.
#if we switch to offline mode, we can still make the xml, html, and smash the json
#if we have a good setcode.json
offlinemode = False

#static
SPOILER_RSS = 'http://www.mtgsalvation.com/spoilers.rss'
#typically magic.wizards.com/en/content/set-name-with-hyphens-cards
IMAGES = 'http://magic.wizards.com/en/content/' + setlongname.lower().replace(' ','-') + '-cards'
#static
IMAGES2 = 'http://mythicspoiler.com/newspoilers.html'
#magic.wizards.com/en/articles/archive/card-image-gallery/set-name-with-hyphens
IMAGES3 = 'http://magic.wizards.com/en/articles/archive/card-image-gallery/' + setlongname.lower().replace(' ','-')

#scraper pattern for mtgs rss feed
patterns = ['<b>Name:</b> <b>(?P<name>.*?)<',
            'Cost: (?P<cost>\d{0,2}[WUBRGC]*?)<',
            'Type: (?P<type>.*?)<',
            'Pow/Tgh: (?P<pow>.*?)<',
            'Rules Text: (?P<rules>.*?)<br /',
            'Rarity: (?P<rarity>.*?)<',
            'Set Number: #(?P<setnumber>.*?)/'
            ]

#for DFC, tuples with front name first, ex:
#"Huntmaster of the Fells":"Ravager of the Fells"
related_cards = {}

#fix any cards that have errors, format:
#"card name": {
#  "key with incorrect value": "correct value"
#}
#can handle multiple incorrect values
#and handles incorrect name
#new keys will be created (loyalty)
#key values: name, img, cost, type, pow, rules, rarity, setnumber, loyalty, colorArray, colorIdentityArray, color, colorIdentity
card_corrections = {
    "Glint-Sleeved Artisan": {
        "name": "Glint-Sleeve Artisan"
    },
    "Fleetwheel Cruiser": {
        "pow": "5/3",
        "type": "Artifact - Vehicle"
    },
    "Golden Wire Fox": {
        "pow": "2/2"
    },
    "Sky Skiff": {
        "pow": "2/3"
    },
    "Skysovereign, Consul Flagship": {
        "pow": "6/5"
    },
    "Ovalchase Dragster": {
        "pow": "6/1"
    },
    "Saheeli Rai": {
        "loyalty": 3
    },
    "Demon of Shadowy Schemes": {
        "name": "Demon of Shady Schemes"
    },
    "Larger than Life": {
        "name": "Larger Than Life",
        "img": "https://pbs.twimg.com/media/CrmPhI1WIAAl77B.png"
    },
    "Pia Nalaar": {
        "img": "http://media.wizards.com/2016/bVvMNuiu2i_KLD/en_z8u7TFxf8R.png"
    },
    "Master Trinketcrafter": {
        "img": "http://media-dominaria.cursecdn.com/avatars/thumbnails/126/862/200/283/636086937653130201.png"
    },
    "Multiform Wonder": {
        "img": "http://media.wizards.com/2016/bVvMNuiu2i_KLD/en_0zfOjCQoWi.png"
    },
    " Rashmi, Eterniafter ": {
        "name": "delete"
    },
    "DeputisProtester": {
        "name": "delete"
    },
    "Decocotion Module": {
        "name": "Decoction Module"
    },
    "Chandra, Torch of Defiance": {
        "loyalty": 4
    },
    "Nissa, Nature's Artisan": {
        "loyalty": 5
    },
    "Nissa, Vital Force": {
        "loyalty": 5
    },
    "Wildest Dreams": {
        "img": "http://media-dominaria.cursecdn.com/avatars/127/172/636089412426252877.png"
    },
    "Acrobatic Maneuver": {
        "img": "http://media-dominaria.cursecdn.com/avatars/127/182/636089769798790258.png"
    },
    "Midnight Oil": {
        "img": "http://media-dominaria.cursecdn.com/avatars/127/183/636089778778747687.png"
    },
    "Noxious Gearhulk": {
        "pow": "5/4"
    },
    "Smuggler's Copter": {
        "pow": "3/3"
    }

}

#if you want to add a card manually
#use this template and place the object in the manual_cards array
#example values:
#"cost": "X3BB",
#"cmc": "6", #yes, it's a string - that's how it's scraped
#"img": "http://media.wizards.com/2016/bVvMNuiu2i_KLD/en_0zfOjCQoWi.png",
#"pow": "*/1",
#"name": "Gideon, Maker of Tokens",
#"rules": "+1: Make a super duper token.\n-20: Destroy stuff.",
#"type": "Legendary Artifact Creature - Human Soldier Zombie Druid",
#"setnumber": "666",
#"rarity": "Mythic Rare",
#"loyalty": 7, #loyalty is the only non-string value
manual_card_template = [
    {
        "cost": '',
        "cmc": '',
        "img": '',
        "pow": '',
        "name": '',
        "rules": '',
        "type": '',
        "setnumber": '',
        "rarity": '',
    }
]

#array for storing manually entered cards, mtgs can be slow
manual_cards = [
    {
        "cost": 'W',
        "cmc": '1',
        "img": 'http://s3.gatheringmagic.com/uploads/2016/09/09/AU_1.png',
        "pow": '',
        "name": 'Fragmentize',
        "rules": 'Destroy target artifact or enchantment with converted mana cost 4 or less.',
        "type": 'Sorcery',
        "setnumber": '14',
        "rarity": 'Common',
    },
    {
        "cost": '2R',
        "cmc": '3',
        "img": 'https://cdn.pastemagazine.com/www/articles/Welding%20Sparks.png',
        "pow": '',
        "name": 'Welding Sparks',
        "rules": 'Welding Sparks deals X damage to target creature, where X is 3 plus the number of artifacts you control.',
        "type": 'Instant',
        "setnumber": '140',
        "rarity": 'Common',
    },
    {
        "cost": '4GG',
        "cmc": '6',
        "img": 'http://media.wizards.com/2016/bVvMNuiu2i_KLD/en_YXvBDsDjHq.png',
        "loyalty": 5,
        "name": 'Nissa, Nature\'s Artisan',
        "rules": '+1: You gain 3 life.\n\
-4: Reveal the top two cards of your library. \
Put all land cards from among them onto the battlefield and the rest into your hand.\n\
-12: Creatures you control get +5/+5 and gain trample until end of turn.',
        "type": 'Planeswalker - Nissa',
        "setnumber": '270',
        "rarity": 'Mythic Rare',
    },
    {
        "cost": '4RR',
        "cmc": '6',
        "img": 'http://media.wizards.com/2016/bVvMNuiu2i_KLD/en_CO4tkc9sLe.png',
        "loyalty": 5,
        "name": 'Chandra, Pyrogenius',
        "rules": '+2: Chandra, Pyrogenius deals 2 damage to each opponent.\n\
-3: Chandra, Pyrogenius deals 4 damage to target creature.\n\
-10: Chandra, Pyrogenius deals 6 damage to target player and \
each creature he or she controls',
        "type": 'Planeswalker - Chandra',
        "setnumber": '265',
        "rarity": 'Mythic Rare',
    },
    {
        "cost": '2GG',
        "cmc": '4',
        "img": 'http://img.tcgplayer.com/tcg_img/media_tcg/articles/0147_MTGKLD_EN_HRR.png',
        "pow": '4/3',
        "name": 'Bristling Hydra',
        "rules": 'When Bristling Hydra enters the battlefield, you get {E}{E}{E} (three energy counters)\n\
Pay {E}{E}{E}: Put a +1/+1 counter on Bristling Hydra. It gains hexproof until end of turn.',
        "type": 'Creature - Hydra',
        "setnumber": '147',
        "rarity": 'Rare',
    }
]

def get_cards():
    text = requests.get(SPOILER_RSS).text
    d = feedparser.parse(text)

    cards = []
    for entry in d.items()[5][1]:
        card = dict(cost='',cmc='',img='',pow='',name='',rules='',type='',
                color='', altname='', colorIdentity='', colorArray=[], colorIdentityArray=[], setnumber='', rarity='')
        summary = entry['summary']
        for pattern in patterns:
            match = re.search(pattern, summary, re.MULTILINE|re.DOTALL)
            if match:
                dg = match.groupdict()
                card[dg.items()[0][0]] = dg.items()[0][1]
        cards.append(card)

    #if we didn't find any cards, let's bail out to prevent overwriting good data
    count = 0
    for card in cards:
        count = count + 1
    #let's assume there should be at least 5 good cards
    #if there's less than 5 cards, why are you scraping?
    if count < 5:
        sys.exit("No cards found, exiting to prevent file overwrite")

    for manual_card in manual_cards:
        #initialize some keys
        manual_card['colorArray'] = []
        manual_card['colorIdentityArray'] = []
        manual_card['color'] = ''
        manual_card['colorIdentity'] = ''
        if not manual_card.has_key('rules'):
            manual_card['rules'] = ''
        if not manual_card.has_key('pow'):
            manual_card['pow'] = ''
        if not manual_card.has_key('setnumber'):
            manual_card['setnumber'] = '0'
        if not manual_card.has_key('type'):
            manual_card['type'] = ''
        #see if this is a dupe
        #and remove the spoiler version
        #i trust my manual cards over their data
        for card in cards:
            if card['name'] == manual_card['name']:
                cards.remove(card)
                #print 'Found scraped card, deleting and using manual card: ' + manual_card['name']
        #print 'Inserting manual card: ' + manual_card['name']
        cards.append(manual_card)



    return cards

def correct_cards(cards):
    for card in cards:
        if card['name'] in card_corrections:
            for correction in card_corrections[card['name']]:
                if correction != 'name':
                    card[correction] = card_corrections[card['name']][correction]
            for correction in card_corrections[card['name']]:
                if correction == 'name':
                    oldname = card['name']
                    card['name'] = card_corrections[oldname]['name']
                    card['rules'] = card['rules'].replace(oldname, card_corrections[oldname][correction])

        card['name'] = card['name'].replace('&#x27;', '\'')
        card['rules'] = card['rules'].replace('&#x27;', '\'') \
            .replace('&lt;i&gt;', '') \
            .replace('&lt;/i&gt;', '') \
            .replace('&quot;', '"') \
            .replace('blkocking', 'blocking').replace('&amp;bull;','*')\
            .replace('comes into the','enters the')\
            .replace('threeor', 'three or')\
            .replace('[i]','')\
            .replace('[/i]','')

        if 'cost' in card and len(card['cost']) > 0:
            m = re.search('(\d+)', card['cost'].replace('X',''))
            cmc = 0
            if m:
                cmc += int(m.group())
                cmc += len(card['cost']) - 1  # account for colored symbols
            else:
                cmc += len(card['cost'])  # all colored symbols
            card['cmc'] = cmc
        # figure out color
        for c in 'WUBRG':
            if c not in card['colorIdentity']:
                if c in card['cost']:
                    card['color'] += c
                    card['colorIdentity'] += c
                if (c + '}') in card['rules'] or (str.lower(c) + '}') in card['rules']:
                    if not (c in card['colorIdentity']):
                        card['colorIdentity'] += c

        if card['name'] == 'delete':
            cards.remove(card)

    #we're going to see if the card count has increased, if it hasn't, bail.
    #remove dupes
    cardnames = []
    for card in cards:
        cardnames.append(card['name'])
        if cardnames.count(card['name']) > 1:
            cards.remove(card)

    if os.path.isfile(setjson):
        with open(setjson) as data_file:
            oldcards = json.load(data_file)
        oldcount = 0
        newcount = 0
        for old in oldcards['cards']:
            #print old['name']
            oldcount = oldcount + 1
        for new in cards:
            isnew = True
            for oldcard in oldcards['cards']:
                if oldcard['name'] == new['name']:
                    isnew = False
            if isnew:
                print 'New card! ' + new['name']
            if not new['name'] == 'delete':
                newcount = newcount + 1
                #print new['name']
        #bail on execution if we don't have any new cards
        #and we're not forcing
        if not newcount > oldcount and not forcerun:
            sys.exit("No new cards found (" + str(newcount) + " cards)")

    return cards

def add_images(cards):
    text = requests.get(IMAGES).text
    text2 = requests.get(IMAGES2).text
    text3 = requests.get(IMAGES3).text
    wotcpattern = r'<img alt="{}.*?" src="(?P<img>.*?\.png)"'
    mythicspoilerpattern = r' src="' + setname.lower() + '/cards/{}.*?.jpg">'
    for c in cards:
        match = re.search(wotcpattern.format(c['name'].replace('\'','&rsquo;')), text, re.DOTALL)
        if not c['img']:
            if match:
                c['img'] = match.groupdict()['img']
            else:
                match3 = re.search(wotcpattern.format(c['name'].replace('\'','&rsquo;')), text3, re.DOTALL)
                if match3:
                    c['img'] = match3.groupdict()['img']
                elif (mythicenabled):
                    match2 = re.search(mythicspoilerpattern.format((c['name']).lower().replace(' ', '').replace('&#x27;', '').replace('-', '').replace('\'','').replace(',', '')), text2, re.DOTALL)
                    if match2:
                        #print match2.group(0).replace(' src="', 'http://mythicspoiler.com/').replace('">', '')
                        c['img'] = match2.group(0).replace(' src="', 'http://mythicspoiler.com/').replace('">', '')
                    else:
                        print('image for {} not found'.format(c['name']))
                        #print('we checked mythic for ' + c['altname'])
                    pass

def make_json(cards, setjson):
    #initialize mtg format json
    cardsjson = {
        "block": blockname,
        "border": "black",
        "code": setname,
        "magicCardsInfoCode": setname.lower(),
        "name": setlongname,
        "releaseDate": setreleasedate,
        "type": "expansion",
        "booster": [
                [
                "rare",
                "mythic rare"
                ],
            "uncommon",
            "uncommon",
            "uncommon",
            "common",
            "common",
            "common",
            "common",
            "common",
            "common",
            "common",
            "common",
            "common",
            "common",
            "land",
            "marketing"
        ],
        "cards": []
    }
    for card in cards:
        dupe = False
        for dupecheck in cardsjson['cards']:
            if dupecheck['name'] == card['name']:
                dupe = True
        if dupe == True:
            continue
        #if 'draft' in card['rules']:
        #    continue
        for cid in card['colorIdentity']:
            card['colorIdentityArray'].append(cid)
        if 'W' in card['color']:
            card['colorArray'].append('White')
        if 'U' in card['color']:
            card['colorArray'].append('Blue')
        if 'B' in card['color']:
            card['colorArray'].append('Black')
        if 'R' in card['color']:
            card['colorArray'].append('Red')
        if 'G' in card['color']:
            card['colorArray'].append('Green')
        cardpower = ''
        cardtoughness = ''
        if len(card['pow'].split('/')) > 1:
            cardpower = card['pow'].split('/')[0]
            cardtoughness = card['pow'].split('/')[1]
        cardnames = []
        cardnumber = card['setnumber'].lstrip('0')
        if card['name'] in related_cards:
            cardnames.append(card['name'])
            cardnames.append(related_cards[card['name']])
            cardnumber += 'a'
            card['layout'] = 'double-faced'
            card['name']
        for namematch in related_cards:
            if card['name'] == related_cards[namematch]:
                card['layout'] = 'double-faced'
                cardnames.append(namematch)
                if not card['name'] in cardnames:
                    cardnames.append(card['name'])
                    cardnumber += 'b'
        cardtypes = []
        if not '-' in card['type']:
            card['type'] = card['type'].replace('instant','Instant')
            cardtypes.append(card['type'].replace('instant','Instant'))
        else:
            cardtypes = card['type'].replace('Legendary ','').split('-')[0].split(' ')[:-1]
        if card['cmc'] == '':
            card['cmc'] = 0
        cardjson = {}
        #cardjson["id"] = hashlib.sha1(setname + card['name'] + str(card['name']).lower()).hexdigest()
        cardjson["cmc"] = card['cmc']
        cardjson["manaCost"] = card['cost']
        cardjson["name"] = card['name']
        cardjson["number"] = cardnumber
        #not sure if mtgjson has a list of acceptable rarities, but my application does
        #so we'll warn me but continue to write a non-standard rarity (timeshifted?)
        #may force 'special' in the future
        if card['rarity'] not in ['Mythic Rare','Rare','Uncommon','Common','Special']:
            print card['name'] + ' has rarity = ' + card['rarity']
        cardjson["rarity"] = card['rarity']
        cardjson["text"] = card['rules']
        cardjson["type"] = card['type']
        cardjson["url"] = card['img']
        cardjson["types"] = cardtypes
        #optional fields
        if len(card['colorIdentityArray']) > 0:
            cardjson["colorIdentity"] = card['colorIdentityArray']
        if len(card['colorArray']) > 0:
            cardjson["colors"] = card['colorArray']
        if len(cardnames) > 1:
            cardjson["names"] = cardnames
        if cardpower or cardpower == '0':
            cardjson["power"] = cardpower
            cardjson["toughness"] = cardtoughness
        if card.has_key('loyalty'):
            cardjson["loyalty"] = card['loyalty']
        if card.has_key('layout'):
            cardjson["layout"] = card['layout']

        cardsjson['cards'].append(cardjson)
    if backupfiles:
        shutil.copyfile(setjson, 'bak/' + setjson)
    with open(setjson, 'w') as outfile:
        json.dump(cardsjson, outfile, sort_keys=True, indent=2, separators=(',', ': '))

    return cardsjson

def specialcards(cardsjson):
    #this is a fuction used for my app to create a list of 'special' cards
    #that are inserted differently than regular cards in a 'pack'
    #specifically, the below is for DFC, exactly, for SOI/EMN
    specialjson = {
        "Mythic Rare": [],
        "Rare": [],
        "Uncommon": [],
        "Common": []
    }
    for card in cardsjson['cards']:
        if card.has_key('layout'):
            if card['layout'] == 'double-faced' and 'a' in card['number']:
                specialjson[card['rarity']].append(card['name'].lower())
    for specialrarity in specialjson:
        print specialrarity + ': ['
        for name in specialjson[specialrarity]:
            print '"' + name + '"'
        print "]"

def write_xml(mtgjson, cardsxml):
    if backupfiles:
        shutil.copyfile(cardsxml, 'bak/' + cardsxml)
    cardsxml = open(cardsxml, 'w')
    cardsxml.truncate()
    count = 0
    dfccount = 0
    newest = ''
    related = 0
    cardsxml.write("<?xml version='1.0' encoding='UTF-8'?>\n"
                   "<cockatrice_carddatabase version='3'>\n"
                   "<sets>\n<set>\n<name>"
                   + setname +
                   "</name>\n"
                   "<longname>"
                   + setlongname +
                   "</longname>\n"
                   "<settype>Expansion</settype>\n"
                   "<releasedate>"
                   + setreleasedate +
                   "</releasedate>\n"
                   "</set>\n"
                   "</sets>\n"
                   "<cards>")
    for card in mtgjson["cards"]:
        if count == 0:
            newest = card["name"]
        count += 1
        #print card["name"]
        name = card["name"]
        if card.has_key("manaCost"):
            manacost = card["manaCost"].replace('{', '').replace('}', '')
        else:
            manacost = ""
        if card.has_key("power") or card.has_key("toughness"):
            if card["power"]:
                pt = str(card["power"]) + "/" + str(card["toughness"])
            else:
                pt = 0
        else:
            pt = 0
        if card.has_key("text"):
            text = card["text"]
        else:
            text = ""
        if card.has_key("names"):
            if len(card["names"]) > 1:
                if card["names"][0] == card["name"]:
                    related = card["names"][1]
                    text += '\n\n(Related: ' + card["names"][1] + ')'
                    dfccount += 1
                elif card['names'][1] == card['name']:
                    related = card["names"][0]
                    text += '\n\n(Related: ' + card["names"][0] + ')'

        cardtype = card["type"]
        tablerow = "1"
        if "Land" in cardtype:
            tablerow = "0"
        elif "Sorcery" in cardtype:
            tablerow = "3"
        elif "Instant" in cardtype:
            tablerow = "3"
        elif "Creature" in cardtype:
            tablerow = "2"

        cardsxml.write("<card>\n")
        cardsxml.write("<name>" + name.encode('utf-8') + "</name>\n")
        cardsxml.write('<set rarity="' + card['rarity'] + '" picURL="' + card["url"] + '">' + setname + '</set>\n')
        cardsxml.write("<manacost>" + manacost.encode('utf-8') + "</manacost>\n")
        cardsxml.write("<cmc>" + str(card['cmc']) + "</cmc>")
        if card.has_key('colors'):
            for color in card['colors']:
                cardsxml.write('<color>' + color + '</color>')
        if name == 'Terrarion' or name == 'Cryptolith Fragment':
            cardsxml.write("<cipt>1</cipt>")
        cardsxml.write("<type>" + cardtype.encode('utf-8') + "</type>\n")
        if pt:
            cardsxml.write("<pt>" + pt + "</pt>\n")
        if card.has_key('loyalty'):
            cardsxml.write("<loyalty>" + str(card['loyalty']) + "</loyalty>")
        cardsxml.write("<tablerow>" + tablerow + "</tablerow>\n")
        cardsxml.write("<text>" + text.encode('utf-8') + "</text>\n")
        if related:
        #    for relatedname in related:
            cardsxml.write("<related>" + related.encode('utf-8') + "</related>\n")
            related = ''

        cardsxml.write("</card>\n")

    cardsxml.write("</cards>\n</cockatrice_carddatabase>")

    print 'XML STATS'
    print 'Total cards: ' + str(count)
    if dfccount > 0:
        print 'DFC: ' + str(dfccount)
    print 'Newest: ' + str(newest)
    print 'Runtime: ' + str(datetime.datetime.today().strftime('%H:%M')) + ' on ' + str(datetime.date.today())

    return newest

def writehtml(newest, cards):
    f = open(html, 'r')
    lines = f.readlines()
    count = 0
    for card in cards['cards']:
        count = count + 1
    lines[22] = str(count) + '\n'
    lines[26] = newest + '\n'
    lines[28] = str(datetime.date.today()) + '\n'
    lines[30] = str(datetime.datetime.today().strftime('%H:%M')) + '\n'
    lines
    f.close()

    if backupfiles:
        shutil.copyfile(html, 'bak/' + html)
    f = open(html, 'w')
    f.writelines(lines)
    f.close()

def download_images(mtgjson):
    for card in mtgjson['cards']:
        if card['url'] and not os.path.isfile('images/' + card['name'] + '.jpg') :
            print 'Downloading ' + card['url'] + ' to images/' + card['name'] + '.jpg'
            urllib.urlretrieve(card['url'], 'images/' + card['name'] + '.jpg')

def makeAllSets(mtgjson):
    #let's see if we have an AllSets.pre.json, and how old it is.
    #if it's more than a week old, let's grab a new one
    getAllSets = True
    if os.path.isfile('AllSets.pre.json'):
        allSetsAge = (time.time() - os.path.getctime('AllSets.pre.json'))
        if (allSetsAge < 604800):
            getAllSets = False
            #print "Found a current (" + str(datetime.timedelta(minutes=allSetsAge/60)) + ") AllSets.pre.json, not grabbing a new one."
    if getAllSets:
        #we have to spoof a user-agent for mtgjson
        class MyOpener(urllib.FancyURLopener):
            version = 'Mozilla/5.0 (Windows; U; Windows NT 5.1; it; rv:1.8.1.11) Gecko / 20071127 Firefox / 2.0.0.11'
        opener = MyOpener()
        opener.retrieve('http://mtgjson.com/json/AllSets.json', 'AllSets.pre.json')
        #let's remove the last } from mtgjson
        #then put the new set code in there
        with open('AllSets.pre.json', 'rb+') as filehandle:
            filehandle.seek(-1, os.SEEK_END)
            filehandle.truncate()
            filehandle.write(',"' + setname + '":')

    #now let's smash together the old json
    #with our new one
    #and then close it!
    with open('AllSets.json', 'wb') as wfd:
        for f in ['AllSets.pre.json', setjson]:
            with open(f, 'rb') as fd:
                shutil.copyfileobj(fd, wfd, 1024 * 1024 * 10)
                # 10MB per writing chunk to avoid reading big file into memory.
        wfd.write('}')

    #let's zip it up, with compression if possible
    try:
        import zlib
        compression = zipfile.ZIP_DEFLATED
    except:
        compression = zipfile.ZIP_STORED

    modes = {zipfile.ZIP_DEFLATED: 'deflated',
             zipfile.ZIP_STORED: 'stored',
             }
    zf = zipfile.ZipFile('AllSets.json.zip', mode='w')
    try:
        #print 'adding AllSets.json with compression mode', modes[compression]
        zf.write('AllSets.json', compress_type=compression)
    finally:
        #let's clear out the working files
        #os.remove('AllSets.pre.json')
        os.remove('AllSets.json')
        zf.close()

if __name__ == '__main__':
    cards = get_cards()
    cards = correct_cards(cards)
    #for some reason bedlam reveler doesn't get caught the first time through...
    #cards = correct_cards(cards)
    add_images(cards)
    if offlinemode:
        with open(setjson) as data_file:
            mtgjson = json.load(data_file)
    else:
        mtgjson = make_json(cards, setjson)
    if makezip:
        makeAllSets(mtgjson)
    newest = write_xml(mtgjson, cardsxml)
    if downloadimages:
        download_images(mtgjson)
    writehtml(newest, mtgjson)
    #specialcards(mtgjson)
