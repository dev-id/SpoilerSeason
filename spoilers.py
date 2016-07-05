# -*- coding: utf-8 -*-
import datetime
import requests
import feedparser
import re
import json

setname = 'EMN'
setjson = setname + '.json'
cardsxml = setname + '.xml'
html = 'index.html'

SPOILER_RSS = 'http://www.mtgsalvation.com/spoilers.rss'
IMAGES = 'http://magic.wizards.com/en/content/eldritch-moon-cards'
IMAGES2 = 'http://mythicspoiler.com/newspoilers.html'

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
                 'Voldaren Pariah': 'Abolisher of Bloodlines'
                 }

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
    fix_cards(cards)

    return cards

def fix_cards(cards):
    for card in cards:
        card['name'] = card['name'].replace('&#x27;','\'')
        card['rules'] = card['rules'].replace('&#x27;','\'').replace('&lt;i&gt;','').replace('&lt;/i&gt;','').replace('&quot;','"')
        card['altname'] = card['name']
        if (card['name'] == 'Vidlin-Pack Outcast'):
            card['name'] = 'Vildin-Pack Outcast'
            card['altname'] = 'Vildin-Pack Outcast'
        if (card['name'] == 'Decimator of the Provinces'):
            card['altname'] = 'Decimator of Provinces'
        if (card['name'] == 'GrizAngler'):
            card['name'] = 'Grizzled Angler'
            card['altname'] = 'Grizzled Angler'
        if (card['name'] == 'Stitcher&#x27;s Graft') or (card['name'] == 'Stitcher\'s Graft'):
            #card['altname'] = 'Graft Stapler'
            card['img'] = 'http://media.wizards.com/2016/ouhtebrpjwxcnw5_EMN/en_h2Hu65ff7l.png'
        if (card['name'] == 'Emrakul\'s Influence'):
            #card['altname'] = 'Influence of Emrakul'
            card['img'] = 'http://media.wizards.com/2016/ouhtebrpjwxcnw5_EMN/en_h2Hu65ff7l.png'
        if (card['name'] == 'Tamiyo, Field Researcher'):
            card['loyalty'] = 4
        if (card['name'] == 'Stromkirk Occultist'):
            card['altname'] = 'Stormkirk Mystic'
        if (card['name'] == 'Gnarlwood Dryad'):
            card['type'] = "Creature - Dryad Horror"
        if (card['name'] == 'Hanweir, the Writhing Township'):
            card['img'] = 'http://mythicspoiler.com/emn/cards/hanweirthewrithingtownship.jpg'
        if (card['name'] == 'Brisela, Voice of Nightmares'):
            card['img'] = 'http://mythicspoiler.com/emn/cards/briselavoiceofnightmares.jpg'
        if (card['name'] == 'Chittering Host'):
            card['img'] = 'http://mythicspoiler.com/emn/cards/chitteringhost.jpg'
        if ('Liliana,') in card['name']:
            card['loyalty'] = 3
        if (card['name'] == 'Selfless Spirit'):
            card['altname'] = 'Selfless Soul'
        if (card['name'] == 'Nephalia Acadamy'):
            card['name'] = 'Nephalia Academy'
            card['altname'] = 'Nephalia Academy'
        if (card['name'] == 'Distended Mindbender'):
            card['pow'] = '5/5'
        if (card['name'] == 'Collective Resistance'):
            card['img'] = 'http://media-dominaria.cursecdn.com/avatars/125/491/636032361836090807.png'
        if ('Writhing Township') in card['name']:
            card['colorIdentityArray'] = ["R"]
        if ('Brisela,') in card['name']:
            card['colorIdentityArray'] = ["W"]
        if ('Chittering Host') in card['name']:
            card['colorIdentityArray'] = ["B"]
        #if ('Lashweed Lurker') in card['name']:
        #    card['colorIdentityArray'] = ["U","G"]

def add_images(cards):
    text = requests.get(IMAGES).text
    text2 = requests.get(IMAGES2).text
    wotcpattern = r'<img alt="{}.*?" src="(?P<img>.*?\.png)"'
    mythicspoilerpattern = r' src="emn/cards/{}.*?.jpg">'
    for c in cards:
        match = re.search(wotcpattern.format(c['name']), text, re.DOTALL)
        if match:
            c['img'] = match.groupdict()['img']
        else:
            match2 = re.search(mythicspoilerpattern.format((c['altname']).lower().replace(' ','').replace('&#x27;','').replace('-','').replace('\'','').replace(',','')), text2, re.DOTALL)
            if match2:
                c['img'] = match2.group(0).replace(' src="','http://mythicspoiler.com/').replace('">','')
            else:
                print('image for {} not found'.format(c['name']))
                #print('we checked mythic for ' + c['altname'])
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
        for namematch in related_cards:
            if card['name'] == related_cards[namematch]:
                card['layout'] = 'double-faced'
                cardnames.append(namematch)
                if not card['name'] in cardnames:
                    cardnames.append(card['name'])
                    cardnumber += 'b'
        cardtypes = []
        if not '-' in card['type']:
            cardtypes.append(card['type'])
        else:
            cardtypes = card['type'].replace('Legendary ','').split('-')[0].split(' ')[:-1]
        if card['cmc'] == '':
            card['cmc'] = 0
        cardjson = {}
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
    return cardsjson

def prep_xml(cards):
    for card in cards:
        if 'cost' in card and len(card['cost']) > 0:
            m = re.search('(\d+)', card['cost'])
            cmc = 0
            if m:
                cmc += int(m.group())
                cmc += len(card['cost']) - 1  # account for colored symbols
            else:
                cmc += len(card['cost'])  # all colored symbols
            card['cmc'] = cmc
    # figure out color
        for c in 'WUBRG':
            if c in card['cost']:
                card['color'] += c
                card['colorIdentity'] += c
            if (c + '}') in card['rules'] or (str.lower(c) + '}') in card['rules']:
                if not (c in card['colorIdentity']):
                    card['colorIdentity'] += c

#make_xml from previous iteration, prefer my implementation in write_xml
def make_xml(cards):
    cardsxml.write("""<cockatrice_carddatabase version="3">
    <sets>
        <set>
            <name>EMN</name>
            <longname>Eldritch Moon</longname>
            <settype>Expansion</settype>
            <releasedate>2016-07-22</releasedate>
        </set>
    </sets>
    <cards>
    """)
    for card in cards:
        cardsxml.write("""
<card>
    <name>{name}</name>
    <set rarity="{rarity}" picURL="{img}">EMN</set>
    <color>{color}</color>
    <manacost>{cost}</manacost>
    <cmc>{cmc}</cmc>
    <type>{type}</type>
    <pt>{pow}</pt>

    <tablerow>2</tablerow>
    <text>{rules}</text>
</card>
        """.format(**card))

    cardsxml.write("""</cards>
    </cockatrice_carddatabase>
    """)

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
        if card.has_key("manacost"):
            manacost = card["manacost"].replace('{', '').replace('}', '')
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
        cardsxml.write("<type>" + cardtype.encode('utf-8') + "</type>\n")
        if pt:
            cardsxml.write("<pt>" + pt + "</pt>\n")
        if card.has_key('loyalty'):
            cardsxml.write("<loyalty>" + str(card['loyalty']) + "</loyalty>")
        cardsxml.write("<tablerow>" + tablerow + "</tablerow>\n")
        cardsxml.write("<text>" + text.encode('utf-8') + "</text>\n")
        if related:
            cardsxml.write("<related>" + related.encode('utf-8') + "</related>\n")
            related = ''

        cardsxml.write("</card>\n")

    cardsxml.write("</cards>\n</cockatrice_carddatabase>")

    print 'XML STATS'
    print 'Total cards: ' + str(count)
    if (dfccount > 0):
      print 'DFC: ' + str(dfccount)
    print 'Newest: ' + str(newest)
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
    add_images(cards)
    prep_xml(cards)
    #make_xml(cards)
    mtgjson = make_json(cards, setjson)
    newest = write_xml(mtgjson, cardsxml)
    # writehtml is an announce page that lists the newest card spoiled and the date of the script's last run
    # disabled by default
    #writehtml(newest)
