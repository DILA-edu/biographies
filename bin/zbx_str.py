#-*- coding:utf-8 -*-
''' 2012.4.27 by 周邦信
'''
import os, re
puncs=(' ', '~', '!', '@', '#', '$', '%', '/', '\\', '^', '&', '*', '(', ')', '[', ']', '{', '}', '-', '+', '=', '<', '>', ';', ':', ',', '.', '?', '`',
'\n', '\r', "'", '"', '　', '，', '。', '！', '．', '；', '：', '︰', '？', '、', '—',
'「', '」', '『', '』', '《', '》', '（', '）', '【', '】', '〈', '〉', '〔', '〕', '”', '“',
'─', '│', '┌', '┐', '└', '┘', '├', '┤', '┬', '┴', '┼',
'○', '▲', '■', '□', '◇', '…', '●', '◎', '∴', '△', '▽', '◑', '←', '→')

def split_chars(str, remove_puncs=True):
	''' 將字串拆為字元 list
	組字式 或 [Z0001] 視為一個字, 5碼Unicode視為一個字 
	'''
	char_pattern='(?:\[[^\]]*?\]|[\ud800-\udbff].|.)'
	chars=re.findall(char_pattern, str, re.DOTALL)
	r=[]
	for s in chars:
		if not s.startswith('['):
			if remove_puncs and (s in puncs): continue
			r.append(s)
			continue
		if re.search(r'[/\*@\-+\?]', s) is not None: # 如果是組字式
			r.append(s)
			continue
		if re.match(r'\[Z\d{4}\]$', s) is not None: # 如果是缺字碼
			r.append(s)
			continue
		for c in s: 
			if remove_puncs and (c in puncs): continue
			r.append(c)
	return r

def split_chinese_chars(s):
	''' 將字串拆為字元 list, 去掉非中文字元
	組字式 視為一個字, 5碼Unicode視為一個字 
	'''
	char_pattern='(?:\[[^\]]*?\]|[\ud800-\udbff].|.)'
	s=remove_diacritics(s)
	chars=re.findall(char_pattern, s)
	r=[]
	for s in chars:
		if not s.startswith('['):
			if s in puncs: continue
			if s.isdigit(): continue
			if re.match('[a-zA-Z]', s) is not None: continue
			r.append(s)
			continue
		if re.search(r'[/\*@\-+\?]', s) is not None: # 如果是組字式
			r.append(s)
			continue
		for c in s: 
			if c in puncs: continue
			if c.isdigit(): continue
			if re.match('[a-zA-Z]', c) is not None: continue
			r.append(c)
	return r

def remove_diacritics(s):
	s=re.sub('[Ā]','A', s)
	s=re.sub('[āáǎàä]','a', s)
	s=re.sub('[Ē]','E', s)
	s=re.sub('[ēéěè]','e', s)
	s=re.sub('[Ḍ]', 'D', s)
	s=re.sub('[ḍ]', 'd', s)
	s=s.replace('ḥ', 'h')
	s=re.sub('[īíǐì]', 'i', s)
	s=re.sub('[ḷ]', 'l', s)
	s=re.sub('[ńňǹṇñṅ]', 'n', s)
	s=re.sub('[ḿṃ]', 'm', s)
	s=re.sub('[Ō]','O', s)
	s=re.sub('[ōóŏǒò]','o', s)
	s=re.sub('[Ś]', 'S', s)
	s=re.sub('[śš]', 's', s)
	s=re.sub('[ṭ]', 't', s)
	s=re.sub('[ūúǔù]','u', s)
	s=re.sub('[üǘǚǜ]','v', s)
	return s

def strip_punctuation(s):
	''' 去除標點, 組字式裡面的不去除 '''
	chars=split_chars(s)
	r=''
	for c in chars:
		if c not in puncs: r+=c
	return r

def normalize_hypy(str):
	tone=5
	r=''
	for c in str:
		if c in 'ĀāĒēīŌōū': tone=1
		elif c in 'áéíńḿóŚśúǘ': tone=2
		elif c in 'ǎěǐňǒšǔǚ': tone=3
		elif c in 'àèìǹòùǜ': tone=4
		r+=remove_diacritics(c)
	return (r, tone)

def hypy2zy(hypy):
	''' 將某個中文字元的漢語拼音轉為注音 '''
	tone_symbol=['', '', 'ˊ', 'ˇ', 'ˋ', '˙']
	if hypy[-1].isdigit():
		py=hypy[:-1]
		tone=int(hypy[-1])
	else:
		(py, tone)=normalize_hypy(hypy)
	py=py.lower()
	return py2zy_table[py]+tone_symbol[tone]

def hypys2zy(str):
	''' 將某個中文字串的漢語拼音轉為注音 '''
	t=str.split()
	r=[]
	for py in t:
		r.append(hypy2zy(py))
	return ' '.join(r)

def html_escape(text):
	html_escape_table = {
		"&": "&amp;",
		'"': "&quot;",
		"'": "&apos;",
		">": "&gt;",
		"<": "&lt;",
	}
	r=''
	for c in text:
		r+=html_escape_table.get(c,c)
	return r

def length(s):
	chars=split_chars(s)
	return len(chars)

def code_point(s):
	if len(s)==1: return ord(s)
	high=ord(s[0])
	if high<0xd800 or high>0xdbff: return high
	low=ord(s[1])
	high=high & 0x3ff
	high+=0x40
	high = high << 10
	low=low& 0x3ff
	return high + low

def substr(s, begin, end):
	''' 取得部份字串
	組字式 視為一個字, 5碼Unicode視為一個字 
	'''
	char_pattern='(?:\[[^\]]*?\]|[\ud800-\udbff].|.)'
	chars=re.findall(char_pattern, s)
	return ''.join(chars[begin:end])

def int2cn(i):
	''' 將 int 轉為中文數字字串, 例如 11 轉為 十一 '''
	i2c = ['', '一', '二', '三', '四', '五', '六', '七', '八', '九']
	tens = int(i / 10)
	r = ''
	if tens > 0:
		if tens > 1:
			r += i2c[tens]
		r += '十'
	units = i % 10
	r += i2c[units]
	return r
	
folder=os.path.dirname(__file__)
py2zy_table={}
fi=open(os.path.join(folder, 'py2zy.txt'), 'r', encoding='utf8')
for line in fi:
	line=line.strip()
	t=line.split('\t')
	py2zy_table[t[0]]=t[1]