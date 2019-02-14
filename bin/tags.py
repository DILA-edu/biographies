# -*- coding: utf-8 *-*
''' 列出所有使用過的標記
'''
import os, re
from lxml import etree
import sw_xml

dir_in='..'

def handle_node(e):
	global tags
	tag=e.tag
	if tag==etree.Comment: 
		return
	if tag not in tags: tags[tag]={}
	for k in e.attrib:
		if k not in tags[tag]:
			tags[tag][k]=[]
		# 下面這些不必列出 attribute 的 value
		if k in ('change', 'cols', 'cRef', 'from', 'from-iso', 'id', 'key', 'n', 'notAfter-iso', 'notBefore-iso', 'ref', 'resp', 'rows', 'target', 'targets', 'to', 'to-iso', 'url', 'when', 'when-iso'): 
			continue
		v=e.get(k)
		if v not in tags[tag][k]:
			tags[tag][k].append(v)

def do1file(filepath):
	print(filepath)
	parser = etree.XMLParser(remove_comments=True)
	tree = etree.parse(filepath, parser)
	tree.xinclude()
	tree=sw_xml.stripNamespaces(tree)
	for e in tree.iter(): 
		handle_node(e)

def do1dir(d, collection):
	l=os.listdir(d)
	for s in l:
		if s.endswith('xml') and s.startswith('wrapper'):
			do1file(d+'/'+s)

# main
fo=open('tags.out', 'w', encoding='utf8')
tags={}
l=os.listdir(dir_in)
for s in l:
	if os.path.isdir(dir_in+'/'+s) and s not in ('bin', 'output'):
		do1dir(dir_in+'/'+s, s)
for tag in sorted(tags.keys()):
	print(tag, file=fo)
	for att in tags[tag]:
		print('\t'+att, file=fo)
		for v in tags[tag][att]:
			print('\t\t'+v, file=fo)