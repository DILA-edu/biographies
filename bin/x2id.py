# coding: utf-8
''' 轉出 XML 供 InDesign 匯入
執行例:
  指定卷數範圍：x2id.py 1..2 # 只跑1~2卷
  列舉執行卷數：x2id.py 1,2,25
'''
import argparse, collections, os, pickle, re, subprocess, sys
from lxml import etree
import sw_xml, zbx_authority, zbx_str, zbx_chars

teiBase = '../Song_GSZ'
BIBL = os.path.join(teiBase, 'SGSZbibliography.xml')
OUT = '../output/indesign/sgsz1.xml'
IGNORE_TEXT = ['body', 'div', 'linkGrp']

count=collections.Counter()
globals={
  'current_apps':{}, 
  'div-level': 0,
  'endnotes':'',
  'endnote-ser':{},
  'mode': '',
  'lb': ''
}

hypy_zy_table='ㄅ(b), ㄆ(p), ㄇ(m), ㄈ(f), ㄉ(d), ㄊ(t), ㄋ(n), ㄌ(l), ㄍ(g), ㄎ(k), ㄏ(h), ㄐ(j), ㄑ(q), ㄒ(x), ㄓ(zh,zhi), ㄔ(ch,chi), ㄕ(sh,shi), ㄖ(r,ri), ㄗ(z,zi), ㄘ(c,ci), ㄙ(s,si), ㄧ(yi,-i), ㄨ(wu,-u), ㄩ(yu,-ü,-u), ㄚ(a), ㄛ(o), ㄜ(e), ㄝ(ê), ㄞ(ai), ㄟ(ei), ㄠ(ao), ㄡ(ou), ㄢ(an), ㄣ(en), ㄤ(ang), ㄥ(eng), ㄦ(er), ㄧㄚ(ya,-ia), ㄧㄛ(yo), ㄧㄝ(ye,-ie), ㄧㄞ(yai,-iai), ㄧㄠ(yao,-iao), ㄧㄡ(you,-iu), ㄧㄢ(yan,-ian), ㄧㄣ(yin,-in), ㄧㄤ(yang,-iang), ㄧㄥ(ying,-ing), ㄨㄚ(wa,-ua), ㄨㄛ(wo,-uo), ㄨㄞ(wai,-uai), ㄨㄟ(wei,-ui), ㄨㄢ(wan,-uan), ㄨㄣ(wen,-un), ㄨㄤ(wang,-uang), ㄨㄥ(weng,-ong), ㄩㄝ(yue,-üe,-ue), ㄩㄢ(yuan,-üan,-uan), ㄩㄣ(yun,-ün,-un), ㄩㄥ(yong,-iong)'

class MyArgs:
  def __init__(self, tag=None):
    self.zhuang = None
    self.juan = None
    self.juan_begin = None
    self.juan_end = None
    self.juans = None
  
class MyNode:
  def __init__(self, tag=None):
    self.tag = tag
    self.att = collections.OrderedDict()
    self.content = ''
    
  def set(self, key, value):
    self.att[key] = value
    
  def __str__(self):
    r = '<' + self.tag
    for k, v in self.att.items():
      r += ' {}="{}"'.format(k, v)
    if len(self.content) == 0:
      r += '/>'
    else:
      r += '>' + self.content
      r += '</{}>'.format(self.tag)
    return r
    
def parse_css(s):
  ''' 傳入 css 字串, 傳回 dictionary
  「font-size:small;display:inline」 => {'font-size':'small', 'display':'inline'}
  '''
  r={}
  if s is None: return r
  if not ':' in s: return r
  pairs=s.split(';')
  for attr in pairs:
    if attr=='': continue
    l=attr.split(':')
    try:
      r[l[0]]=l[1]
    except:
      error('css 格式錯誤:'+attr)
  return r

def create_endnote(id):
  global count, globals
  if id in globals['endnote-ser']:
    n=globals['endnote-ser'][id]
  else:
    if id not in notes:
      return ''
    count['endnote']+=1
    n=count['endnote']
    globals['endnote-ser'][id]=n
    if id not in notes:
      sys.exit('error 106: 有 <ptr target="#{0}"> 但是沒有 <note id="{0}">'.format(id))
      
    node = MyNode('p')
    node.set('rend', 'endnote')
    node.content = '[{}] '.format(n)
    node.content += notes[id]
    globals['endnotes'] += str(node) + '\n'
    
  # 因為【】視覺上太佔空間, 所以改用 []
  #r=open_char_style('endnote_anchor') + '【{}】'.format(n) + close_char_style()
  s = '<span rend="endnote-anchor">' + '[{}]'.format(n) + '</span>'
  return s

def get_ancestors(e):
  r=[]
  for ancestor in e.iterancestors():
    r.append(ancestor.tag)
  return r

def handle_plain_text(s):
  if s is None: return ''
  s=s.replace('&', '&amp;')
  s=s.replace('\n', '')
  return s

def get_plain_text(node, ignore_sic=True):
  r = ''
  tag = node.tag
  if ignore_sic and tag == 'sic':
    return r
  if tag == 'g':
    return '[{}]'.format(node.get('ref')[1:])
  if tag not in IGNORE_TEXT:
    r += handle_plain_text(node.text)
  for n in node.iterchildren(): 
    r += get_plain_text(n)
    if tag not in IGNORE_TEXT:
      r +=  handle_plain_text(n.tail)
  return r

def handle_text(s):
  if s is None: return ''
  s = s.replace('&', '&amp;')
  s = s.replace('\n', '')
  r = ''
  for c in s:
    if ord(c)>0xffff:
      r += '<span rend="extb">{}</span>'.format(c)
    else:
      r += c
  # Adobe 明體 Std 不能正確顯示 糩
  #r = r.replace('糩', '<span rend="新細明體">糩</span>')
  return r
  
def handle_authority_text(s):
  s=s.replace('\x02','')
  s=s.replace('\n','')
  s=s.replace('\r','')
  s=re.sub('<a .*?>(.*?)</a>', r'\1', s)
  s=s.replace('&', '&amp;')
  return s

def traverse(node):
  r = ''
  tag = node.tag
  s = handle_text(node.text)
  if tag not in IGNORE_TEXT:
    r += s
  for n in node.iterchildren(): 
    r += handle_node(n)
    s = handle_text(n.tail)
    if tag not in IGNORE_TEXT:
      r += s
  return r

def create_footnote(s, e):
  r = '<footnote>'

  ancestors=get_ancestors(e)
  if 'head' in ancestors:
    r = "<footnote marker_style='footnote-anchor'>"
  else:
    parent=e.getparent()
    if parent.tag in ('persName', 'placeName', 'name'):
      if len(e.xpath('following-sibling::node()')) == 0:
        # 如果是最後一個元素
        r = "<footnote marker_style='footnote-anchor'>"
      else:
        r = "<footnote marker_style='footnote-anchor-underline'>"

  s = re.sub(r'<(img type="g" src=".*?") width=".*?" height=".*?"/>', r'<\1 width="10" height="10"/>', s)
  return r + s + '</footnote>'

def date_abbr(pre, d1, d2):
  t1=d1.split('.')
  t2=d2.split('.')
  # 如果有「約」, 而且起迄年份相同, 就只顯示年份
  if pre!='' and t1[0]==t2[0]:
    return pre+t1[0]
  return pre+'{0}~{1}'.format(d1, d2)

def dateFormat(d):
  pre=''
  s=d
  if d.startswith('-'): 
    pre='-'
    s=d[1:]
  elif d.startswith('+'):
    s=d[1:]
  return pre + s.lstrip('0').replace('-','.').replace('.0', '.')

def handle_anchor(e):
  r=''
  id=e.get('id')
  if id is not None:
    print('anchor id:', id, file=log)
    app_id=id[3:]
    if app_id in app_type_0: return ''
    if app_id not in appId2Ser:
      print('anchor ID 在 sgszApparatus.xml 不存在: '+id, file=log)
    else:
      if id.startswith('beg'):
        globals['current_apps'][app_id]=''
      elif id.startswith('end'):
        '''
        r=open_char_style('Footnote_20_anchor')
        r+='[{}]'.format(appId2Ser[app_id])
        r+=close_char_style()
        '''
        # 有成對的 anchor 才處理
        if app_id in globals['current_apps']:
          if globals['mode']!='notes': # 校勘裡又有校勘, 不能再加 footnote
            s=apps[app_id]
            s+=globals['current_apps'][app_id] # 如果 app 包 choice, 把 choice 產生的 note 文字也加進來
            r+=create_footnote(s, e)
            print(330, r, file=log)
          del globals['current_apps'][app_id]
  return r

def handle_choice(e):
  global globals
  r=''
  if e.find('sic') is not None and e.find('corr') is not None:
    corr=handle_node(e.find('corr'))
    sic=handle_node(e.find('sic'))
    s=e.findtext('note')
    r += corr
    if len(globals['current_apps'])>0: # 如果 choice 是包在 app 裏, 就不產生 footnote
      print('choice在app裡, lb:', globals['lb'], file=log)
      # 已經有校勘, 就一定會有大正藏是什麼字, 就不必再說原大正藏作什麼了
      #if s is None:
      # s='原《大正藏》作「{}」。'.format(sic)
      if s is not None:
        for k in globals['current_apps']: 
          globals['current_apps'][k]+=s
          print('\t'+k, file=log)
    else:
      if s is None:
        s='底本作「{0}」。'.format(''.join(sic))
      r += create_footnote(s, e)
  elif e.find('orig') is not None and e.find('reg') is not None:
    reg=handle_node(e.find('reg'))
    orig=handle_node(e.find('orig'))
    s=e.findtext('note')
    if s is None:
      s='底本「{0}」的通用字。'.format(''.join(orig))
    r += reg
    if len(globals['current_apps'])>0:
      for k in globals['current_apps']: 
        globals['current_apps'][k]+=s
    else:
      r += create_footnote(s, e)
  return r

def handle_date(e):
  r=traverse(e)
  
  # <head> 裏的 <date> 不顯示西元年
  ancestors=get_ancestors(e)
  if 'head' in ancestors: 
    parent=e.getparent()
    # head 裏的 seg 因為會另起新段落, 所以仍要顯示西元年
    # head 裏 <seg rend='display:inline'> 仍會在標題裏, 所以不顯示西元年
    if parent.tag!='seg': return r
    if e.get('rend') is not None and 'display:inline' in e.get('rend'): 
      return r

  # 如果是朝代的話就不顯示西元年
  k=e.get('key')
  if k in zbx_authority.dynastyID:
    r = '<span rend="dynasty">' + ''.join(r) + '</span>'
  else:
    s=''
    if e.get('when-iso') is not None:
      s=dateFormat(e.get('when-iso'))
    else:
      pre=''
      d1=e.get('notBefore-iso')
      if d1 is None: d1=e.get('from-iso')
      else: pre='約'
      d2=e.get('notAfter-iso')
      if d2 is None: d2=e.get('to-iso')
      else: pre='約'
      if d1 is not None and d2 is not None:
        s=date_abbr(pre, dateFormat(d1), dateFormat(d2))
    if s!='':
      if globals['mode']=='notes':
        r += '（'+s+'）'
      else: 
        r += create_footnote(s, e)
  return r

def handle_div(e):
  global globals
  
  if 'n' in e.attrib:
    n = e.get('n')
    i = int(n)
    
  if (e.get('type')=='juan'):
    if args.juan is not None:  # 只做某一卷
      if i != args.juan:
        return ''
    elif args.juans is not None:  # 列舉要做的卷
      if e.get('n') not in args.juans:
        return ''
    elif args.juan_begin is not None and args.juan_end is not None:  # 指定卷數範圍
      if (i < args.juan_begin) or (i > args.juan_end):
        return ''
    print('juan', n)
    
  # 只做某一個傳
  if args.zhuang is not None:
    id=e.get('id')
    z=args.zhuang
    if id!=z:
      if len(e.xpath('descendant::div[@id="{}"]'.format(z)))==0:
        if len(e.xpath('ancestor::div[@id="{}"]'.format(z)))==0:
          return ''
          
  if e.find('head') is None:
    r = traverse(e)
  else:
    globals['div-level'] += 1
    r = traverse(e)
    globals['div-level'] -= 1
  return r

def handle_head(e):
  r = ''
  head = traverse(e)
  pure_head = ''
  for s in head:
    s = s.replace('<span>', '')
    s = s.replace('</span>', '')
    pure_head += s
  pure_head = re.sub('<footnote[^>]*?>.*?</footnote>', '', pure_head)
    
  # 給目錄用的
  if globals['div-level']==2:
    r = '<p rend="h2-for-toc">' + pure_head + '</p>\n'

  parent = e.getparent()
  node = MyNode('p')
  style = 'h{}'.format(globals['div-level'])
  node.set('rend', style)
  node.content = head
  r += str(node) + '\n'

  # 給頁首用的
  if globals['div-level']==1:
    child_div = parent.find('div')
    if child_div is not None:
      type = child_div.get('type')
      if type is not None:
        pure_head += ' ‧ ' + type
      s = '<header>' + pure_head + '</header>\n'
      r += s

  return r

def handle_lb(e):
  lb = e.get('n')
  globals['lb'] = lb
  # 如果產生 lb, 會干擾後面的處理
  #return "<lb n='%s'/>" % lb
  return ''

def handle_name(e):
  parent = e.getparent()
  ancestors = get_ancestors(e)
  k = e.get('key')
  if 'head' in get_ancestors(e): # 如果在 head 裡, 就不加底線
    r = traverse(e)
  else:
    node = MyNode('span')
    node.set('rend', 'name')
    node.content = traverse(e)
    r = str(node)
  print('handle_name: ', r, file=log)
  return r

def handle_persName(e):
  global people

  ancestors = get_ancestors(e)
  in_head = 'head' in ancestors

  parent = e.getparent()
  ancestors = get_ancestors(e)

  k = e.get('key')
  if parent.tag == 'persName':
    if parent.index(e) == 0: # 如果是下層的第一個 persName
      r = person_name_node(parent, e, in_head)
    else:
      node = MyNode('persName')
      node.content = traverse(e)
      if not in_head: node.set('rend', 'persName')
      r = str(node)
  else:
    if e.find('persName') is not None: # 如果下層還有 persName
      r = traverse(e)
    else:
      r = person_name_node(e, e, in_head)
  return r

def person_name_node(key_node, content_node, in_head):
  node = MyNode('persName')
  k = key_node.get('key')
  if (k is not None) and (globals['mode']!='notes'):
    name = get_plain_text(key_node)
    people.add(k+'\t'+name)
    node.set('key', k)
    node.set('name', name)
  if not in_head: node.set('rend', 'persName')
  node.content = traverse(content_node)
  return str(node)

def handle_placeName(e):
  global place

  ancestors = get_ancestors(e)
  in_head = 'head' in ancestors

  parent = e.getparent()

  # placeName 如果包在 persName 裡面，就當做沒標這個 placeName
  if parent.tag == 'persName':
    return traverse(e)

  if parent.tag == 'placeName': # 如果上層也是 placeName
    if parent.index(e) == 0: # 如果是下層的第一個 placeName
      r = place_name_node(parent, e, in_head)
    else:
      node = MyNode('placeName')
      node.content = traverse(e)
      if not in_head: node.set('rend', 'placeName')
      r = str(node)
  else:
    if e.find('placeName') is not None: # 如果下層還有 placeName
      r = traverse(e)
    else:
      r = place_name_node(e, e, in_head)
  return r

def place_name_node(key_node, content_node, in_head):
  node = MyNode('placeName')
  k = key_node.get('key')
  if (k is not None) and (globals['mode']!='notes'):
    name = get_plain_text(key_node)
    place.add(k+'\t'+name)
    node.set('key', k)
    node.set('name', name)
  if not in_head: node.set('rend', 'placeName')
  node.content = traverse(content_node)
  return str(node)

def handle_ptr(e):
  css=parse_css(e.get('rend'))
  if css.get('display', '')=='none': 
    return ''
  if globals['mode']=='notes': 
    return ''
  type=e.get('type')
  r = ''
  if type is None or type=='glossary':
    target = e.get('target')
    note_id=target[1:]
    r=create_endnote(note_id)
  return r

def handle_roleName(e):
  node = MyNode('span')
  node.set('rend', 'roleName')
  node.content = traverse(e)
  r = str(node)
  return r

def handle_seg(e):
  t = e.get('type', '')
  if t == 'latin':
    r = '<span rend="index-pinyin">%s</span>' % traverse(e)
  elif t == 'note':
    r = ''
  elif t == 'pronunciation':
    r = ''
  else:
    r = traverse(e)
  return r

def handle_supplied(e):
  global globals
  r = traverse(e)
  s='底本無「{}」字。'.format(r)
  r += create_footnote(s, e)
  return r

def handle_node(e):
  global globals
  tag=e.tag
  if tag==etree.Comment: return ''
  r = ''
  if tag == 'anchor':
    r = handle_anchor(e)
  elif tag == 'byline':
    node = MyNode('p')
    node.set('rend', 'byline')
    node.content = traverse(e)
    r = str(node) + '\n'
  elif tag == 'choice':
    r = handle_choice(e)
  elif tag == 'date':
    r = handle_date(e)
  elif tag == 'div':
    r = handle_div(e)
  elif tag == 'g':
    r = '<img type="g" src="{}.ai" width="12" height="12"/>'.format(e.get('ref')[1:])
  elif tag == 'head':
    r = handle_head(e)
  elif tag == 'lb':
    r = handle_lb(e)
  elif tag == 'lg':
    node = MyNode('p')
    node.set('rend', 'lg')
    node.content = traverse(e)
    r = str(node) + '\n'
  elif tag == 'name':
    r = handle_name(e)
  elif tag == 'p':
    node = MyNode('p')
    node.set('rend', 'p')
    node.content = traverse(e)
    r = str(node) + '\n'
  elif tag == 'pb':
    n = e.get('n')
    n = n.lstrip('0')
    r = '<pb n="{}"/>'.format(n)
  elif tag == 'persName':
    r = handle_persName(e)
  elif tag == 'placeName':
    r = handle_placeName(e)
  elif tag == 'ptr':
    r = handle_ptr(e)
  elif tag == 'roleName':
    r = handle_roleName(e)
  elif tag == 'seg':
    r = handle_seg(e)
  elif tag == 'supplied':
    r = handle_supplied(e)
  else:
    r = traverse(e)
  return r
  
def check_regular_name(auth_info, name_set):
  ''' 如果常名沒出現過, 那也要新增一筆 '''
  temp_set = name_set.copy()
  for s in temp_set:
    (k, name) = s.split('\t')
    try:
      info = auth_info[k]
    except:
      sys.exit('錯誤：找不到 {} 的 authority 資訊，請先執行 read-authority.py 取得最新資訊，\n如果還是發生相同錯誤，請檢查 Authority DB 是否有此 ID。'.format(k))
    
    if info is None:
      print('{} 在 authority 資訊中不存在。'.format(k))
      sys.exit('程式中斷')

    if 'name' in info:
      new = k + '\t' + info['name']
    else:
      sys.exit('{} 的 authority 資訊中沒有 name。'.format(k))
    if (new) not in name_set:
      name_set.add(new)

def person_authority(fo):
  global people
  fo.write(h1('人名索引'))
  fo.write('<p><span>依漢語拼音排序 (破音字以一般讀音排序)</span></p>\n')
  fo.write('<p><span>注音符號對照漢語拼音簡表：</span></p>\n')
  fo.write('<p><span>' + hypy_zy_table + '</span></p>\n')
  
  with open('personAuthority.pickle', 'rb') as f:
    person_info = pickle.load(f)
    
  check_regular_name(person_info, people)
  
  # 取得漢語拼音
  person_index=[]
  for s in people:
    (k, name) = s.split('\t')
    try:
      print(f'person key: {k}, name: {name}', file=log)

      py=''
      # 優先從 authority 取得漢語拼音
      if k in person_info:
        h = person_info[k]['pinyin']
        if name in h:
          py = h[name]
          print(f'從 authority 取得漢語拼音: {py}', file=log)

      if py=='':
        py = zbx_authority.get_name_yin('person', name)

      print(py, file=log)

      py=py.lower()
      pyn=zbx_str.remove_diacritics(py)
      pi = (pyn, py, name, k)
      if pi not in person_index:
        person_index.append(pi)
    except zbx_chars.zbxError as err:
      for c in err.value:
        if c not in HanYuPinYinUnknow:
          HanYuPinYinUnknow.append(c)
          
  # 依漢語拼音排序
  person_index = sorted(person_index)
  
  py_first_char=''
  for pi in person_index:
    py = pi[1]
    name = pi[2]
    k = pi[3]
    
    s = ''
    
    # 拼音的第一個字母 設為 標題2
    c = pi[0][0].upper()
    if c!=py_first_char:
      py_first_char=c
      s += '<p rend="h2"><span>{}</span></p>\n'.format(py_first_char)
      
    try:
      info = person_info[k]
    except:
      sys.exit('錯誤：找不到 {} 的人名資訊，請先執行 read-authority.py 取得最新資訊，如果還是發生相同錯誤，請檢查 Authority DB 是否有此人名 ID。'.format(k))
    if info is None:
      continue
    #s = '<auth_person key="{}" name="{}">'.format(k, info['name'])
    #s = '<auth_person key="{}" name="{}">'.format(k, name)
    #s += py
    name_with_style = handle_text(name)
    name_with_style = re.sub(r'\[(Z\d{4})\]', r'<img type="g" src="\1.ai" width="12" height="12"/>', name_with_style)
    if name != info['name']:
      s += '<p rend="index-entry">{}'.format(name_with_style)
      s += ' <span rend="index-pinyin">{}</span><span>：</span>'.format(py)
      s += '<index_person_pages key="{}" name="{}"/>'.format(k, name)
      s += '<span>參 {} </span><span rend="index-key">({})</span>'.format(info['name'], k)
      s += '</p>\n'
    else:
      s += '<p rend="index-entry">{}'.format(name_with_style)
      s += ' <span rend="index-pinyin">{}</span><span>：</span>'.format(py)
      s += '<span rend="index-key">({});</span>'.format(k)
      s += ' <index_person_pages key="{}"/>'.format(k, name)
      s += '</p>\n'
      if 'note' in info and info['note'] is not None:
        note = handle_authority_text(info['note'])
        if note != '':
          note=re.sub('（[^）]*?）$', '', note)
        s += '<p rend="index-note"><span>{}</span></p>\n'.format(note)
      if 'names' in info:
        names=info['names']
        names=names.replace('\n', '; ')
        names=names.replace(',', ', ')
        if names!='': 
          # 若只有中文別名 就不顯示 [中文]
          languages=re.findall(r'\[[^\]/]+\]', names)
          if len(languages)<2:
            names=names.replace('[中文] ', '')
          s+='<p rend="index-note"><span>{}</span></p>\n'.format('別名：' + names)
    #s += '</auth_person>\n'
    fo.write(s)

def place_authority(fo):
  global place
  fo.write(h1('地名索引'))
  fo.write('<p><span>依漢語拼音排序 (破音字以一般讀音排序)</span></p>\n')
  fo.write('<p><span>注音符號對照漢語拼音簡表：</span></p>\n')
  fo.write('<p><span>' + hypy_zy_table + '</span></p>\n')
    
  with open('placeAuthority.pickle', 'rb') as f:
    place_info = pickle.load(f)
    
  check_regular_name(place_info, place)
  
  # 取得漢語拼音
  place_index=[]
  for s in place:
    (k, name) = s.split('\t')
    try:
      print(f'place key: {k}, name: {name}', file=log)

      py=''
      # 優先從 authority 取得漢語拼音
      if k in place_info:
        h = place_info[k]['pinyin']
        if name in h:
          py = h[name]
          print(f'從 authority 取得漢語拼音: {py}', file=log)
          
      if py=='':
        py = zbx_authority.get_name_yin('place', name)

      py = py.lower()
      pyn = zbx_str.remove_diacritics(py)
      pi = (pyn, py, name, k)
      if pi not in place_index:
        place_index.append(pi)
    except zbx_chars.zbxError as err:
      for c in err.value:
        if c not in HanYuPinYinUnknow:
          HanYuPinYinUnknow.append(c)
          
  # 依漢語拼音排序
  place_index = sorted(place_index)
  
    
  py_first_char=''
  for pi in place_index:
    py = pi[1]
    name = pi[2]
    k = pi[3]
    
    s = ''
    
    # 拼音的第一個字母 設為 標題2
    c = pi[0][0].upper()
    if c!=py_first_char:
      py_first_char=c
      s += '<p rend="h2"><span>{}</span></p>\n'.format(py_first_char)
      
    try:
      info = place_info[k]
    except:
      sys.exit('錯誤：找不到 {} 的人名資訊，請先執行 read-authority.py 取得最新資訊，如果還是發生相同錯誤，請檢查 Authority DB 是否有此人名 ID。'.format(k))
    if info is None:
      continue
    if name != info['name']:
      s += '<p rend="index-entry"><span>{} </span><span rend="index-pinyin">{}</span><span>：</span>'.format(name, py)
      s += '<index_place_pages key="{}" name="{}"/>'.format(k, name)
      s += '<span>參 {} </span><span rend="index-key">({})</span>'.format(info['name'], k)
      s += '</p>\n'
    else:
      s += '<p rend="index-entry"><span>{} </span><span rend="index-pinyin">{}</span><span>：</span>'.format(name, py)
      s += '<span rend="index-key">({});</span>'.format(k)
      s += ' <index_place_pages key="{}"/>'.format(k, name)
      s += '</p>\n'
      if 'note' in info and info['note'] is not None:
        note = handle_authority_text(info['note'])
        if note != '':
          note=re.sub('（[^）]*?）$', '', note)
        s += '<p rend="index-note"><span>{}</span></p>\n'.format(note)
      if 'names' in info:
        names=info['names']
        names=names.replace('\n', '; ')
        names=names.replace(',', ', ')
        if names!='': 
          # 若只有中文別名 就不顯示 [中文]
          languages=re.findall(r'\[[^\]/]+\]', names)
          if len(languages)<2:
            names=names.replace('[中文] ', '')
          s+='<p rend="index-note"><span>{}</span></p>\n'.format('別名：' + names)
    fo.write(s)
  
def read_notes(tree):
  global globals
  globals['mode']='notes'
  back = tree.find('.//back')
  r={}
  for n in back.iter('note'):
    if 'display:none' in n.get('rend', ''):
      continue
    id=n.get('id')
    if id is not None:
      r[id]=traverse(n)
  globals['mode']=''
  return r

def readApps(tei):
  global appsContent, appId2Ser, app_type_0
  globals['mode']='notes'
  back = tei.find('.//back')
  appsContent=collections.OrderedDict()
  appId2Ser={}
  app_type_0 = []
  r={}
  count=0
  for n in back.iter('app'):
    appId=n.get('from')[3:]
    s=''

    ana = n.get('ana')
    if ana == 'appType0':
      app_type_0.append(appId)
      continue

    if ana != 'appType0':
      s += re.sub('^appType(.*)$', r'\1）', ana)

    lem=n.find('lem')
    #s+=lem.get('wit')
    if lem is None:
      print('832 app 無 lem', appId)
      sys.exit()
    #s+=icon(lem.get('wit'))+' '
    #s+=handle_node(lem)
    lem_wits = [lem.get('wit')]
    lem_text = handle_node(lem)
    
    # rdg 內容與 lem 相同的，與 lem 合併
    # rdg 彼此內容相同的, 合併為一個 rdg
    rdgs=collections.OrderedDict()
    for c in n.iterchildren('rdg'):
      wit=c.get('wit')
      rdg=handle_node(c)
      if rdg == lem_text: lem_wits.append(wit)
      elif rdg in rdgs: rdgs[rdg]+=wit
      else: rdgs[rdg]=wit

    for w in lem_wits:
      s += icon(w)
    s += lem_text

    for rdg in rdgs:
      s+='；'+icon(rdgs[rdg])+' '+rdg
    #s += '。' + n.get('ana')
    s += '。'
    r[appId]=s
    if s not in appsContent: 
      count+=1
      ser=count
      appsContent[s]=str(count)
    else: ser=appsContent[s]
    appId2Ser[appId]=ser
  globals['mode']=''
  return r

def insert_underline_separator(mo):
  if mo.group(0).startswith('<p '):
    return mo.group(0)
  return '{}<span rend="underline_separator"> </span>{}'.format(mo.group(1), mo.group(2))

def h1(s):
  return '<p rend="h1"><span>{0}</span></p>\n<header>{0}</header>\n'.format(s)

def icon(wit):
  icons={
    'ref': 'ref.ai',
    'CBETA': 'cbeta.ai',
    '大': 'da.ai',
    '宋': 'song.ai',
    '元': 'yuan.ai',
    '范': 'fan.ai',
    '磧': 'qi.ai',
    '宮': 'gong.ai',
    '增': 'zeng.ai',
    '南藏': 'nan.ai',
  }
  t=re.split('[【】]', wit)
  r=[]
  for c in t:
    if c=='': continue
    if c in icons:
      count['graphic']+=1
      s = '<img type="g" src="{}" width="12" height="12"/>'.format(icons[c])
    else: s='【{}】'.format(c)
    r.append(s)
  return ' '.join(r)

def read_bibl():
  tree = etree.parse(BIBL)
  tree = sw_xml.stripNamespaces(tree)
  bibls = tree.xpath('//listBibl/bibl')

  entries = []
  for bibl in bibls:
    last_name = bibl.findtext('author/hi')
    #print(last_name)
    entries.append((last_name, bibl))

  # 依 作者 last name 排序
  entries.sort(key=lambda a: a[0])

  r = ''
  for (last_name, bibl) in entries:
    author_element = bibl.find('author')
    author = traverse(author_element.find('hi'))
    r += "<p rend='bibl1'><span>{}".format(author)
    date_element = bibl.find('edition/date')
    if date_element is not None:
      date = date_element.text
      if date is not None:
        date = date.replace('.', '-')
        r += " ({})".format(date)
    r += "</span></p>\n"
    r += "<p rend='bibl2'><span>"
    r += traverse(author_element) + ': '
    r += traverse(bibl.find('title')) + '. '
    r += traverse(bibl.find('edition')) + ' '
    r += "(={})".format(bibl.find('abbr').text)
    r += "</span></p>\n"
  return r

# main
# 下面取得參數的方法在伯雍的電腦上無效
#parser = argparse.ArgumentParser()
#parser.add_argument("-z", action="store", dest="zhuang", help="某個傳的id")
#parser.add_argument("-j", action="store", type=int, dest="juan", help="只輸出某一卷")
#parser.add_argument('-b', dest='juan_begin', type=int, help='起始卷數')
#parser.add_argument('-e', dest='juan_end', type=int, help='結束卷數')
#args = parser.parse_args()

HanYuPinYinUnknow=[]

args = MyArgs()
if len(sys.argv)>1:
  arg = sys.argv[1]
  if '..' in arg:
    mo = re.match(r'(\d+)\.\.(\d+)$', arg)
    args.juan_begin = int(mo.group(1))
    args.juan_end = int(mo.group(2))
  elif ',' in arg:
    args.juans = arg.split(',')
  else:
    args.juan = int(arg)

log = open('x2id.log', 'w', encoding='utf_8_sig')
xml_file = os.path.join(teiBase, 'wrapper-song.xml')
print(xml_file)
tree = etree.parse(xml_file)
tree.xinclude()
tree = sw_xml.stripNamespaces(tree)

people = set()
place = set()
notes=read_notes(tree)
apps=readApps(tree)

body = tree.find('.//body')
content_list = traverse(body)
content = ''.join(content_list)

# persName 的一開頭如果是 roleName, 就把 roleName 移到 persName 前面
content = re.sub('(<persName[^>]*>)(<span rend="roleName">.*?</span>)', r'\2\1', content)

# 在兩個地名或人名之間插入空白, 以斷開底線
# 標題裡面不必加
regexp = r'<p rend="h\d+">.*?</p>|(</persName>|</placeName>|<span rend="name">[^<]*?>/span>)(<persName|<placeName|<span rend="name")'
content = re.sub(regexp, insert_underline_separator, content)

out_folder = os.path.dirname(OUT)
os.makedirs(out_folder, exist_ok=True)
print('output file:', OUT)
fo = open(OUT, 'w', encoding='utf8')
fo.write('<root>\n')
fo.write('  <body>\n')
fo.write(content)


print('write 註解')
fo.write(h1("註解"))
fo.write(globals['endnotes'])
fo.write('  </body>\n')
fo.write('  <back>\n')
place_authority(fo)
person_authority(fo)

print('write 引用書目')
fo.write(h1("引用書目"))
fo.write(read_bibl())
fo.write('  </back>\n')
fo.write('</root>')
fo.close()
print('system platform:', sys.platform)
if sys.platform.startswith('win'):
  os.system('python x2id2.py')
  os.system('ruby x2id3.rb')
else:
  r=subprocess.call(['python3', 'x2id2.py'])
  print('python3 x2id2.py return:', r)
  r=subprocess.call(['ruby', 'x2id3.rb'])
  print('ruby x2id3.rb return:', r)