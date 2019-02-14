#-*- coding:utf-8 -*-
''' 2012.5.27 by 周邦信
'''
__author__          = "周邦信"
__email__           = "zhoubx@gmail.com"
__license__         = "GPL http://www.gnu.org/licenses/gpl.txt"
__date__            = "2012.5.14"

import os
import zbx_str

def get_readings(char):
	''' 傳入某個字元, 傳回一個 list 包含該字元的漢語拼音.
	如果沒有該字元的讀音資料, 就傳回 None. '''
	i=zbx_str.code_point(char)
	c='{:X}'.format(i)
	if c in unihan_readings:
		r=unihan_readings[c]
		if len(r)>0: 
			return list(r)
		else:
			return None
	else:
		return None

def strokes():
	folder=os.path.dirname(__file__)
	fi=open(os.path.join(folder, 'Unihan_DictionaryLikeData.txt'), 'r', encoding='utf8')
	r = {}
	for line in fi:
		if line.startswith('#'):
			continue
		line = line.strip()
		if line == '':
			continue
		(uni, type, n) = line.split('\t')
		if type == 'kTotalStrokes':
			r[uni[2:]] = int(n)
	fi.close()
	return r

folder=os.path.dirname(__file__)
unihan_readings={}
fi=open(os.path.join(folder, 'Unihan_Readings.txt'), 'r', encoding='utf8')
for line in fi:
	if line.startswith('#'): continue
	line=line.strip()
	if line=='': continue
	t=line.split('\t')
	char=t[0][2:]
	field=t[1]
	value=t[2]
	if char not in unihan_readings:
		unihan_readings[char]=set()
	if field=='kHanyuPinyin':
		# U+34D8	kHanyuPinyin	10278.080,10278.090:sù
		# U+3B8F	kHanyuPinyin	21244.040:nài,nì,nà 80020.040:nà,nài,nì
		groups=value.split(' ')
		for g in groups:
			g=g.partition(':')[2]
			t=g.split(',')
			for py in t: unihan_readings[char].add(py)
	elif field=='kMandarin':
		unihan_readings[char].add(value)
fi.close()

