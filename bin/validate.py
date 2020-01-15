# -*- coding: utf8 -*-
'''
2011.1.7-4.13 Ray Chou

mac
	conda activate base
	python validate.py /Library/jing/jing.jar
'''

from lxml import etree
import codecs,datetime,glob,os,re,shutil,sys,time

rnc='../Schema/gisSchema.rnc'
fn_out='validate.txt'

def my_mkdir(p):
	if not os.path.exists(p): os.mkdir(p)

def validate(p):
	global jing
	cmd='java -Dorg.apache.xerces.xni.parser.XMLParserConfiguration=org.apache.xerces.parsers.XIncludeParserConfiguration '
	cmd+='-jar %s' % jing
	
	folder=os.path.dirname(p)
	l=glob.glob(folder+'/*.rnc')
	if len(l)>0:
		cmd += ' -c %s ' % l[0]
	else:
		cmd += ' -c %s ' % rnc
	cmd+='%s 2>&1 >> %s' % (p, 'validate.txt')
	print(cmd+'\n')
	os.system(cmd)

def do1vol(vol):
	for p in glob.iglob(phase4dir+'/'+vol[:1]+'/'+vol+'/*.xml'): validate(p)
	print(vol)
	log.write(vol+'\n')

def do1dir(dir, sel):
	vols=os.listdir(dir)
	vols.sort()
	for vol in vols:
		if re.match(os.environ['SEL'], vol): 
			if vol in ('T56', 'T57'): continue
			if sel=='' or vol.startswith(sel): do1vol(vol)

# main
if len(sys.argv) > 1:
	jing = sys.argv[1]
else: 
	jing='d:/bin/jing/jing.jar'

if os.path.exists('validate.txt'): os.remove('validate.txt')
validate('../Tang_GSZ/wrapper-tang.xml')
validate('../Song_GSZ/wrapper-song.xml')
validate('../biQiuNi/wrapper-biqiuni.xml')
validate('../Liang_GSZ/wrapper-liang.xml')
validate('../Ming_GSZ/wrapper-ming.xml')
validate('../Mingsengzhuanchao/MSCCwrapper-Mingsengzhuanchao.xml')
validate('../chuSanZangJiJi/wrapper-chuSanZangJiJi.xml')
validate('../Buxu_GSZ/wrapper-buxu.xml')
validate('../Xinxu_GSZ/wrapper-xinxu.xml')