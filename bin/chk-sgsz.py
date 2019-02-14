# -*- coding: utf-8 *-*
import os
from lxml import etree
import sw_xml

def chk_notes():
	global fo, text_tree
	print('check notes')
	for e in text_tree.iter('ptr'):
		type=e.get('type')
		if type is None or type=='glossary':
			id=e.get('target')[1:]
			print('check note', id)
			if id not in globals['notes']:
				print('有 <ptr target="#{0}"> 但是沒有 <note id="{0}">'.format(id), file=fo)
			
def chk_ptr(d):
	global fo, text_tree
	print('check <ptr>')
	for e in d.iter('note'):
		id=e.get('id')
		r=text_tree.xpath('//ptr[@target="#{}"]'.format(id))
		if len(r)==0: 
			print('note id:', id, '未使用', file=fo)

def chk_anchor(d):
	global fo, text_tree
	print('check anchor')
	for e in d.iter('app'):
		id=e.get('from')
		r=text_tree.xpath('//anchor[@id="{}"]'.format(id))
		if len(r)==0: 
			print('app from:', id, '沒有對應的 anchor', file=fo)

def chk_name(s, k):
	chars=('，', '　', '‧')
	for c in chars:
		if c in s:
			print('名稱中含有', c, ': ', s, file=fo)
			print('\tkey:', k, file=fo)
			print('\tlb:', globals['lb'], file=fo)

def handleText(s):
	if s is None: return ''
	return s

def traverse(node):
	r=handleText(node.text)
	for n in node.iterchildren(): 
		s=handleNode(n)
		r+=s
		r+=handleText(n.tail)
	return r

def handleNode(e):
	global globals
	r=''
	if e.tag=='anchor':
		id=e.get('id')
		if id is None: return ''
		if id.startswith('end'): return ''
		app=text_tree.xpath('//app[@from="{}"]'.format(id))
		if len(app)==0: 
			print('anchor id:', id, '沒有對應的 app', file=fo)
	elif e.tag=='lb':
		n=e.get('n')
		globals['lb']=n
		pb=n[:5]
		if  pb not in globals['pbs']:
			print('pb不存在:', pb, file=fo)
			globals['pbs'].append(pb)
	elif e.tag=='note':
		id=e.get('id')
		globals['notes'].append(id)
	elif e.tag=='pb':
		globals['pbs'].append(e.get('n'))
	elif e.tag=='persName':
		r=traverse(e)
		chk_name(r, e.get('key'))
		gs = e.xpath('g')
		for g in gs:
			globals['quezi'].add(g.get('ref'))
	elif e.tag=='placeName':
		r=traverse(e)
		chk_name(r, e.get('key'))
		gs = e.xpath('g')
		for g in gs:
			globals['quezi'].add(g.get('ref'))
	else:
		r=traverse(e)
	return r

fo=open('chk-sgsz.log', 'w', encoding='utf8')
globals={
	'pbs':[],
	'notes':[],
	'quezi': set()
}

teiBase = '../Song_GSZ'
xml_file = os.path.join(teiBase, 'wrapper-song.xml')
text_tree = etree.parse(xml_file)
text_tree.xinclude()
text_tree = sw_xml.stripNamespaces(text_tree)
body = text_tree.find('.//body')
for n in body.iter():
	handleNode(n)

d=text_tree.xpath('//back/div[@type="notes"]')
chk_ptr(d[0])
for e in d[0].iter('note'):
	globals['notes'].append(e.get('id'))

d=text_tree.xpath('//back/div[@type="glossary"]')
chk_ptr(d[0])
for e in d[0].iter('note'):
	globals['notes'].append(e.get('id'))

d=text_tree.xpath('//back/div[@type="apparatus"]')
chk_anchor(d[0])

chk_notes()

print('人名或地名中含缺字：', file=fo)
for g in globals['quezi']:
	print(g, file=fo)