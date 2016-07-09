# -*- coding: utf-8 -*-
import datetime
import requests
import feedparser
import re
import json
#import hashlib

setname = 'EMN'
setjson = setname + '.json'
cardsxml = setname + '.xml'
html = 'index.html'

SPOILER_RSS = 'http://www.mtgsalvation.com/spoilers.rss'
IMAGES = 'http://magic.wizards.com/en/content/eldritch-moon-cards'
IMAGES2 = 'http://mythicspoiler.com/newspoilers.html'
IMAGES3 = 'http://magic.wizards.com/en/articles/archive/card-image-gallery/eldritch-moon'

patterns = ['<b>Name:</b> <b>(?P<name>.*?)<',
            'Cost: (?P<cost>\d{0,2}[WUBRGC]*?)<',
            'Type: (?P<type>.*?)<',
            'Pow/Tgh: (?P<pow>.*?)<',
            'Rules Text: (?P<rules>.*?)<br /',
            'Rarity: (?P<rarity>.*?)<',
            'Set Number: #(?P<setnumber>.*?)/'
            ]

related_cards = {'Gisela, the Broken Blade': 'Brisela, Voice of Nightmares',
                 'Bruna, the Fading Light': 'Brisela, Voice of Nightmares',
                 'Ulrich of the Krallenhorde': 'Ulrich, Uncontested Alpha',
                 'Lone Rider': 'It That Rides as One',
                 'Grizzled Angler': 'Grisly Anglerfish',
                 'Docent of Perfection': 'Final Iteration',
                 'Cryptolith Fragment': 'Aurora of Emrakul',
                 'Hanweir Battlements': 'Hanweir, the Writhing Township',
                 'Hanweir Garrison': 'Hanweir, the Writhing Township',
                 'Midnight Scavengers': 'Chittering Host',
                 'Graf Rats': 'Chittering Host',
                 'Ulvenwald Captive': 'Ulvenwald Abomination',
                 'Vildin-Pack Outcast': 'Dronepack Kindred',
                 'Smoldering Werewolf': 'Erupting Dreadwolf',
                 'Kessig Prowler': 'Sinuous Predator',
                 'Curious Homunculus': 'Voracious Reader',
                 'Voldaren Pariah': 'Abolisher of Bloodlines',
                 'Extricator of Sin': 'Extricator of Flesh',
                 'Conduit of Storms': 'Conduit of Emrakul',
                 'Shrill Howler': 'Howling Chorus',
                 'Tangleclaw Werewolf': 'Fibrous Entangler'
                 }

card_corrections = {
    'Strange Augmentation': {
        "type": "Enchantment - Aura"
    },
    'Contigencey Plan': {
        "name": 'Contingency Plan'
    },
    'Advanced Stichwing': {
        "name": 'Advanced Stitchwing'
    },
    'Power of the Moon':{
        "name": 'Lunar Force'
    },
    'Lunarch Mantle':{
        "type": 'Enchantment - Aura'
    },
    'Choking Restraints':{
        "type": 'Enchantment - Aura'
    },
    'Faithbearer Paladin ':{
        "name": 'Faithbearer Paladin'
    },
    'Faith Bender':{
        "name": 'Fiend Binder'
    },
    'Geist of the Lonely Vgil':{
        "name": 'Geist of the Lonely Vigil'
    },
    'Vidlin-Pack Outcast': {
        "name": 'Vildin-Pack Outcast'
    },
    'Decimator of the Provices': {
        "altname": 'Decimator of Provinces'
    },
    'Tamiyo, Field Researcher': {
        'loyalty': 4
    },
    'Stromkirk Occultist': {
        'altname': 'Stormkirk Mystic'
    },
    'Gnarlwood Dryad': {
        'type': 'Creature - Dryad Horror'
    },
    'Hanweir, the Writhing Township': {
        'img': 'http://mythicspoiler.com/emn/cards/hanweirthewrithingtownship.jpg',
        'colorIdentityArray': ["R"]
    },
    'Brisela, Voice of Nightmares': {
        'img': 'http://mythicspoiler.com/emn/cards/briselavoiceofnightmares.jpg',
        'colorIdentityArray': ["W"]
    },
    'Chittering Host': {
        'img': 'http://mythicspoiler.com/emn/cards/chitteringhost.jpg',
        'colorIdentityArray': ["B"]
    },
    'Liliana, the Last Hope': {
        'loyalty': 3
    },
    'Selfless Spirit': {
        'altname': 'Selfless Soul'
    },
    'Nephalia Acadamy': {
        'name': 'Nephalia Academy'
    },
    'Distended Mindbender': {
        'pow': '5/5'
    },
    'Fortune\'s Favor': {
        'cost': '3U'
    },
    'Dark Salvation': {
        'cost': 'XXB'
    },
    'Lupine Prototype': {
        'pow': '5/5'
    },
    'Spontaenous Mutation': {
        'name': 'Spontaneous Mutation'
    },
    'Nebegast Herald': {
        'name': 'Nebelgast Herald'
    },
    'Enlightend Maniac': {
        'name': 'Enlightened Maniac'
    }
}

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

manual_cards = [
]

def get_cards():
    text = requests.get(SPOILER_RSS).text
    d = feedparser.parse(text)

    cards = []
    for entry in d.items()[5][1]:
    #for entry in d.items()[5][1][:5]:
        card = dict(cost='',cmc='',img='',pow='',name='',rules='',type='',
                color='', altname='', colorIdentity='', colorArray=[], colorIdentityArray=[], setnumber='', rarity='')
        summary = entry['summary']
        for pattern in patterns:
            match = re.search(pattern, summary, re.MULTILINE|re.DOTALL)
            if match:
                dg = match.groupdict()
                card[dg.items()[0][0]] = dg.items()[0][1]
        cards.append(card)

    for manual_card in manual_cards:
        inCards = False
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
        #print 'Inserting manual card: ' + manual_card['name']
        for card in cards:
            if card['name'] == manual_card['name']:
                inCards = True
        if not (inCards):
            #print 'Inserting manual card: ' + manual_card['name']
            cards.append(manual_card)
    return cards

def correct_cards(cards):
    for card in cards:
        if card['name'] == 'Chaoeveler':
            cards.remove(card)
        elif card['name'] == 'GrizAngler':
            cards.remove(card)
        card['name'] = card['name'].replace('&#x27;', '\'')
        card['rules'] = card['rules'].replace('&#x27;', '\'') \
            .replace('&lt;i&gt;', '') \
            .replace('&lt;/i&gt;', '') \
            .replace('&quot;', '"') \
            .replace('blkocking', 'blocking').replace('&amp;bull;','*')\
            .replace('comes into the','enters the')
        if card['name'] in card_corrections:
            for correction in card_corrections[card['name']]:
                if correction == 'name':
                    card['rules'] = card['rules'].replace(card['name'],card_corrections[card['name']][correction])
                card[correction] = card_corrections[card['name']][correction]

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

    #cards.append(cost='',cmc='',img='',pow='',name='',rules='',type='',
    #            color='', altname='', colorIdentity='', colorArray=[], colorIdentityArray=[], setnumber='', rarity='')
    return cards

def add_images(cards):
    text = requests.get(IMAGES).text
    text2 = requests.get(IMAGES2).text
    text3 = requests.get(IMAGES3).text
    wotcpattern = r'<img alt="{}.*?" src="(?P<img>.*?\.png)"'
    mythicspoilerpattern = r' src="emn/cards/{}.*?.jpg">'
    for c in cards:
        match = re.search(wotcpattern.format(c['name'].replace('\'','&rsquo;')), text, re.DOTALL)
        if not c['img']:
            if match:
                c['img'] = match.groupdict()['img']
            else:
                match3 = re.search(wotcpattern.format(c['name'].replace('\'','&rsquo;')), text3, re.DOTALL)
                if match3:
                    c['img'] = match3.groupdict()['img']
                else:
                    #disable mythicspoiler now that we're fully spoiled
                    #match2 = re.search(mythicspoilerpattern.format((c['name']).lower().replace(' ', '').replace('&#x27;', '').replace('-', '').replace('\'','').replace(',', '')), text2, re.DOTALL)
                    #if match2:
                        #print match2.group(0).replace(' src="', 'http://mythicspoiler.com/').replace('">', '')
                    #    c['img'] = match2.group(0).replace(' src="', 'http://mythicspoiler.com/').replace('">', '')
                    #else:
                    print('image for {} not found'.format(c['name']))
                    # print('we checked mythic for ' + c['altname'])
                    pass


def make_json(cards, setjson):
    #initialize mtg format json
    cardsjson = {
        "block": "Shadows over Innistrad",
        "border": "black",
        "code": "EMN",
        "magicCardsInfoCode": "emn",
        "name": "Eldritch Moon",
        "releaseDate": "2016-07-22",
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
            "marketing",
            "double-faced"
        ],
        "cards": []
    }
    for card in cards:
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
        #cardjson["id"] = hashlib.sha1('EMN' + card['name'] + str(card['name']).lower()).hexdigest()
        cardjson["cmc"] = card['cmc']
        cardjson["manaCost"] = card['cost']
        cardjson["name"] = card['name']
        cardjson["number"] = cardnumber
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
    with open(setjson, 'w') as outfile:
        json.dump(cardsjson, outfile, sort_keys=True, indent=2, separators=(',', ': '))
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
    #create dict of DFC sorted by library                
    #for specialrarity in specialjson:
        #print specialrarity + ': [
        #for name in specialjson[specialrarity]:
        #    print '"' + name + '"'
       # print "]"
    return cardsjson

def write_xml(mtgjson, cardsxml):
    cardsxml = open(cardsxml, 'w')
    cardsxml.truncate()
    count = 0
    dfccount = 0
    newest = ''
    related = 0
    cardsxml.write("<?xml version='1.0' encoding='UTF-8'?>\n<cockatrice_carddatabase version='3'>\n<sets>\n<set>\n<name>EMN</name>\n<longname>Eldritch Moon</longname>\n<settype>Expansion</settype>\n<releasedate>2016-07-22</releasedate>\n</set>\n</sets>\n<cards>")
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
        cardsxml.write('<set rarity="' + card['rarity'] + '" picURL="' + card["url"] + '">EMN</set>\n')
        cardsxml.write("<manacost>" + manacost.encode('utf-8') + "</manacost>\n")
        cardsxml.write("<cmc>" + str(card['cmc']) + "</cmc>")
        if card.has_key('colors'):
            for color in card['colors']:
                cardsxml.write('<color>' + color + '</color>')
        #add 'CIPT' tag to enters the battlefield tapped cards            
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
    print 'Time: ' + str(datetime.datetime.today().strftime('%H:%M'))

    return newest

def writehtml(newest):
    f = open(html, 'r')
    lines = f.readlines()
    lines[26] = newest + '\n'
    lines[28] = str(datetime.date.today()) + '\n'
    lines[30] = str(datetime.datetime.today().strftime('%H:%M')) + '\n'
    f.close()

    f = open(html, 'w')
    f.writelines(lines)
    f.close()

if __name__ == '__main__':
    cards = get_cards()
    cards = correct_cards(cards)
    #for some reason bedlam reveler doesn't get caught the first time through... unicode?
    cards = correct_cards(cards)
    add_images(cards)
    mtgjson = make_json(cards, setjson)
    newest = write_xml(mtgjson, cardsxml)
    #writehtml(newest)
