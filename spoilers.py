# -*- coding: utf-8 -*-
import requests
import feedparser
import re
import sys
import os
import shutil
import time
from lxml import html
from PIL import Image
import datetime
import urllib
import json

def scrape_mtgs(url):
    return requests.get(url, headers={'Cache-Control':'no-cache', 'Pragma':'no-cache', 'Expires': 'Thu, 01 Jan 1970 00:00:00 GMT'}).text

def parse_mtgs(mtgs, manual_cards=[], card_corrections=[], delete_cards=[], split_cards=[], related_cards=[]):
    patterns = ['<b>Name:</b> <b>(?P<name>.*?)<',
                'Cost: (?P<cost>\d{0,2}[WUBRGC]*?)<',
                'Type: (?P<type>.*?)<',
                'Pow/Tgh: (?P<pow>.*?)<',
                'Rules Text: (?P<rules>.*?)<br /',
                'Rarity: (?P<rarity>.*?)<',
                'Set Number: #(?P<setnumber>.*?)/'
                ]
    d = feedparser.parse(mtgs)

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

    cardlist = []
    cardarray = []
    for card in cards:
        dupe = False
        for dupecheck in cardarray:
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

        cardarray.append(cardjson)

    return {"cards": cardarray}

def get_scryfall(setUrl):
    #getUrl = 'https://api.scryfall.com/cards/search?q=++e:'
    #setUrl = getUrl + setname.lower()
    setDone = False
    scryfall = []

    #firstPass = True
    while setDone == False:
        setcards = requests.get(setUrl)
        setcards = setcards.json()
        if setcards.has_key('data'):
                #if firstPass:
                #    cards[set]["cards"] = []
                #    firstPass = False
            scryfall.append(setcards['data'])
                #for setkey in mtgjson[set]:
                #    if 'card' not in setkey:
                #        if set != 'NMS':
                #            cards[set][setkey] = mtgjson[set][setkey]
        else:
            setDone = True
            print setUrl
            print setcards
            print 'No data - ' + set
                #noset.append(set)
        time.sleep(.1)
        if setcards.has_key('has_more'):
            if setcards['has_more'] == True:
                #print 'Going to extra page of ' + set
                setUrl = setcards['next_page']
            else:
                setDone = True
        else:
            setDone = True
    #return scryfall
    convert_scryfall(scryfall)
    return scryfall
    print

def convert_scryfall(scryfall):
    cards2 = []
    for card in scryfall:
        card2 = {}
        card2['cmc'] = int((card['converted_mana_cost']).split('.')[0])
        if card.has_key('mana_cost'):
            card2['manaCost'] = card['mana_cost'].replace('{','').replace('}','')
        else:
            card2['manaCost'] = ''
        card2['name'] = card['name']
        card2['number'] = card['collector_number']
        card2['rarity'] = card['rarity'].replace('mythic','mythic rare').title()
        if card.has_key('oracle_text'):
            card2['text'] = card['oracle_text'].replace(u"\u2022 ", u'*').replace(u"\u2014",'-').replace(u"\u2212","-")
        else:
            card2['text'] = ''
        card2['url'] = card['image_uri']
        card2['type'] = card['type_line'].replace(u'—','-')
        cardtypes = card['type_line'].split(u' — ')[0].replace('Legendary ','').replace('Snow ','')\
        .replace('Elite ','').replace('Basic ','').replace('World ','').replace('Ongoing ','')
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
            if not card['colors'] == []:
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
                #card2['colors'] = card['colors']
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
            card2['loyalty'] = card['loyalty']
        if card.has_key('artist'):
            card2['artist'] = card['artist']
        #if card.has_key('source'):
        #    card2['source'] = card['source']
        #if card.has_key('rulings'):
        #    card2['rulings'] = card['rulings']
        if card.has_key('flavor_text'):
            card2['flavor'] = card['flavor_text']
        if card.has_key('multiverse_id'):
            card2['multiverseid'] = card['multiverse_id']

        cards2['cards'].append(card2)

    return cards2
    print

def scrape_fullspoil(url, showRarityColors=False, showFrameColors=False, manual_cards=[], delete_cards=[], split_cards=[]):
    page = requests.get(url)
    tree = html.fromstring(page.content)
    cards = []
    cardtree = tree.xpath('//*[@id="content-detail-page-of-an-article"]')
    for child in cardtree:
        cardElements = child.xpath('//*/p/img')
        cardcount = 0
        for cardElement in cardElements:
            card = {
                "name": cardElement.attrib['alt'].replace(u"\u2019",'\'').split(' /// ')[0],
                "img": cardElement.attrib['src']
            }
            card["url"] = card["img"]
            card["cmc"] = 0
            card["manaCost"] = ""
            card["type"] = "Land"
            card["types"] = ["Land"]
            card["text"] = ""
            #card["colorIdentity"] = [""]

            if card['name'] in split_cards:
                card["names"] = [card['name'], split_cards[card['name']]]
                card["layout"] = "split"
            notSplit = True
            for backsplit in split_cards:
                if card['name'] == split_cards[backsplit]:
                    notSplit = False
            if notSplit and not card['name'] in delete_cards:
                cards.append(card)
            cardcount += 1
    print "Spoil Gallery has " + str(cardcount) + " cards."
    #print mtgjson
    #print cards
    #return cards
    get_rarities_by_symbol(fullspoil, showRarityColors)
    get_colors_by_frame(fullspoil, showFrameColors)
    return cards

def get_rarities_by_symbol(fullspoil, split_cards=[]):
    symbolPixels = (234, 215, 236, 218)
    highVariance = 15
    colorAverages = {
        "Common": [225, 224, 225],
        "Uncommon": [194, 228, 240],
        "Rare": [225, 201, 134],
        "Mythic Rare": [249, 163, 15]
    }
    #symbolCount = 0
    for card in fullspoil:
        cardImage = Image.open('images/' + card['name'] + '.png')
        if card['name'] in split_cards:
            setSymbol = cardImage.crop((234, 134, 236, 137))
        else:
            setSymbol = cardImage.crop(symbolPixels)
        cardHistogram = setSymbol.histogram()
        reds = cardHistogram[0:256]
        greens = cardHistogram[256:256 * 2]
        blues = cardHistogram[256 * 2: 256 * 3]
        reds = sum(i * w for i, w in enumerate(reds)) / sum(reds)
        greens = sum(i * w for i, w in enumerate(greens)) / sum(greens)
        blues = sum(i * w for i, w in enumerate(blues)) / sum(blues)
        variance = 768
        for color in colorAverages:
            colorVariance = 0
            colorVariance = colorVariance + abs(colorAverages[color][0] - reds)
            colorVariance = colorVariance + abs(colorAverages[color][1] - greens)
            colorVariance = colorVariance + abs(colorAverages[color][2] - blues)
            if colorVariance < variance:
                variance = colorVariance
                card['rarity'] = color
        if variance > highVariance:
            # if a card isn't close to any of the colors, it's probably a planeswalker? make it mythic.
            print card['name'], 'has high variance of', variance, ', closest rarity is', card['rarity']
            card['rarity'] = "Mythic Rare"
            print card['name'], '$', reds, greens, blues
        #if symbolCount < 10:
        #setSymbol.save('images/' + card['name'] + '.symbol.jpg')
        #    symbolCount += 1
    return fullspoil
    print

def get_colors_by_frame(fullspoil, split_cards=[]):
    framePixels = (20, 11, 76, 16)
    highVariance = 10
    colorAverages = {
        "White": [231,225,200],
        "Blue": [103,193,230],
        "Black": [58, 61, 54],
        "Red": [221, 122, 101],
        "Green": [118, 165, 131],
        "Multicolor": [219, 200, 138],
        "Artifact": [141, 165, 173],
        "Colorless": [216, 197, 176],
    }
    #symbolCount = 0
    for card in fullspoil:
        cardImage = Image.open('images/' + card['name'] + '.png')
        if card['name'] in split_cards:
            continue
            #setSymbol = cardImage.crop((234, 134, 236, 137))
        #else:
        cardColor = cardImage.crop(framePixels)

        cardHistogram = cardColor.histogram()
        reds = cardHistogram[0:256]
        greens = cardHistogram[256:256 * 2]
        blues = cardHistogram[256 * 2: 256 * 3]
        reds = sum(i * w for i, w in enumerate(reds)) / sum(reds)
        greens = sum(i * w for i, w in enumerate(greens)) / sum(greens)
        blues = sum(i * w for i, w in enumerate(blues)) / sum(blues)
        variance = 768
        for color in colorAverages:
            colorVariance = 0
            colorVariance = colorVariance + abs(colorAverages[color][0] - reds)
            colorVariance = colorVariance + abs(colorAverages[color][1] - greens)
            colorVariance = colorVariance + abs(colorAverages[color][2] - blues)
            if colorVariance < variance:
                variance = colorVariance
                card['colors'] = [color]
        if variance > highVariance:
            # if a card isn't close to any of the colors, it's probably a planeswalker? make it mythic.
            #print card['name'], 'has high variance of', variance, ', closest rarity is', card['color']
            print card['name'], '$ colors $', reds, greens, blues
        #if 'Multicolor' in card['colors'] or 'Colorless' in card['colors'] or 'Artifact' in card['colors']:
        #    card['colors'] = []
        #if symbolCount < 10:
        #cardColor.save('images/' + card['name'] + '.symbol.jpg')
        #    symbolCount += 1
    return fullspoil

def get_image_urls(mtgjson, isfullspoil, setname, setlongname, setSize=269):
    IMAGES = 'http://magic.wizards.com/en/content/' + setlongname.lower().replace(' ', '-') + '-cards'
    IMAGES2 = 'http://mythicspoiler.com/newspoilers.html'
    IMAGES3 = 'http://magic.wizards.com/en/articles/archive/card-image-gallery/' + setlongname.lower().replace(' ', '-')

    text = requests.get(IMAGES).text
    text2 = requests.get(IMAGES2).text
    text3 = requests.get(IMAGES3).text
    wotcpattern = r'<img alt="{}.*?" src="(?P<img>.*?\.png)"'
    mythicspoilerpattern = r' src="' + setname.lower() + '/cards/{}.*?.jpg">'
    for c in mtgjson['cards']:
        match = re.search(wotcpattern.format(c['name'].replace('\'','&rsquo;')), text, re.DOTALL)
        if match:
            c['url'] = match.groupdict()['img']
        else:
            match3 = re.search(wotcpattern.format(c['name'].replace('\'','&rsquo;')), text3, re.DOTALL)
            if match3:
                c['url'] = match3.groupdict()['img']
            else:
                match2 = re.search(mythicspoilerpattern.format((c['name']).lower().replace(' ', '').replace('&#x27;', '').replace('-', '').replace('\'','').replace(',', '')), text2, re.DOTALL)
                if match2 and not isfullspoil:
                    c['url'] = match2.group(0).replace(' src="', 'http://mythicspoiler.com/').replace('">', '')
                pass
        #if ('Creature' in c['type'] and not c.has_key('power')) or ('Vehicle' in c['type'] and not c.has_key('power')):
        #    print(c['name'] + ' is a creature w/o p/t img: ' + c['url'])
        if len(str(c['url'])) < 10:
            print(c['name'] + ' has no image.')
    return mtgjson

def write_xml(mtgjson, setname, setlongname, setreleasedate, split_cards=[]):
    if not os.path.isdir('out/'):
        os.makedirs('out/')
    cardsxml = open('out/' + setname + '.xml', 'w+')
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
                        #print "We're skipping " + card['name'] + " because it's the right side of a split card"
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

def make_allsets(AllSets, mtgjson, setname):
    AllSets[setname] = mtgjson
    return AllSets

def scrape_masterpieces(url='http://www.mtgsalvation.com/spoilers/181-amonkhet-invocations', cardurl='http://www.mtgsalvation.com/cards/amonkhet-invocations/'):
    page = requests.get(url)
    tree = html.fromstring(page.content)
    cards = []
    cardstree = tree.xpath('//*[contains(@class, "log-card")]')
    for child in cardstree:
        #print child.text
        cardpage = requests.get(cardurl + child.attrib['data-card-id'] + '-' + child.text.replace(' ','-'))
        tree = html.fromstring(cardpage.content)
        cardtree = tree.xpath('//img[contains(@class, "card-spoiler-image")]')
        #print cardtree[0]
        card = {
            "name": child.text,
            "url": cardtree[0].attrib['src']
        }
        cards.append(card)
    return cards

def make_masterpieces(headers, AllSets, spoil):
    masterpieces = scrape_masterpieces(headers['mtgsurl'], headers['mtgscardpath'])
    masterpieces2 = []
    for masterpiece in masterpieces:
        matched = False
        for spoilcard in spoil['cards']:
            if spoilcard['name'] == masterpiece['name'] and not matched:
                mixcard = spoilcard
                mixcard['rarity'] = 'Mythic Rare'
                mixcard['url'] = masterpiece['url']
                masterpieces2.append(mixcard)
                matched = True
        for set in AllSets:
            if not matched:
                for oldcard in AllSets[set]['cards']:
                    if oldcard['name'] == masterpiece['name'] and not matched:
                        mixcard = oldcard
                        mixcard['url'] = masterpiece['url']
                        mixcard['rarity'] = 'Mythic Rare'
                        masterpieces2.append(mixcard)
                        matched = True
        if not matched:
            print "We couldn't find a card object to assign the data to for masterpiece " + masterpiece['name']
            masterpieces2.append(masterpiece)
    mpsjson = {
        "name": headers['setlongname'],
        "alternativeNames": headers['alternativeNames'],
        "code": "MPS_AKH",
        "releaseDate": headers['setreleasedate'],
        "border": "black",
        "type": "masterpiece",
        "cards": masterpieces2
    }
    return mpsjson

def get_allsets():
    class MyOpener(urllib.FancyURLopener):
        version = 'Mozilla/5.0 (Windows; U; Windows NT 5.1; it; rv:1.8.1.11) Gecko / 20071127 Firefox / 2.0.0.11'

    opener = MyOpener()
    opener.retrieve('http://mtgjson.com/json/AllSets.json', 'AllSets.pre.json')
    with open('AllSets.pre.json') as data_file:
        AllSets = json.load(data_file)
    return AllSets

def add_headers(mtgjson, setinfos):
    mtgjson2 = {
        "block": setinfos['blockname'],
        "border": "black",
        "code": setinfos['setname'],
        "magicCardsInfoCode": setinfos['setname'].lower(),
        "name": setinfos['setlongname'],
        "releaseDate": setinfos['setreleasedate'],
        "type": setinfos['settype'],
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
        "cards": mtgjson['cards']
    }
    return mtgjson2
