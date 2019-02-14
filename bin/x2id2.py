# coding: utf-8
''' XML 轉 InDesign 第二步驟
'''
import os, re, sys
from lxml import etree

IN = '../output/indesign/sgsz1.xml'
#OUT = '../output/indesign/step2'
OUT = '../output/indesign/sgsz2.xml'
STEP3 = '../output/indesign/step3'

def handle_text(s):
	if s is None:
		return ''
	s=s.replace('&', '&amp;')
	return s
	
def end_tag(e):
	return '</{}>'.format(e.tag)
	
def open_tag(e):
	r = '<' + e.tag
	for k,v in e.attrib.items():
		r += ' {}="{}"'.format(k, v)
	r += '>'
	return r

def traverse(e):
	r = ''
	s = handle_text(e.text)
	if s != '':
		if e.tag in ('footnote', 'p'):
			r += '<span>{}</span>'.format(s)
		else:
			r += s
	for n in e.iterchildren(): 
		r += handle_node(n)
		s = handle_text(n.tail)
		if s != '':
			if e.tag in ('footnote', 'p'):
				r += '<span>{}</span>'.format(s)
			else:
				r += s
	return r

def flat(e):
	''' 將樹狀結構扁平化，把 span 裡的 footnote 拆出來 '''
	r = ''

	tag1 = open_tag(e)
	tag2 = end_tag(e)

	s = handle_text(e.text)
	if s != '':
		r = tag1 + s + tag2
	for n in e.iterchildren(): 
		r += handle_node(n)
		s = handle_text(n.tail)
		if s != '':
			r += tag1 + s + tag2
	return r

def handle_persName(e):
	''' persName 下的第一個文字或元素放在 persName 裡面, 其餘的拆出來 
	例如 <persName key="A010154" name="𧦪公"><span rend="extb">𧦪</span><span rend="roleName">公</span></persName>
	轉為 <persName key="A010154" name="𧦪公" rend="persName-extb">𧦪</persName><span rend="roleName">公</span>
	'''
	persname_open = True
	s = handle_text(e.text)
	r = ''
	if s != '':
		r += open_tag(e) + s + end_tag(e)
		persname_open = False
	for n in e.iterchildren(): 
		if persname_open:
			if n.tag == 'span':
				e.set('rend', 'persName-'+n.get('rend'))
				r += open_tag(e) + traverse(n) + end_tag(e)
				persname_open = False
			elif n.tag == 'img':
				# 如果 persName 裡面的第一個字是缺字, 就將缺字移出
				r += open_tag(e) + end_tag(e)
				r += open_tag(n) + traverse(n) + end_tag(n)
				persname_open = False
			else:
				sys.exit('error 61 persName 下層含有未知的元素: pb='+pb+', tag: '+n.tag)
		else:
			r += handle_node(n)
		s = handle_text(n.tail)
		if s!= '':
			if persname_open:
				e.set('rend', 'persName')
				r += open_tag(e) + s + end_tag(e)
				persname_open = False
			else:
				r += '<span rend="persName">{}</span>'.format(s)
	return r
	
def handle_placeName(e):
	''' persName 下的第一個文字或元素放在 persName 裡面, 其餘的拆出來 
	'''
	open = True
	rend = e.get('rend', None)
	s = handle_text(e.text)
	r = ''
	if s != '':
		r += open_tag(e) + s + end_tag(e)
		open = False
	for n in e.iterchildren(): 
		if n.tag == 'lb':
			continue
		if open:
			if n.tag == 'span':
				e.set('rend', 'placeName-'+n.get('rend'))
				r += open_tag(e) + traverse(n) + end_tag(e)
				open = False
			else:
				print('error 116, placeName child: '+n.tag)
				print('lb: %s' % lb)
				print('key: %s' % e.get('key'))
				print('s: %s' % s)
				print(traverse(n))
				sys.exit()
		else:
			r += handle_node(n)
		s = handle_text(n.tail)
		if s!= '':
			if open:
				e.set('rend', 'persName')
				r += open_tag(e) + s + end_tag(e)
				open = False
			else:
				if rend is None:
					r += '<span>{}</span>'.format(s)
				else:
					r += '<span rend="{}">{}</span>'.format(rend, s)
	return r

def handle_node(e):
	global lb, pb
	tag = e.tag
	parent = e.getparent()
	if tag=='lb':
		lb = e.get('n')
		r = ''
	elif tag=='pb':
		pb = e.get('n')
		r = open_tag(e) + traverse(e) + end_tag(e)
	elif tag=='persName':
		r = handle_persName(e)
	elif tag=='placeName':
		r = handle_placeName(e)
	elif tag == 'span':
		rend = e.get('rend', '')
		if rend=='extb':
			if parent.tag == 'persName':
				e.set('rend', 'persName-extb')
		r = flat(e)
	else:
		r = open_tag(e) + traverse(e) + end_tag(e)
	return r
	
def insert_underline_separator(mo):
  if mo.group(0).startswith('<p '):
    return mo.group(0)
  return '{}<span rend="underline_separator"> </span>'.format(mo.group(1))

def repl(mo):
	global log
	print(mo.group(0), file=log)
	r = mo.group(1)
	r += 'rend="persName-{}">'.format(mo.group(2))
	r += mo.group(3) + '</persName>'
	r += mo.group(4)
	print(r, file=log)
	return r
	
def out(juan, s):
	fn = 'sgsz-{:02d}.xml'.format(juan)
	fn = os.path.join(OUT, fn)
	fo = open(fn, 'w', encoding='utf_8_sig')
	s = '<root>\n' + s + '</root>'
	fo.write(s)
	fo.close()

log = open('x2id2.log', 'w', encoding='utf_8_sig')
lb = ''
pb = ''

print('x2id2.py')
fi = open(IN, 'r', encoding='utf8')
xml = fi.read()
fi.close()

#xml = re.sub('(<persName [^>]*)rend="persName"><span rend="([^"]*)">([^<]*)</span>(.*?)</persName>', repl, xml)
persnames = re.findall('(<persName[^>]*>(.*?)</persName>)', xml)
for s in persnames:
	if s[1].startswith('<'):
		print(s[0], file=log)

#root = etree.fromstring(xml)
tree = etree.parse(IN)
root = tree.getroot()
text = traverse(root)

# 2018-12-27 改用 x2id3.rb 處理這個問題
# 在兩個地名或人名之間插入空白, 以斷開底線
# 標題裡面不必加
#regexp = r'<p rend="h\d+">.*?</p>|(</persName>|</placeName>|<span rend="name">[^<]*?</span>)(?=<persName|<placeName|<span rend="name")'
#text = re.sub(regexp, insert_underline_separator, text)

#fo = open(OUT, 'w', encoding='utf_8_sig')
fo = open(OUT, 'w', encoding='utf_8')
fo.write('<root>' + text + '</root>')
fo.close()
sys.exit()

# 以下切一卷一檔, 暫時不用
os.makedirs(OUT, exist_ok=True)
os.makedirs(STEP3, exist_ok=True)
juans = re.split('(<p rend="h1">)', text)
j = 1
first = True
s = ''
for juan in juans:
	if juan == '<p rend="h1">':
		if first:
			first = False
			s += juan
		else:
			out(j, s)
			s = juan
			j += 1
	else:
		s += juan
out(j, s)
