#-*- coding:utf-8 -*-
import codecs, json, os, pickle, re, sys
from lxml import etree
import sw_xml, zbx_authority

API = 'http://dev.dila.edu.tw/authority/webwidget/getAuthorityData.php'
#API = 'http://authority.dila.edu.tw/webwidget/getAuthorityData.php'

def read_person(key):
  print(key)
  if key!='unknown' and key not in personInfo:
    personInfo[key]=zbx_authority.getPersonInfo(key)
    if personInfo[key] is None: notFound.append(key)

def read_place(key):
    print(key)
    if key!='unknown' and key not in placeInfo:
      placeInfo[key]=zbx_authority.getPlaceInfo(key)
      if placeInfo[key] is None: notFound.append(key)
      print(key, file=log)

def readXML(fn_in):
  global notFound
  tei = etree.parse(fn_in)
  tei.xinclude()
  tei = sw_xml.stripNamespaces(tei)
  tei = tei.getroot()

  for e in tei.iter('persName'):
    if 'key' not in e.attrib: continue
    read_person(e.get('key'))

  for e in tei.iter('placeName'):
    if 'key' not in e.attrib: continue
    read_place(e.get('key'))

def save_json(obj, folder, fn):
  path = os.path.join(folder, fn)
  #s = json.dumps(personInfo, sort_keys=True, indent=2)
  with codecs.open(path, 'w', encoding='utf-8') as f:
    json.dump(obj, f, ensure_ascii=False, indent=2)

personInfo={}
placeInfo={}
notFound=[]

log=open('read-authority.log', 'w', encoding='utf8')

zbx_authority.set_api_url(API)
readXML('../Song_GSZ/wrapper-song.xml')
readXML('../Song_GSZ/sgszNotes.xml')

print('person keys: {}'.format(len(personInfo)))
print('place keys: {}'.format(len(placeInfo)))

with open('personAuthority.pickle', 'wb') as f:
    pickle.dump(personInfo, f)

with open('placeAuthority.pickle', 'wb') as f:
    pickle.dump(placeInfo, f)

base = '../output/authority'
if not os.path.exists(base):
  os.makedirs(base)
#save_json(personInfo, base, 'person.json')
#save_json(placeInfo, base, 'place.json')

if len(notFound)>0:
  print('not found:')
  for s in notFound: print(s)