# -*- coding: utf-8 *-*
''' (1) 將 cRef 屬性值 標準化
  例如, 原為: CBETA, T39, no. 1799, p. 845, c22-23
  轉為: CBETA_T39_n1799_p845_c22-p845_c23
(2) 將 <placeName> 內容中有半形空格區隔的, 再包 <placeName>
  例如: <placeName xml:id="abc">金山 法鼓寺</placeName>
  轉為: <placeName xml:id="abc"><placeName>金山</placeName><placeName>法鼓寺</placeName></placeName>
(3) 將 <persName> 內容中有半形空格區隔的, 再包 <persName>
'''
import os, re, sys

INPUT = '../Song_GSZ'
OUTPUT = '../output/xml'

def myRepl(mo):
  s=mo.group(1)
  if not s.startswith('CBETA') or not ' ' in s: return mo.group(0)
  r=s.replace('no. ', 'n')
  r=r.replace('p. ', 'p')
  r=r.replace(', ','_')
  if '-' in r:
    t=r.split('-')
    begin=t[0]
    end=t[1]
    if 'p' not in end:
      b=begin.split('_')
      if len(b) < 5:
        print("格式錯誤：%s" % s)
        sys.exit(0)
      page=b[3]
      line=b[4]
      if re.match('[a-z]', end) is None:
        end=line[0]+end
      r=begin+'-'+page+'_'+end
  r=re.sub('_n0+', '_n', r)
  return 'cRef="{}"'.format(r)

def repl_place(mo):
  ''' 空格隔開的地名再包 placeName '''
  tag = mo.group(1)
  name = mo.group(2)
  if not ' ' in name:
    return mo.group(0)
  
  tokens = re.findall('(?:<[^>]*?>|.)', name, re.DOTALL)
  names = ['']
  for t in tokens:
    if t==' ':
      names.append('')
    else:
      names[-1] += t
      
  if len(names)==1:
    return mo.group(0)
    
  r = tag
  for n in names:
    r += '<placeName>{}</placeName>'.format(n)
  r += '</placeName>'
  return r

def repl_person(mo):
  ''' 空格隔開的人名再包 persName '''
  tag = mo.group(1)
  name = mo.group(2)
  if not ' ' in name:
    return mo.group(0)
  
  tokens = re.findall('(?:<[^>]*?>|.)', name, re.DOTALL)
  names = ['']
  for t in tokens:
    if t==' ':
      names.append('')
    else:
      names[-1] += t
      
  if len(names)==1:
    return mo.group(0)
    
  r = tag
  for n in names:
    r += '<persName>{}</persName>'.format(n)
  r += '</persName>'
  return r

def do1file(fn):
  print(fn)
  with open(os.path.join(INPUT, fn), 'r', encoding='utf8') as fi:
    text=fi.read()
    
  text=re.sub('cRef="(.*?)"', myRepl, text)
  text=re.sub('(<placeName [^>]*?>)(.*?)</placeName>', repl_place, text, flags=re.DOTALL)
  text=re.sub('(<persName [^>]*?>)(.*?)</persName>', repl_person, text, flags=re.DOTALL)
  
  with open(os.path.join(OUTPUT, fn), 'w', encoding='utf8') as fo:
    fo.write(text)

if not os.path.exists(OUTPUT):
  os.makedirs(OUTPUT)
  
files = os.listdir(INPUT)
for f in files:
  if f.endswith('xml'):
    do1file(f)