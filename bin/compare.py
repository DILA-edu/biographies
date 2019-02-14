# -*- coding: utf-8 *-*
''' txt 比對
'''
import difflib, os, re, sys

dir1='../Song_GSZ'
dir2='../output/xml'

def myReadLines(f):
	fi=open(f, 'r', encoding='utf8')
	r=[]
	for line in fi:
		line=line.strip()
		if line!='':
			r.append(line+'\n')
	return r

def comp_file(p1, p2):
	print(p1)
	s1=myReadLines(p1)
	s2=myReadLines(p2)
	prev_line=''
	buf=''
	for line in difflib.ndiff(s1, s2):
		if re.match('[+\-?]', line):
			if line.strip()=='+': continue
			if line.startswith('?'): continue
			if line.startswith('-') and prev_line.startswith('+'): buf+='\n'
			buf+=line
			prev_line=line
	if buf!='':
		print('-'*40, file=fo)
		print(p1, p2, file=fo)
		fo.write(buf)

def comp_folder(d1, d2):
	files=os.listdir(d1)
	for f in files:
		if not f.endswith('.xml'):
			continue
		p1=os.path.join(d1, f)
		p2=os.path.join(d2, f)
		if os.path.isdir(p1):
			comp_folder(p1, p2)
		else:
			comp_file(p1, p2)

fo=open('compare.out', 'w', encoding='utf8')
if len(sys.argv)>1:
	f=sys.argv[1]+'.txt'
	comp_file(os.path.join(dir1, f), os.path.join(dir2, f))
else:
	comp_folder(dir1, dir2)
