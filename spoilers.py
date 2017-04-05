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

blockname = 'Amonkhet'
setname = 'AKH'
setlongname = 'Amonkhet'
setreleasedate = '2017-04-28'
setcount = 269
#set types: "core", "expansion", "reprint", "box", "un", "from the vault", "premium deck", "duel deck",
    # "starter", "commander", "planechase", "archenemy", "promo", "vanguard", "masters", "conspiracy"
settype = 'expansion'

offlineMode = False
useScryfall = False
makeAllsetsZip = True
downloadImages = True
overwriteImages = False
fullspoil = False
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

#for DFC, tuples with front name first, ex:
#"Huntmaster of the Fells":"Ravager of the Fells"
related_cards = {}

#delete erroneous cards and basics
delete_cards = ['Ready', 'Plains', 'Island', 'Swamp', 'Mountain', 'Forest']

#fix any cards that have errors, format:
#"card name": {
#  "key with incorrect value": "correct value"
#}
#can handle multiple incorrect values
#and handles incorrect name
#new keys will be created (loyalty)
#key values: name, img, cost, type, pow, rules, rarity, setnumber, loyalty, colorArray, colorIdentityArray, color, colorIdentity
card_corrections = {
    "Gideon of the Trials": {
        "loyalty": "3"
    },
    "Watchers of the Dead": {
        "pow": "2/2"
    },
    "Lay Bare the Heart": {
        "name": "Open Heart"
    },
    "Kefnet the Mindful": {
        "img": "https://i.redd.it/3ei96s19zjpy.jpg"
    },
    "Dusk": {
        "rules": "Destroy all creatures with power 3 or greater."
    },
    "Annointer Priest": {
        "name": "Anointer Priest"
    },
    "Kefnet's Monument": {
        "img": "http://mythicspoiler.com/akh/cards/kefnatsmonument.jpg"
    }
}

#if you want to add a card manually
#use this template and place the object in the manual_cards array
#example values:
#"cost": "X3BB",
#"cmc": "6", #yes, it's a string - that's how it's scraped
#"img": "http://media.wizards.com/2016/bVvMNuiu2i_KLD/en_0zfOjCQoWi.png",
#"pow": "*/1",
#"name": "Elspeth, Maker of Tokens",
#"rules": "+1: Make a super duper token.\n-20: Destroy stuff.",
#"type": "Legendary Artifact Creature - Human Soldier Zombie Druid",
#"setnumber": "666",
#"rarity": "Mythic Rare",
#"loyalty": 7, #loyalty is the only non-string value
manual_card_template = [
    {
        "cost": "",
        "cmc": "",
        "img": "",
        "pow": "",
        "name": "",
        "rules": "",
        "type": "",
        "setnumber": "",
        "rarity": "",
    },
]
#array for storing manually entered cards, mtgs can be slow
manual_cards = [
    {
        "cost": "2R",
        "cmc": "3",
        "img": "http://mythicspoiler.com/akh/cards/onwardvictory.jpg",
        "pow": "",
        "name": "Onward",
        "rules": "Target creature gets +X/+0 until end of turn, where X is its power.",
        "type": "Instant",
        "setnumber": "218a",
        "rarity": "Uncommon",
    },
    {
        "cost": "2W",
        "cmc": "3",
        "img": "http://mythicspoiler.com/akh/cards/onwardvictory.jpg",
        "pow": "",
        "name": "Victory",
        "rules": "Aftermath (Cast this spell only from your graveyard. Then exile it.)\nTarget creature gains double strike until end of turn.",
        "type": "Sorcery",
        "setnumber": "218b",
        "rarity": "Uncommon",
    },
    {
        "cost": "1W",
        "cmc": "2",
        "img": "http://mythicspoiler.com/akh/cards/preparedfight.jpg",
        "pow": "",
        "name": "Prepare",
        "rules": "Untap target creature. It gains +2/+2 and has lifelink until end of turn.",
        "type": "Instant",
        "setnumber": "220a",
        "rarity": "Rare",
    },
    {
        "cost": "3G",
        "cmc": "4",
        "img": "http://mythicspoiler.com/akh/cards/preparedfight.jpg",
        "pow": "",
        "name": "Fight",
        "rules": "Aftermath (Cast this spell only from your graveyard. Then exile it.)\nTarget creature you control fights target creature an opponent controls.",
        "type": "Sorcery",
        "setnumber": "220b",
        "rarity": "Rare",
    },
    {
        "cost": "3WW",
        "cmc": '5',
        "img": 'http://mythicspoiler.com/akh/cards/duskdawn.jpg',
        "pow": '',
        "name": 'Dawn',
        "rules": 'Aftermath (Cast this spell only from your graveyard, then exile it.)\nReturn all creature cards with power 2 or less from your graveyard to your hand.',
        "type": 'Sorcery',
        "setnumber": '210b',
        "rarity": 'Rare'
    },
    {
        "cost": "4W",
        "cmc": '5',
        "img": 'http://mythicspoiler.com/akh/cards/gideonmartialparagon.jpg',
        "pow": '',
        "loyalty": '0',
        "name": 'Gideon, Martial Paragon',
        "rules": "+2: Untap creatures you control. They get +1/+1 until end of turn.\n0: Until end of turn, Gideon, Martial Paragon becomes a 5/5 human Soldier with indestructible that's still a planeswalker. Prevent all damage that would be dealt to him this turn.\n-10: Creatures you control get +2/+2 until end of turn. Tap all creatures your opponents control.",
        "type": 'Planeswalker - Gideon',
        "setnumber": '270',
        "rarity": 'Mythic Rare'
    },
    {
        "cost": "5BB",
        "cmc": '7',
        "img": 'http://mythicspoiler.com/akh/cards/lilianadeathwielder.jpg',
        "pow": '',
        "loyalty": "0",
        "name": 'Liliana, Death Wielder',
        "rules": "+2: Put a -1/-1 counter on up to one target creature.\n-3: Destroy target creature with a -1/-1 counter on it.\n-10: Return all creature cards from your graveyard to the battlefield.",
        "type": 'Planeswalker - Liliana',
        "setnumber": '275',
        "rarity": 'Mythic Rare'
    },
    {
        "cost": "2W",
        "cmc": "3",
        "img": "https://i.redd.it/0qev4j3z1moy.png",
        "pow": "",
        "name": "Renewed Faith",
        "rules": "You gain 6 life\nCycling {1}{W}\nWhen you cycle Renewed Faith, you may gain 2 life.",
        "type": "Instant",
        "setnumber": "25",
        "rarity": "Uncommon",
    },
    {
        "cost": "1GG",
        "cmc": "3",
        "img": "https://pbs.twimg.com/media/C8MhyQwVwAAa-u-.jpg",
        "pow": "4/3",
        "name": "Prowling Serpopard",
        "rules": "Prowling Serpopard can't be countered.\nCreature spells you control can't be countered",
        "type": "Creature - Cat Snake",
        "setnumber": "180",
        "rarity": "Rare",
    },
    {
        "cost": "1B",
        "cmc": "2",
        "img": "http://mythicspoiler.com/akh/cards/destinedlead.jpg",
        "pow": "",
        "name": "Destined",
        "rules": "Target creature gets +1/+0 and gains indestructible until end of turn. ",
        "type": "Instant",
        "setnumber": "217a",
        "rarity": "Uncommon",
    },
    {
        "cost": "3G",
        "cmc": "4",
        "img": "http://mythicspoiler.com/akh/cards/destinedlead.jpg",
        "pow": "",
        "name": "Lead",
        "rules": "All creatures able to block target creature this turn do so.",
        "type": "Sorcery",
        "setnumber": "217b",
        "rarity": "Uncommon",
    },
]

#split cards (and aftermath) go here,
#"Front": "Back"
split_cards = {
    "Dusk": "Dawn",
    "Destined": "Lead",
    "Prepare": "Fight",
    "Onward": "Victory"
}

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

newest = ''

def scrape_mtgs():
    text = requests.get(SPOILER_RSS, headers={'Cache-Control':'no-cache', 'Pragma':'no-cache', 'Expires': 'Thu, 01 Jan 1970 00:00:00 GMT'}).text
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
    if count < 1:
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
        cards.append(manual_card)

    for card in cards:
        card['name'] = card['name'].replace('&#x27;', '\'')
        card['rules'] = card['rules'].replace('&#x27;', '\'') \
            .replace('&lt;i&gt;', '') \
            .replace('&lt;/i&gt;', '') \
            .replace('&quot;', '"') \
            .replace('blkocking', 'blocking')\
            .replace('&amp;bull;','*')\
            .replace('comes into the','enters the')\
            .replace('threeor', 'three or')\
            .replace('[i]','')\
            .replace('[/i]','')\
            .replace('Lawlwss','Lawless')\
            .replace('Costner',"Counter")
        card['type'] = card['type'].replace('  ',' ')\
            .replace('Crature', 'Creature')
        if card['type'][-1] == ' ':
            card['type'] = card['type'][:-1]
        if card['name'] in card_corrections:
            for correction in card_corrections[card['name']]:
                if correction != 'name':
                    card[correction] = card_corrections[card['name']][correction]
            for correction in card_corrections[card['name']]:
                if correction == 'name':
                    oldname = card['name']
                    card['name'] = card_corrections[oldname]['name']
                    card['rules'] = card['rules'].replace(oldname, card_corrections[oldname][correction])
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

    cleanedcards = []

    #let's remove any cards that are named in delete_cards array
    for card in cards:
        if not card['name'] in delete_cards:
            cleanedcards.append(card)
    cards = cleanedcards

    #remove dupes
    cardnames = []
    nodupes = []
    for card in cards:
        cardnames.append(card['name'])
        if not cardnames.count(card['name']) > 1:
            nodupes.append(card)
            
    cards = nodupes

    cardlist = []
    if (fullspoil):
        #print "Missing Cards:\n"
        for comparison in cardlist:
            missing = True
            for card in cards:
                if comparison in card['name']:
                    missing = False
                    #print 'found ' + comparison
            if missing:
                print comparison
    cardsjson = {
        'cards': []
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
        for namematch in related_cards:
            if card['name'] == related_cards[namematch]:
                card['layout'] = 'double-faced'
                cardnames.append(namematch)
                if not card['name'] in cardnames:
                    cardnames.append(card['name'])
                    cardnumber += 'b'
        cardnames = []
        if card['name'] in split_cards:
            cardnames.append(card['name'])
            cardnames.append(split_cards[card['name']])
            cardnumber = cardnumber.replace('b','').replace('a','') + 'a'
            card['layout'] = 'split'
        for namematch in split_cards:
            if card['name'] == split_cards[namematch]:
                card['layout'] = 'split'
                cardnames.append(namematch)
                if not card['name'] in cardnames:
                    cardnames.append(card['name'])
                    cardnumber = cardnumber.replace('b','').replace('a','') + 'b'
        if 'number' in card:
            if 'b' in card['number'] or 'a' in card['number']:
                if not 'layout' in card:
                    print card['name'] + " has a a/b number but no 'layout'"

        cardtypes = []
        if not '-' in card['type']:
            card['type'] = card['type'].replace('instant','Instant').replace('sorcery','Sorcery').replace('creature','Creature')
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
    if backupfiles and os.path.isfile(setjson):
        shutil.copyfile(setjson, 'bak/' + setjson)

    for card in cardsjson['cards']:
        for type in card['types']:
            if len(str(type)) <= 3:
                print card['name'] + ' has bad type'
    cardsjson = add_headers(cardsjson['cards'])

    return cardsjson

def add_headers(cardsarray):
    cardsjson = {
        "block": blockname,
        "border": "black",
        "code": setname,
        "magicCardsInfoCode": setname.lower(),
        "name": setlongname,
        "releaseDate": setreleasedate,
        "type": settype,
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
        "cards": cardsarray
    }
    return cardsjson

def get_scryfall():
    #ok let's set the api uri
    setUrl = 'https://api.scryfall.com/cards/search?q=++e:' + setname.lower()
    #we're going to while loop over the sets because they are spread across multiple pages
    setDone = False
    #initialize a cards array
    cards = {
        setname: {
            "cards": []
        }
    }
    while setDone == False:
            setcards = requests.get(setUrl)
            setcards = setcards.json()
            if setcards.has_key('data'):
                cards[setname]['cards'] = cards[setname]['cards'] + setcards['data']
            else:
                setDone = True
            #api requests a .05 sleep, generous with a .1
            time.sleep(.1)
            #key for has_more is true if there's another page and stores next page in 'next_page' key
            if setcards.has_key('has_more'):
                if setcards['has_more'] == True:
                    setUrl = setcards['next_page']
                else:
                    setDone = True
            else:
                setDone = True

    #create a new array for mtgjson conversion
    cards2 = {}
    cards2[setname] = {
        "cards": []
    }

    for card in cards[setname]['cards']:
        card2 = {}
        card2['cmc'] = int((card['converted_mana_cost']).split('.')[0])
        if card.has_key('mana_cost'):
            card2['manaCost'] = card['mana_cost'].replace('{', '').replace('}', '')
        else:
            card2['manaCost'] = ''
        card2['name'] = card['name']
        card2['number'] = card['collector_number']
        card2['rarity'] = card['rarity'].title()
        if card.has_key('oracle_text'):
            card2['text'] = card['oracle_text'].replace(u"\u2022 ", u'*').replace(u"\u2014", '-').replace(
                u"\u2212", "-")
        else:
            card2['text'] = ''
        card2['url'] = card['image_uri']
        card2['img'] = card['image_uri']
        card2['type'] = card['type_line'].replace(u'—', '-')
        cardtypes = card['type_line'].split(u' — ')[0].replace('Legendary ', '').replace('Snow ', '') \
            .replace('Elite ', '').replace('Basic ', '').replace('World ', '').replace('Ongoing ', '')
        cardtypes = cardtypes.split(' ')
        if u' — ' in card['type_line']:
            cardsubtypes = card['type_line'].split(u' — ')[1]
            if ' ' in cardsubtypes:
                card2['subtypes'] = cardsubtypes.split(' ')
            else:
                card2['subtypes'] = [cardsubtypes]
        if 'Legendary' in card['type_line']:
            if card2.has_key('supertypes'):
                card2['supertypes'].append('Legendary')
            else:
                card2['supertypes'] = ['Legendary']
        if 'Snow' in card['type_line']:
            if card2.has_key('supertypes'):
                card2['supertypes'].append('Snow')
            else:
                card2['supertypes'] = ['Snow']
        if 'Elite' in card['type_line']:
            if card2.has_key('supertypes'):
                card2['supertypes'].append('Elite')
            else:
                card2['supertypes'] = ['Elite']
        if 'Basic' in card['type_line']:
            if card2.has_key('supertypes'):
                card2['supertypes'].append('Basic')
            else:
                card2['supertypes'] = ['Basic']
        if 'World' in card['type_line']:
            if card2.has_key('supertypes'):
                card2['supertypes'].append('World')
            else:
                card2['supertypes'] = ['World']
        if 'Ongoing' in card['type_line']:
            if card2.has_key('supertypes'):
                card2['supertypes'].append('Ongoing')
            else:
                card2['supertypes'] = ['Ongoing']
        card2['types'] = cardtypes
        if card.has_key('color_identity'):
            card2['colorIdentity'] = card['color_identity']
        if card.has_key('colors'):
            card2['colors'] = []
            if 'W' in card['colors']:
                card2['colors'].append("White")
            if 'U' in card['colors']:
                card2['colors'].append("Blue")
            if 'B' in card['colors']:
                card2['colors'].append("Black")
            if 'R' in card['colors']:
                card2['colors'].append("Red")
            if 'G' in card['colors']:
                card2['colors'].append("Green")
                # card2['colors'] = card['colors']
        if card.has_key('all_parts'):
            card2['names'] = []
            for partname in card['all_parts']:
                card2['names'].append(partname['name'])
        if card.has_key('power'):
            card2['power'] = card['power']
        if card.has_key('toughness'):
            card2['toughness'] = card['toughness']
        if card.has_key('layout'):
            if card['layout'] != 'normal':
                card2['layout'] = card['layout']
        if card.has_key('loyalty'):
            card2['loyalty'] = int(card['loyalty'])
        if card.has_key('artist'):
            card2['artist'] = card['artist']
        #scryfall doesn't carry these keys
        # if card.has_key('source'):
        #    card2['source'] = card['source']
        # if card.has_key('rulings'):
        #    card2['rulings'] = card['rulings']
        if card.has_key('flavor_text'):
            card2['flavor'] = card['flavor_text']
        #did i forget a key? here's a template
        #if card.has_key(''):
        #    card2[''] = card['']

        cards2[setname]['cards'].append(card2)

    #we're just going to return the list of cards, because the rest of the program likes that.
    #cards2 by default is formatted
    #"setcode": {
    #  "cards": {
    #    [array of cards]
    #  }
    #}
    cards2 = add_headers(cards2[setname]['cards'])
    return cards2

#def list_missing(mtgjson):
#   return

#def combine_jsons(json1, json2):
#    return

def get_images(mtgjson):
    text = requests.get(IMAGES).text
    text2 = requests.get(IMAGES2).text
    text3 = requests.get(IMAGES3).text
    wotcpattern = r'<img alt="{}.*?" src="(?P<img>.*?\.png)"'
    mythicspoilerpattern = r' src="' + setname.lower() + '/cards/{}.*?.jpg">'
    for c in mtgjson['cards']:
        if fullspoil and not int(c['number']) > 184:
        #if fullspoil:
            #print c['name'] + ' is #' + c['setnumber']
            c['url'] = ''
        match = re.search(wotcpattern.format(c['name'].replace('\'','&rsquo;')), text, re.DOTALL)
        #if not c['url']:
        if match:
            c['url'] = match.groupdict()['img']
        else:
            match3 = re.search(wotcpattern.format(c['name'].replace('\'','&rsquo;')), text3, re.DOTALL)
            if match3:
                c['url'] = match3.groupdict()['img']
            elif not (fullspoil):
                match2 = re.search(mythicspoilerpattern.format((c['name']).lower().replace(' ', '').replace('&#x27;', '').replace('-', '').replace('\'','').replace(',', '')), text2, re.DOTALL)
                if match2:
                    c['url'] = match2.group(0).replace(' src="', 'http://mythicspoiler.com/').replace('">', '')
                    #else:
                        #print('image for {} not found'.format(c['name']))
                pass
        if ('Creature' in c['type'] and not c.has_key('power')) or ('Vehicle' in c['type'] and not c.has_key('power')):
            print(c['name'] + ' is a creature w/o p/t img: ' + c['url'])
        if len(str(c['url'])) < 10:
            print(c['name'] + ' has no image.')
    return mtgjson

def check_new(mtgjson):
    if os.path.isfile(setjson):
        with open(setjson) as data_file:
            oldcards = json.load(data_file)
        oldcount = 0
        newcount = 0
        for old in oldcards['cards']:
            #print old['name']
            oldcount = oldcount + 1
        for new in mtgjson['cards']:
            isnew = True
            for oldcard in oldcards['cards']:
                if oldcard['name'] == new['name']:
                    isnew = False
            if isnew:
                print 'New card! ' + new['name'] + '( ' + new['url'] + ' ) '
            if not new['name'] == 'delete':
                newcount = newcount + 1

def write_mtgjson(mtgjson):
    with open(setjson, 'w') as outfile:
        json.dump(mtgjson, outfile, sort_keys=True, indent=2, separators=(',', ': '))

def make_allsets(mtgjson):
    #let's see if we have an AllSets.pre.json, and how old it is.
    #if it's more than a week old, let's grab a new one
    getAllSets = False
    #if os.path.isfile('AllSets.pre.json'):
    #    allSetsAge = (time.time() - os.path.getctime('AllSets.pre.json'))
    #    if (allSetsAge < 604800):
    #        getAllSets = False
    #        #print "Found a current (" + str(datetime.timedelta(minutes=allSetsAge/60)) + ") AllSets.pre.json, not grabbing a new one."
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
        zf.write('AllSets.json', compress_type=compression)
    finally:
        #let's clear out the working files
        #os.remove('AllSets.pre.json')
        os.remove('AllSets.json')
        zf.close()

def write_xml(mtgjson, cardsxml):
    if backupfiles and os.path.isfile(cardsxml):
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
    #print mtgjson
    for card in mtgjson["cards"]:
        for carda in split_cards:
            if card["name"] == split_cards[carda]:
                continue
        if count == 0:
            newest = card["name"]
        count += 1
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
        cardcmc = str(card['cmc'])
        cardtype = card["type"]
        if card.has_key("names"):
            if "layout" in card:
                if card["layout"] != 'split':
                    if len(card["names"]) > 1:
                        if card["names"][0] == card["name"]:
                            related = card["names"][1]
                            text += '\n\n(Related: ' + card["names"][1] + ')'
                            dfccount += 1
                        elif card['names'][1] == card['name']:
                            related = card["names"][0]
                            text += '\n\n(Related: ' + card["names"][0] + ')'
                else:
                    for carda in split_cards:
                        if card["name"] == carda:
                            cardb = split_cards[carda]
                            for jsoncard in mtgjson["cards"]:
                                if cardb == jsoncard["name"]:
                                    cardtype += " // " + jsoncard["type"]
                                    manacost += " // " + (jsoncard["manaCost"]).replace('{', '').replace('}', '')
                                    cardcmc += " // " + str(jsoncard["cmc"])
                                    text += "\n---\n" + jsoncard["text"]
                                    name += " // " + cardb
            else:
                print card["name"] + " has multiple names and no 'layout' key"


        tablerow = "1"
        if "Land" in cardtype:
            tablerow = "0"
        elif "Sorcery" in cardtype:
            tablerow = "3"
        elif "Instant" in cardtype:
            tablerow = "3"
        elif "Creature" in cardtype:
            tablerow = "2"

        if 'number' in card:
            if 'b' in card['number']:
                if 'layout' in card:
                    if card['layout'] == 'split':
                        print "We're skipping " + card['name'] + " because it's the right side of a split card"
                        continue

        cardsxml.write("<card>\n")
        cardsxml.write("<name>" + name.encode('utf-8') + "</name>\n")
        cardsxml.write('<set rarity="' + card['rarity'] + '" picURL="' + card["url"] + '">' + setname + '</set>\n')
        cardsxml.write("<manacost>" + manacost.encode('utf-8') + "</manacost>\n")
        cardsxml.write("<cmc>" + cardcmc + "</cmc>")
        if card.has_key('colors'):
            colorTranslate = {
                "White": "W",
                "Blue": "U",
                "Black": "B",
                "Red": "R",
                "Green": "G"
            }
            for color in card['colors']:
                cardsxml.write('<color>' + colorTranslate[color] + '</color>')
        if name + ' enters the battlefield tapped' in text:
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

def download_images(mtgjson):
    if downloadImages:
        if not os.path.isdir('images/' + setname):
            os.makedirs('images/' + setname)
        for card in mtgjson['cards']:
            if card['url']:
                if os.path.isfile('images/' + setname + '/' + card['name'] + '.jpg') and not overwriteImages:
                    continue
                print 'Downloading ' + card['url'] + ' to images/' + setname + '/' + card['name'] + '.jpg'
                urllib.urlretrieve(card['url'], 'images/' + setname + '/' + card['name'] + '.jpg')
        #let's zip it up, with compression if possible
        try:
            import zlib
            compression = zipfile.ZIP_DEFLATED
        except:
            compression = zipfile.ZIP_STORED

        modes = {zipfile.ZIP_DEFLATED: 'deflated',
                 zipfile.ZIP_STORED: 'stored',
                 }
        zf = zipfile.ZipFile('Images.zip', mode='w')

        try:
            for file in os.listdir('images/' + setname):
                zf.write('images/' + setname + '/' + file, setname + '/' + file, compress_type=compression)
            zf.close()
        finally:
            zf.close()

def write_html(newest, mtgjson):
    f = open(html, 'r')
    lines = f.readlines()
    count = 0
    for card in mtgjson['cards']:
        count = count + 1
    lines[22] = str(count) + '/' + str(setcount) + ' \n'
    lines[26] = newest + '\n'
    lines[28] = str(datetime.date.today()) + '\n'
    lines[30] = str(datetime.datetime.today().strftime('%H:%M')) + '\n'
    #lines
    f.close()

    if backupfiles:
        shutil.copyfile(html, 'bak/' + html)
    f = open(html, 'w')
    f.writelines(lines)
    f.close()
    return

if __name__ == '__main__':
    if not offlineMode:
        mtgsjson = scrape_mtgs()
        if useScryfall:
            scryfalljson = get_scryfall()
            #mtgjson = combine_jsons(mtgsjson, scryfalljson)
        else:
            mtgjson = mtgsjson
    else:
        if os.path.isfile(setjson):
            with open(setjson) as data_file:
                mtgjson = json.load(data_file)
        else:
            sys.exit("No " + setjson + " file found, cannot run offline")
    mtgjson = get_images(mtgjson)
    check_new(mtgjson)
    write_mtgjson(mtgjson)
    make_allsets(mtgjson)
    latest = write_xml(mtgjson, cardsxml)
    download_images(mtgjson)
    write_html(latest, mtgjson)
