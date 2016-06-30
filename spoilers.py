import requests
import feedparser
import re

SPOILER_RSS = 'http://www.mtgsalvation.com/spoilers.rss'
IMAGES = 'http://magic.wizards.com/en/content/eldritch-moon-cards'
IMAGES2 = 'http://mythicspoiler.com/newspoilers.html'


related_cards = {'Gisela, the Broken Blade':'Brisela, Voice of Nightmares',
        'Bruna, the Fading Light':'Brisela, Voice of Nightmares',
        'Ulrich of the Krallenhorde':'Ulrich, Uncontested Alpha',
        'Lone Rider':'It That Rides as One',
        'Grizzled Angler':'Grisly Anglerfish',
        'Docent of Perfection':'Final Iteration',
        'Cryptolith Fragment':'Aurora of Emrakul',
        'Hanweir Battlements':'Hanweir, the Writhing Township',
        'Hanweir Garrison':'Hanweir, the Writhing Township',
        'Midnight Scavengers':'Chittering Host',
        'Graf Rats':'Chittering Host',
        }


patterns = ['<b>Name:</b> <b>(?P<name>.*?)<',
            'Cost: (?P<cost>\d{0,2}[WUBRGC]*?)<',
            'Type: (?P<type>.*?)<',
            'Pow/Tgh: (?P<pow>.*?)<',
            'Rules Text: (?P<rules>.*?)<br /'
            ]

def get_cards():
    text = requests.get(SPOILER_RSS).text
    d = feedparser.parse(text)
   
    cards = []
    for entry in d.items()[5][1]:
        card = dict(cost='',cmc='',img='',pow='',name='',rules='',type='',
                color='', altname='')
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
        card['altname'] = card['name']
        if (card['name'] == 'Vidlin-Pack Outcast'):
            card['name'] = 'Vildin-Pack Outcast'
            card['altname'] = 'Vildin-Pack Outcast'
        elif (card['name'] == 'Decimator of the Provinces'):
            card['altname'] = 'Decimator of Provinces'
        elif (card['name'] == 'GrizAngler'):
            card['name'] = 'Grizzled Angler'
            card['altname'] = 'Grizzled Angler'
        elif (card['name'] == 'Stitcher&#x27;s Graft'):
            card['altname'] = 'Graft Stapler'
        elif (card['name'] == 'Emrakul&#x27;s Influence'):
            card['altname'] = 'Influence of Emrakul'


def add_images(cards):
    text = requests.get(IMAGES).text
    text2 = requests.get(IMAGES2).text
    
    wotc_pattern = r'<img alt="{}.*?" src="(?P<img>.*?\.png)"'
    mythic_pattern = r' src="emn/cards/{}.*?.jpg">'
    for c in cards:
        match = re.search(wotc_pattern.format(c['name']), text, re.DOTALL)
        if match:
            c['img'] = match.groupdict()['img']
        else: 
            match2 = re.search(mythic_pattern.format(
                (c['altname']).lower().replace(' ','')
                                      .replace('&#x27;','')
                                      .replace('-','')), text2, re.DOTALL)
            if match2:
                c['img'] = (match2.group(0)
                        .replace('src="','http://mythicspoiler.com/')
                        .replace('">',''))
def make_xml(cards):
    print """<cockatrice_carddatabase version="3">
    <sets>
        <set>
            <name>EMN</name>
            <longname>Eldritch Moon</longname>
            <settype>Custom</settype>
            <releasedate></releasedate>
        </set>
    </sets>
    <cards>
    """
    for card in cards:
      try:
        # figure out cmc from cost
        if 'cost' in card and len(card['cost']) > 0:
            m = re.search('(\d+)', card['cost'])
            cmc = 0
            if m:
                cmc += int(m.group())
                cmc += len(card['cost']) - 1 # account for colored symbols
            else:
                cmc += len(card['cost']) # all colored symbols
            card['cmc'] = cmc
        # figure out color
        for c in 'WUBRG' :
            if c in card['cost']:
                card['color'] += c
        print """
<card>
	<name>{name}</name>
    <set picURL="{img}">EMN</set>
    <color>{color}</color>
    <manacost>{cost}</manacost>
    <cmc>{cmc}</cmc>
    <type>{type}</type> 
    <pt>{pow}</pt>
    <tablerow>2</tablerow>
    <text>{rules}</text>
        """.format(**card)
        if card['name'] in related_cards:
            print "    <related>{}</related>".format(related_cards[card['name']])
        print "</card>"
      except Exception as e:
          print card
          raise

    print """</cards>
    </cockatrice_carddatabase>
    """

if __name__ == '__main__':
    cards = get_cards()
    add_images(cards)
    make_xml(cards)
