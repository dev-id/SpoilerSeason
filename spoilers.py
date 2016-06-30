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
    #for entry in d.items()[5][1][:5]:
        card = dict(cost='',cmc='',img='',pow='',name='',rules='',type='',
                color='')
        summary = entry['summary']
        for pattern in patterns:
            match = re.search(pattern, summary, re.MULTILINE|re.DOTALL)
            if match:
                dg = match.groupdict()
                card[dg.items()[0][0]] = dg.items()[0][1]
        cards.append(card)

    return cards

def add_images(cards):
    text = requests.get(IMAGES).text
    
    pattern = r'<img alt="{}.*?" src="(?P<img>.*?\.png)"'
    for c in cards:
        match = re.search(pattern.format(c['name']), text, re.DOTALL)
        if match:
            c['img'] = match.groupdict()['img']
        else:
            pass
            #print('image for {} not found'.format(c['name']))

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
