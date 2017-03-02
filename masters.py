# -*- coding: utf-8 -*-

# masters.py is a script to assist in the handling of masters sets.
# These sets are entirely made of reprints. the only new information
# we care about is their new art and their rarity. WOTC does not include
# rarity on the spoiler page, so we're going to have to figure out out.
# The set symbol on current sets is color coded based on rarity.
# Find out the location of the biggest chunk of rarity-colored pixels
# in a card image, and put that in as 'symbolPixels'.  If a card doesn't
# have a set symbol in the normal area, it should have a larger variance
# from the average color of symbols.  Max variance from images with correct
# set symbol placement is about *7*, we set the alarm rate at 10.

import io
from lxml import html
import requests
import urllib
import os
from PIL import Image
import json
import time

setname = 'MM3'

# we're going to sample a 2x8 box from the set symbol
symbolPixels = (231, 222, 238, 224)

highVariance = 10

def scrapeCards():
    page = requests.get('http://magic.wizards.com/en/articles/archive/card-image-gallery/modern-masters-2017-edition')
    tree = html.fromstring(page.content)

    cards = []

    cardtree = tree.xpath('//*[@id="content-detail-page-of-an-article"]')

    for child in cardtree:
        cardElements = child.xpath('//*/p/img')
        for cardElement in cardElements:
            card = {
                "name": cardElement.attrib['alt'].replace(u"\u2019",'\''),
                "img": cardElement.attrib['src']
            }
            card["url"] = card["img"]
            cards.append(card)

    return cards


def downloadImages(cards):
    for card in cards:
        if not os.path.isdir('images/' + setname):
            os.makedirs('images/' + setname)
        for card in cards:
            if card['img']:
                if os.path.isfile('images/' + setname + '/' + card['name'] + '.png'):
                    continue
                print 'Downloading ' + card['img'] + ' to images/' + setname + '/' + card['name'] + '.png'
                urllib.urlretrieve(card['img'], 'images/' + setname + '/' + card['name'] + '.png')
                time.sleep(.2)


def getRarity(cards):
    colorAverages = {
        "Common": [11, 7, 8],
        "Uncommon": [175, 211, 223],
        "Rare": [212, 188, 119],
        "Mythic Rare": [235, 130, 22]
    }
    for card in cards:
        #card['name'] = 'Griselbrand'
        cardImage = Image.open('images/' + setname + '/' + card['name'] + '.png')
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
            #print card['name'], '$', reds, greens, blues
        #setSymbol.save('images/' + card['name'] + '.symbol.jpg')
    return cards

def concatmtgjson(mastersCards):
    mastersSet = {
        "name": "Modern Masters 2017 Edition",
        "code": "MM3",
        "releaseDate": "2017-03-17",
        "border": "black",
        "type": "reprint",
        "booster": [["rare","mythic rare"],"uncommon","uncommon","uncommon","common","common","common","common","common","common","common","common","common","common",["foil mythic rare","foil rare","foil uncommon","foil common"]],
        "cards": []
    }
    manualCards = {}
    for card in manualCards:
        scraped = False
        for scrapedCard in mastersCards:
            if scrapedCard['name'] == card:
                scraped = True
                print 'Using scraped card for ' + str(card)
        if scraped == False:
            mastersCards.append({
                "name": card,
                "rarity": manualCards[card]
            })
    with open('AllCards.json') as data_file:
        allCards = json.load(data_file)
    with open('AllSets.json') as data_file:
        mtgjson = json.load(data_file)
    for card in mastersCards:
        allCard = allCards[card['name']]
        #
        if card.has_key('url'):
            allCard['url'] = card['url']
        else:
            cardfound = False
            for set in mtgjson:
                if (cardfound == False):
                    for setcard in mtgjson[set]['cards']:
                        if setcard['name'] == card['name']:
                            if setcard.has_key('multiverseid'):
                                allCard['url'] = "http://gatherer.wizards.com/Handlers/Image.ashx?multiverseid=" + unicode(setcard['multiverseid']) + "&type=card"
                                cardfound = True
                                continue

        allCard['rarity'] = card['rarity']
        mastersSet['cards'].append(allCard)
    mtgjson['MM3'] = mastersSet
    print mastersSet
    with open('AllSets.plus' + setname + '.json', 'w') as outfile:
        json.dump(mtgjson, outfile, sort_keys=True, indent=2, separators=(',', ': '))

if __name__ == '__main__':
    cards = scrapeCards()
    downloadImages(cards)
    cards = getRarity(cards)
    print cards
    with open(setname + '.json', 'w') as outfile:
        json.dump(cards, outfile, sort_keys=True, indent=2, separators=(',', ': '))
    concatmtgjson(cards)
