# -*- coding: utf-8 *-*
import os, re, sys
from lxml import etree
import zbx_authority

folder='../Song_GSZ'

def myRepl(mo):
	gv['count']+=1
	orig=mo.group(1)
	print(orig, file=log)
	s=orig
	if not s.endswith('/>'): s+='</date>'
	root = etree.XML(s)
	key=root.get('key')
	print(key, file=log)
	done=False
	if root.get('when-iso') is not None:
		if re.match(r'^.*\d\-', root.get('when-iso')): # 如果不只有年份
			info=zbx_authority.getTimeInfo(w=key[1:8])
			root.set('when-iso', info['W']['data1']['ceDate'])
			done=True
		else:
			del root.attrib['when-iso']
	if not done and root.get('from-iso') is not None and root.get('to-iso') is not None :
		info=zbx_authority.getTimeInfo(f=key[1:8], t=key[8:])
		if info is None: 
			print('在 authority 找不到資料', file=log)
			print(gv['fn'], key, file=log)
		else:
			root.set('from-iso', info['F']['data1']['ceDate'])
			root.set('to-iso', info['T']['data1']['ceDate'])
			done=True
	if not done and root.get('notAfter-iso') is not None and root.get('notBefore-iso') is not None :
		info=zbx_authority.getTimeInfo(f=key[1:8], t=key[8:])
		if info is None: 
			print('在 authority 找不到資料', file=log)
			print(gv['fn'], key, file=log)
		else:
			root.set('notBefore-iso', info['F']['data1']['ceDate'])
			root.set('notAfter-iso', info['T']['data1']['ceDate'])
			done=True
	if done:
		r=str(etree.tostring(root), encoding='utf8')
		if not s.endswith('/>'): r=re.sub('^(.*)/>', r'\1>', r)
	else:
		print('when, from, to, notAfter, notBefore 都沒有', file=log)
		r=mo.group(0)
	print(r, file=log)
	print(file=log)
	return r

def do1file(source, target):
	print(source)
	with open(os.path.join(folder, source), 'r', encoding='utf8') as fi:
		text=fi.read()
	text=re.sub('(<date [^>]*?>)', myRepl, text)
	fo=open(os.path.join(folder, target), 'w', encoding='utf8')
	fo.write(text)
	fo.close()

def do1folder(dir1, dir2):
	print(dir1)
	if not os.path.exists(dir2):
		os.makedirs(dir2)
	files=os.listdir(dir1)
	for f in files:
		p1=os.path.join(dir1, f)
		p2=os.path.join(dir2, f)
		if os.path.isdir(p1):
			do1folder(p1, p2)
		elif f.endswith('xml'):
			gv['fn']=f
			do1file(p1, p2)
gv={'count':0}
f1=sys.argv[1]
f2=sys.argv[2]
log=open('date.log', 'w', encoding='utf8')
do1folder(f1, f2)
print('共取代 {} 個 <date>'.format(gv['count']))