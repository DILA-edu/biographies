# coding:utf_8_sig
from retry import retry
import json, os, urllib.request, re
import zbx_str, zbx_unihan

dynastyID = ('j16410251646133','j16462521647669','j16477011723283','j17243601729737','j17304061801742','j18017581818249','j18019131817499','j18048431823479','j18182531836822','j18369381874651','j18493231865308','j18614411873630','j18620951916335','j18746541896160','j18961611904523','j19045331924818','j19221051931862','j19245481933331','j19248221936231','j19333311946884','j19469512052491','j19730671978610','j20523972132049','j20524952058505','j20583162063308','j20632642066960','j20670182068412','j20684542071731',
'j21283392171816',
'j21328572188290', # 南宋
'j21615902185641','j21856422220977','j22207422321634','j23218222419402',
'j16477011801742', #漢
'j18182531874651', #晉
'j20717322132773',
'j20717322188290', #宋
'j20717322132856', #北宋
)

authorityAPI='http://authority.dila.edu.tw/webwidget/getAuthorityData.php'

name_yin={
  '憑翊'  'feng yi',
  '費縣'  'bi xian',
}
place_name_yin={
  '濟':'jǐ',
}
person_name_yin={
  '濟':'jì',
}
last_name_yin={
  '區':'ōu',
  '藏':'cáng',
  '任':'rén',
  '給':'jǐ',
  '仇':'qiú',
  '載':'dài',
  '解':'xiè',
  '亡':'wú',
  '候':'hóu',
  '𧓍': 'bin'
}

class zbxError(Exception):
  def __init__(self, value):
    self.value = value
  def __str__(self):
    return repr(self.value)

def set_api_url(url):
  global authorityAPI
  authorityAPI=url

@retry(backoff=2)
def getPersonInfo(key):
  url=authorityAPI+'?type=person&id=' + key
  try:
    f=urllib.request.urlopen(url)
    s=f.read().decode('utf-8')
    r=json.loads(s)
  except:
    print("\ngetPersonInfo 失敗，URL:", url)
    raise
    
  if r is None: return r
  info=r['data1']
  if ('note' in info) and (info['note'] is not None):
    info['note']=info['note'].replace('\x02','')
  return info

@retry(backoff=2)
def getTimeInfo(w=None, f=None, t=None):
  if w is not None:
    url=authorityAPI+'?type=time&format=j&when=' + w
  else:
    url=authorityAPI+'?type=time&format=j&from={}&to={}'.format(f,t)
  
  try:
    f=urllib.request.urlopen(url)
    s=f.read().decode('utf-8')
    r=json.loads(s)
  except:
    print("\ngetTimeInfo 失敗，URL:", url)
    raise
  
  if r is None: return r
  return r

@retry(backoff=2)
def getPlaceInfo(key):
  url=authorityAPI+'?type=place&id=' + key

  try:
    f=urllib.request.urlopen(url)
    s=f.read().decode('utf-8')
    r=json.loads(s)
  except:
    print("\ngetPlaceInfo 失敗，URL:", url)
    raise
  
  if r is None: return r
  return r['data1']

def personLivingYears(info):
  if ('bornDateBegin' not in info) and ('diedDateEnd' not in info):
    return ''
  begin=info['bornDateBegin']
  end=info['diedDateEnd']
  if begin=='unknown' and end=='unknown': return ''
  if begin=='unknown': begin='?'
  if end=='unknown': end='?'
  if begin.startswith('-'):
    begin=begin[1:]
    begin=re.sub(r'^0*(\d+)\-.*$', r'\1BCE', begin[1:])
  else:
    begin=re.sub(r'^0*(\d+)\-.*$', r'\1', begin[1:])
  if end.startswith('-'):
    end=re.sub(r'^0*(\d+)\-.*$', r'\1BCE', end[1:])
  else:
    end=re.sub(r'^0*(\d+)\-.*$', r'\1', end[1:])
    if begin.startswith('-'): begin+='CE'
  return '({0}-{1})'.format(begin,end)
  
def get_name_yin(type, name):
  global name_yin
  if name in name_yin: 
    return name_yin[name]
  name=zbx_str.strip_punctuation(name)
  chars=zbx_str.split_chars(name)
  r=[]
  first=True
  for c in chars:
    if c.isdigit():
      continue
    py=''
    if re.match('[A-Za-zāäḍīśšü]', c):
      py=c
    if py=='': # 先在針對人名、地名的讀音表中尋找
      if type=='person':
        if first and c in last_name_yin: # 在姓氏讀音表中尋找
          py=last_name_yin[c]
        else:
          py=person_name_yin.get(c, '')
      elif type=='place':
        py=place_name_yin.get(c, '')
    if py=='':
      py=name_char_yin.get(c, '')
    if py=='':
      pys=zbx_unihan.get_readings(c)
      if pys is not None: py=pys[0]
    if py=='' and c != '‧':
      i=zbx_str.code_point(c)
      raise zbxError('缺漢語拼音: [{}] U+{:X}'.format(c, i))
    if py != '':
      r.append(py)
    first=False
  return ' '.join(r)
  
def read_name_char_yin():
  folder=os.path.dirname(__file__)
  fn=os.path.join(folder, 'name-char-yin.txt')
  fi=open(fn, 'r', encoding='utf8')
  r={}
  for line in fi:
    if line.startswith('#'): continue
    line=line.strip()
    t=line.split('\t')
    r[t[0]]=t[1]
  fi.close()
  return r

name_char_yin=read_name_char_yin()
