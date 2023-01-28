import requests
from bs4 import BeautifulSoup
import re
import sys
import os
import operator
import orodja


def pripravi_imenik(ime_datoteke):
    '''Če še ne obstaja, pripravi prazen imenik za dano datoteko.'''
    imenik = os.path.dirname(ime_datoteke)
    if imenik:
        os.makedirs(imenik, exist_ok=True)

# Del kode pridobljen: https://stackoverflow.com/questions/69780727/web-scraping-with-dopostback
def shrani_spletno_stran(url, st_strani, ime_datoteke, vsili_prenos=False):
    '''Vsebino strani na danem naslovu shrani v datoteko z danim imenom.'''
    try:
        print(f'Shranjujem {url} ...', end='')
        sys.stdout.flush()
        if os.path.isfile(ime_datoteke) and not vsili_prenos:
            print('shranjeno že od prej!')
            return
        page_content = requests.get(url).content
        soup = BeautifulSoup(page_content, 'html.parser')

        VIEWSTATEGENERATOR  = soup.find('input',{'id':'__VIEWSTATEGENERATOR'}).get('value')
        VIEWSTATE  = soup.find('input',{'id':'__VIEWSTATE'}).get('value')
        EVENTARGUMENT = f"Page${st_strani}"

        headers = {'user-agent': 'Mozilla/5.0'}
        data = {  
                "ctl00$ScriptManager1": "ctl00$ContentPlaceHolder1$ctlSets$UpdatePanelMain|ctl00$ContentPlaceHolder1$ctlSets$GridViewSets",
                "ctl00$txtSearchHeader2": "",
                "ctl00$txtSearchHeader": "",
                "subthemesorter": "",
                "setsorter": "SetNumberDESC",
                "ctl00$LoginModalUsername": "",
                "ctl00$LoginModalPassword": "",
                "__EVENTTARGET": "ctl00$ContentPlaceHolder1$ctlSets$GridViewSets",
                "__EVENTARGUMENT": EVENTARGUMENT,
                "__VIEWSTATE":VIEWSTATE,
                "__VIEWSTATEGENERATOR": VIEWSTATEGENERATOR, 
                "__ASYNCPOST": 'true'
        }
        r = requests.post(url, data=data, headers =headers).text
    except requests.exceptions.ConnectionError:
        print('stran ne obstaja!')
    else:
        pripravi_imenik(ime_datoteke)
        with open(ime_datoteke, 'w', encoding='utf-8') as datoteka:
            datoteka.write(r)
            print('shranjeno!')

def seti_v_letu(leto):
    url = f'https://www.brickeconomy.com/sets/year/{leto}'
    vsebina = requests.get(url).text
    vzorec = re.compile(r'<td nowrap>.*?<span class="text-muted">to</span>.*?<span class="text-muted">of</span> (?P<stevilo>.+?) <span class="text-muted">sets</span></td>', flags=re.DOTALL)
    blok = re.findall(vzorec, vsebina)
    stevilo_strani = int(blok[0]) // 50 + 1
    for i in range(1, stevilo_strani + 1):
        ime_datoteke = f'seti-v-letu-{leto}-st-{i}.html'
        path = os.path.join(f'strani-brickeconomy', ime_datoteke)
        shrani_spletno_stran(url, i, path)

def minifigure_v_letu(leto):
    url=f'https://brickset.com/minifigs/year-{leto}/page-1'
    vsebina = requests.get(url).text
    vzorec = re.compile(r"<div class='results'>1 to .*? of (?P<stevilo>.+?) matches</div>", flags=re.DOTALL)
    blok = re.findall(vzorec, vsebina)
    stevilo_strani = int(blok[0]) // 50 + 1
    for i in range(1, stevilo_strani + 1):
        url = f'https://brickset.com/minifigs/year-{leto}/page-{i}'
        ime_datoteke = f'minifigure-v-letu-{leto}-st-{i}.html'
        path = os.path.join(f'strani-brickset', ime_datoteke)
        orodja.shrani_spletno_stran(url, path)

vzorec_bloka_brickeconomy = re.compile(
    r'<td class="hidden-xs ctlsets-image">([\S\s]+?)<div id="ContentPlaceHolder1_ctlSets_GridViewSets_PanelUserWantOwn_(.*?)" class="ctlsets-wantown text-left hidden-xs">',
    flags=re.DOTALL
)

vzorec_seta = re.compile(
    r"""<div class="mb-5"><h4><a href="/set/.*?">(?P<stevilka>[\d|-]+?) (?P<ime>.+?)</a></h4></div>"""
    r""".*?<div class="mb-2"><small class="text-muted mr-5">Theme( / Subtheme)?</small> <a class="a-body" href="/sets/theme/"""
    r""".*?">(?P<tema>.+?)( / (?P<podtema>.+?))?</a></div>.*?<div class="mb-2"><small class="text-muted mr-5">Year</small> (?P<leto>\d+?)</div>"""
    r""".*?<div class="mb-2"><small class="text-muted mr-5">Pieces( / .+?)?</small> (?P<st_kock>[\d|,]+?)( / (?P<st_minifigur>\d\d?))?</div>"""
    r""".*?<div class="mb-2"><small class="text-muted mr-5">Availability</small> (?P<dostopnost>.+?)</div>""",
    flags=re.DOTALL
)

vzorec_msrp = re.compile(
    r"""<div><small class="text-muted mr-5">Retail</small> (?P<msrp>[\d|,]+?) €</div>""",
    flags=re.DOTALL
)

vzorec_vrednost = re.compile(
    r"""<div><small class="text-muted mr-5">Value</small> (?P<vrednost>[\d|,]+?) €</div>""",
    flags=re.DOTALL
)

vzorec_bloka_brickset = re.compile(
    r"""<article class='set'>([\s\S]+?)</div></article>""",
    flags=re.DOTALL
)

vzorec_minifigure = re.compile(
    r"""<img src="https:.*?" title="(?P<id>.+?): (?P<ime>.+?)" onError="this\.src='/assets/images/spacer2\.png'"""
    r""".*?<div class='meta'>.+?<a href='/minifigs/category-.*?'>(?P<tema>.+?)</a> <a class='subtheme' href='/minifigs/category-"""
    r""".*?'>(?P<podtema>.+?)</a> <a class='year' href='/minifigs/category-.*?/year-\d*'>(?P<leto>\d+?)</a>"""
    r""".+?<dl><dt>Appears In</dt><dd><a class='plain' href='/sets/containing-minifig-.*?'>(?P<st_setov>\d+?) sets?</a></dd>"""
    r""".*?(<dt>Appears In</dt><dd class='tags'>)?(<a href='/sets/.*?'>(?P<st_1>[\d|-]+?)</a> )?(<a href='/sets/.*?'>(?P<st_2>[\d|-]+?)</a> )?"""
    r"""(<a href='/sets/.*?'>(?P<st_3>[\d|-]+?)</a> )?(<a href='/sets/.*?'>(?P<st_4>[\d|-]+?)</a> )?(<a href='/sets/.*?'>(?P<st_5>[\d|-]+?)</a> )?</dd>""",
    #pobere številke setov, v katerih je figura (do 5)
    flags=re.DOTALL
)

vzorec_nove_figure = re.compile(
    r"""<dt>Value new</dt><dd><a class='plain' href='https://.*?'>~(?P<novo>.+?)</a></dd>""",
    flags=re.DOTALL
)

vzorec_rabljene_figure = re.compile(
    r"""<dt>Value used</dt><dd><a class='plain' href='https://.*?'>~(?P<rabljeno>.+?)</a></dd>""",
    flags=re.DOTALL
)

def izloci_podatke_seta(blok):
    komplet = vzorec_seta.search(blok)
    if komplet:
        komplet = komplet.groupdict()
        msrp = vzorec_msrp.search(blok)
        vrednost = vzorec_vrednost.search(blok)
        komplet['tema'] = komplet['tema'].strip('</a>')
        komplet['leto'] = int(komplet['leto'])
        komplet['st_kock'] = int(komplet['st_kock'].replace(',',''))
        komplet['stevilka'] = float(komplet['stevilka'].replace('-','.'))
        if komplet['podtema']:
            komplet['podtema'] = komplet['podtema'][komplet['podtema'].index('>')+1:]
        if komplet['st_minifigur']:
            komplet['st_minifigur'] = int(komplet['st_minifigur'])
        else:
            komplet['st_minifigur'] = 0
        if msrp:
            try:
                komplet['msrp'] = float(msrp['msrp'].replace(',','.'))
            except:
                komplet['msrp'] = msrp['msrp']
        else:
            komplet['msrp'] = None
        if vrednost:
            try:
                komplet['vrednost'] = float(vrednost['vrednost'].replace(',','.'))
            except:
                komplet['vrednost'] = vrednost['vrednost']
        else:
            komplet['vrednost'] = None
        return komplet
    else:
        pass
    
    
def izloci_podatke_minifigure(blok):
    minifigura = vzorec_minifigure.search(blok)
    if minifigura:
        minifigura = minifigura.groupdict()
        if not minifigura['st_5']:
            minifigura.pop('st_5')
        if not minifigura['st_4']:
            minifigura.pop('st_4')
        if not minifigura['st_3']:
            minifigura.pop('st_3')
        if not minifigura['st_2']:
            minifigura.pop('st_2')
        minifigura['leto'] = int(minifigura['leto'])
        minifigura['st_setov'] = int(minifigura['st_setov'])
        nova = vzorec_nove_figure.search(blok)
        rabljena = vzorec_rabljene_figure.search(blok)
        if nova:
            minifigura['novo'] = float(nova['novo'].strip('€'))
        else:
            minifigura['novo'] = None
        if rabljena:
            minifigura['rabljeno'] = float(rabljena['rabljeno'].strip('€'))
        else:
            minifigura['rabljeno'] = None
        return minifigura
    else:
        pass

def seti_v_datoteki(dat):
    vsebina = orodja.vsebina_datoteke('strani-brickeconomy', dat)
    for blok in vzorec_bloka_brickeconomy.finditer(vsebina):
        rtr = blok.group(0)
        yield izloci_podatke_seta(rtr)

def minifigure_v_datoteki(dat):
    vsebina = orodja.vsebina_datoteke('strani-brickset', dat)
    for blok in vzorec_bloka_brickset.finditer(vsebina):
        rtr = blok.group(0)
        yield izloci_podatke_minifigure(rtr)


for l in range(1992, 2022):
    seti_v_letu(l)
for j in range(1990, 2022):
    minifigure_v_letu(j)
seti = []
minifigure = []
pojavitve_figur = []
for dat in list(os.listdir('strani-brickeconomy')):
    for komplet in seti_v_datoteki(dat):
        if komplet != None:
            seti.append(komplet)

for dat in list(os.listdir('strani-brickset')):
    for minifigura in minifigure_v_datoteki(dat):
        for i in range(1, 6):
            try:
                if minifigura[f'st_{i}'] and minifigura['id']:
                    pojavitve_figur.append(
                        {'set': float(minifigura[f'st_{i}'].replace('-','.').replace('.1','.0')),
                        'id': minifigura['id']}
                    )
            except:
                pass
        if minifigura != None:
            minifigure.append(minifigura)


seti.sort(key=operator.itemgetter('stevilka'))
minifigure.sort(key=operator.itemgetter('id'))
pojavitve_figur.sort(key=operator.itemgetter('set'))
orodja.zapisi_csv(
    seti,
    ['stevilka', 'ime', 'tema', 'podtema', 'leto', 'st_kock', 'st_minifigur', 'dostopnost', 'msrp', 'vrednost'],
    'obdelani-podatki/seti.csv'
)
orodja.zapisi_csv(
    minifigure,
    ['id', 'ime', 'tema', 'podtema', 'leto', 'st_setov', 'novo', 'rabljeno'],
    'obdelani-podatki/minifigure.csv'
)
orodja.zapisi_csv(
    pojavitve_figur,
    ['set', 'id'],
    'obdelani-podatki/minifigure_v_setih.csv'
)
