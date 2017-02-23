# masters.py is a script to assist in the handling of masters sets
# these sets are entirely made of reprints. the only new information
# we care about is their new art and their rarity. WOTC does not include
# rarity on the spoiler page, so we're going to have to figure out out.
# The set symbol on current sets is color coded based on rarity.
# Find out the location of the biggest chunk of rarity-colored pixels
# in a card image, and put that in as 'symbolPixels'.  If a card doesn't
# have a set symbol in the normal area, it should have a larger variance
# from the average color of symbols.  Max variance from images with correct
# set symbol placement is about *7*, we set the alarm rate at 10.

from lxml import html
import requests
import urllib
import os
from PIL import Image
import json
import time

setname = 'EMA'

# we're going to sample a 2x8 box from the set symbol
symbolPixels = (233, 213, 241, 214)

highVariance = 10

def scrapeCards():
    page = requests.get('http://magic.wizards.com/en/articles/archive/card-image-gallery/eternal-masters')
    tree = html.fromstring(page.content)

    cards = []

    cardtree = tree.xpath('//*[@id="content-detail-page-of-an-article"]')

    for child in cardtree:
        cardElements = child.xpath('//*/p/img')
        for cardElement in cardElements:
            card = {
                "name": cardElement.attrib['alt'],
                "img": cardElement.attrib['src']
            }
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
        "Common": [10, 10, 10],
        "Uncommon": [176, 212, 224],
        "Rare": [217, 195, 130],
        "Mythic Rare": [242, 142, 20]
    }
    for card in cards:
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
            print card['name'], ' has high variance of ', variance, ', closest rarity is ', card['rarity']
            card['rarity'] = "Mythic Rare"
            # print card['name'], reds, greens, blues
            # setSymbol.save('images/' + card['name'] + '.symbol.jpg')
    return cards

if __name__ == '__main__':
    cards = scrapeCards()
    downloadImages(cards)
    cards = getRarity(cards)
    print cards
    with open(setname + '.json', 'w') as outfile:
        json.dump(cards, outfile, sort_keys=True, indent=2, separators=(',', ': '))
