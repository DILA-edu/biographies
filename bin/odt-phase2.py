# coding: utf_8_sig
import os,pickle,re,shutil,sys,zipfile
import zbx_authority, zbx_odt, zbx_chars
import zbx_str

inputFolder='../output/odt'
odtTemp='../output/odt-temp'
refpng='odt-template/Pictures/ref.svg'

hypy_zy_table='ㄅ(b), ㄆ(p), ㄇ(m), ㄈ(f), ㄉ(d), ㄊ(t), ㄋ(n), ㄌ(l), ㄍ(g), ㄎ(k), ㄏ(h), ㄐ(j), ㄑ(q), ㄒ(x), ㄓ(zh,zhi), ㄔ(ch,chi), ㄕ(sh,shi), ㄖ(r,ri), ㄗ(z,zi), ㄘ(c,ci), ㄙ(s,si), ㄧ(yi,-i), ㄨ(wu,-u), ㄩ(yu,-ü,-u), ㄚ(a), ㄛ(o), ㄜ(e), ㄝ(ê), ㄞ(ai), ㄟ(ei), ㄠ(ao), ㄡ(ou), ㄢ(an), ㄣ(en), ㄤ(ang), ㄥ(eng), ㄦ(er), ㄧㄚ(ya,-ia), ㄧㄛ(yo), ㄧㄝ(ye,-ie), ㄧㄞ(yai,-iai), ㄧㄠ(yao,-iao), ㄧㄡ(you,-iu), ㄧㄢ(yan,-ian), ㄧㄣ(yin,-in), ㄧㄤ(yang,-iang), ㄧㄥ(ying,-ing), ㄨㄚ(wa,-ua), ㄨㄛ(wo,-uo), ㄨㄞ(wai,-uai), ㄨㄟ(wei,-ui), ㄨㄢ(wan,-uan), ㄨㄣ(wen,-un), ㄨㄤ(wang,-uang), ㄨㄥ(weng,-ong), ㄩㄝ(yue,-üe,-ue), ㄩㄢ(yuan,-üan,-uan), ㄩㄣ(yun,-ün,-un), ㄩㄥ(yong,-iong)'

name_yin={
	'憑翊'	'féng yì',
	'費縣'	'bì xiàn',
}
place_name_yin={
	'濟':'jǐ',
}
person_name_yin={
	'濟':'jì',
}
last_name_yin={
	'區':'ōu',
	'藏':'cáng',
	'任':'rén',
	'給':'jǐ',
	'仇':'qiú',
	'載':'dài',
	'解':'xiè',
	'亡':'wú',
	'候':'hóu',
}
def handleText(s):
	s=s.replace('\x02','')
	s=re.sub('<a .*?>(.*?)</a>', r'\1', s)
	s=s.replace('&', '&amp;')
	return s

def persNameInPage(key, name, page):
	if (key+name) in personIndexPage:
		if page not in personIndexPage[key+name]:
			personIndexPage[key+name].append(page)
	else:
		personIndexPage[key+name]=[page]
'''
def str2hypy(str, type=None):
	if str in name_yin:
		return name_yin[str]
	chars=zbx.str.split_chars(str)
	r=[]
	first=True
	for c in chars:
		py=''
		if re.match('[A-Za-zāäḍīśšü]', c):
			py=c
		if py=='': # 先在針對人名、地名的讀音表中尋找
			if type=='person':
				if first and c in last_name_yin: # 在姓氏讀音表中尋找
					py=last_name_yin[c]
				else:
					py=person_name_yin.get(c, '')
			elif type=='place':
				py=place_name_yin.get(c, '')
		if py=='':
			py=name_char_yin.get(c, '')
		if py=='':
			unknow=c
			if unknow not in HanYuPinYinUnknow:
				HanYuPinYinUnknow.append(unknow)
		r.append(py)
		first=False
	return ' '.join(r)
'''
def personIndexAdd(key, name, page):
	global personIndexPage
	name=name.replace('<text:soft-page-break/>', '')
	name=name.replace( '　', '')
	persNameInPage(key, name, page)
	try:
		#py=str2hypy(name, 'person')
		py=zbx_authority.get_name_yin('person', name)
		py=py.lower()
		#pi=py+','+name+','+key
		pyn=zbx_str.remove_diacritics(py)
		pi=(pyn, py, name, key)
		if pi not in personIndex:
			personIndex.append(pi)
			return True
		else: return False
	except zbx_chars.zbxError as err:
		for c in err.value:
			if c not in HanYuPinYinUnknow:
				HanYuPinYinUnknow.append(c)
		return False

def placeIndexAdd(key, name, page):
	name=name.replace('<text:soft-page-break/>', '')
	name=name.replace( '　', '')
	if (key+name) in placeIndexPage:
		if page not in placeIndexPage[key+name]:
			placeIndexPage[key+name].append(page)
	else:
		placeIndexPage[key+name]=[page]
	try:
		#py=str2hypy(name, 'place')
		py=zbx_authority.get_name_yin('place', name)
		py=py.lower()
		pyn=zbx_str.remove_diacritics(py)
		if pyn=='':
			print(108, '拼音是空的', name)
		pi=(pyn, py, name, key)
		if pi not in placeIndex:
			placeIndex.append(pi)
			return True
		else: return False
	except zbx_chars.zbxError as err:
		for c in err.value:
			if c not in HanYuPinYinUnknow:
				HanYuPinYinUnknow.append(c)
		return False

def reconstructPersonIndex(content):
	print('reconstruct person index')
	mo=re.search(r'<text:user-index .*?text:name="personNameIndex\d">(.*?)</text:user-index>', content)
	indexDiv=mo.group(1)
	indexes=re.findall(r'<text:p .*?>\[key:(.*?)\](.*?)<text:tab/>(\d*?)</text:p>', indexDiv)
	for index in indexes:
		key=index[0]
		name=index[1]
		page=index[2]
		info=personInfo[key]
		if info is None:
			continue
		#print('[62]', 'key:[{}]'.format(key), 'info:', info, file=log)
		if not name.startswith('釋迦牟尼') and name.startswith('釋'):
			name=name[1:]
		if personIndexAdd(key,name,page):
			if info['name']!=name:
				personIndexAdd(key, info['name'], page)
				#if 'द' in info['name']:
					#print('authority 人名主名稱中含有天城體', file=log)
					#print('\tkey:', key, ', name:', info['name'], file=log)
		names=splitNames(info['names'])
		if '梵文' in names:
			n=names['梵文'].split(',')
			if len(n)>1 and n[0]!=name:
				n=n[0]
				pi=(zbx_str.remove_diacritics(n), n, n, key)
				if pi not in personIndex:
					personIndex.append(pi)
				persNameInPage(key, n, page)
		if '日文' in names:
			n=names['日文'].split(',')
			if len(n)>1 and n[1]!=name:
				n=n[1]
				pi=(zbx_str.remove_diacritics(n), n, n, key)
				if pi not in personIndex:
					personIndex.append(pi) # 日文轉寫名 加入 index
				persNameInPage(key, n, page)
		if 'p' not in info: info['p']=[]
		if page not in info['p']: info['p'].append(page)

def splitNames(names):
	t=names.split('\n')
	r={}
	for s in t:
		mo=re.match(r'\[(.*?)\] (.*)$', s)
		if mo is not None:
			r[mo.group(1)]=mo.group(2)
	return r

def ref_img():
	count['graphic']+=1
	r='''<draw:frame draw:style-name="fr2" draw:name="圖形{0}" text:anchor-type="as-char"
  svg:width="0.36cm" svg:height="0.36cm" svg:y="-0.3cm"
  draw:z-index="0">
  <draw:image xlink:href="Pictures/ref.svg" xlink:type="simple" xlink:show="embed" xlink:actuate="onLoad"/>
 </draw:frame>'''.format(count['graphic'])
	return r

def rebuildPersonIndex(content):
	global personIndex
	print('rebuildPersonIndex')
	personIndex=sorted(personIndex)
	newIndex='<text:h text:style-name="Heading_20_1" text:outline-level="1">人名索引</text:h>'
	newIndex+='<text:h text:style-name="Heading_20_2" text:outline-level="2">人名索引</text:h>'
	newIndex+='<text:h text:style-name="Heading_20_4" text:outline-level="4">人名索引</text:h>'
	newIndex+='<text:p text:style-name="p">依漢語拼音排序 (破音字以一般讀音排序)</text:p>'
	newIndex+='<text:p text:style-name="Standard">注音符號對照漢語拼音簡表：</text:p>'
	newIndex+='<text:p text:style-name="Standard">{}</text:p>'.format(hypy_zy_table)
	newIndex+='<text:section text:style-name="{}" text:name="SectIndexPersonName">'.format(sectionName)
	pyFirstChar=''
	count=0
	for pi in personIndex:
		py=pi[1]
		name=pi[2]
		key=pi[3]
		print(143, key, file=log)
		count+=1
		if count%1000==0:
			print(' rebuildPersonIndex '+key, 'Count:', count)
		s=''
		c=pi[0][0].upper()
		if c!=pyFirstChar:
			pyFirstChar=c
			s+='<text:h text:style-name="Heading_20_4" text:outline-level="4">{}</text:h>\n'.format(pyFirstChar)
		info=personInfo[key]
		if name!=personInfo[key]['name']:
			s+='<text:p text:style-name="indexItem1">'
			s+=name
			if py!=name: s+=' '+py
			#print(name, py, zbx_chars.py2zy(py), file=log)
			s+='：<text:span text:style-name="indexRef">'
			s+=formatPageNumber(personIndexPage[key+name])
			s+=' '+ ref_img() + ' </text:span>'
			s+=info['name']
			s+= ' <text:span text:style-name="small">({})</text:span></text:p>\n'.format(key)
		else:
			#s+='<text:p>' + name + '({}) '.format(key)
			s+='<text:p text:style-name="indexItem1">' + name+' '+py
			#print(name, py, zbx_chars.py2zy(py), file=log)
			years=zbx_authority.personLivingYears(info)
			if years!='': s+=' '+years+';'
			s+=' <text:span text:style-name="small">('+key+'); '
			s+=formatPageNumber(info['p'])+'</text:span>'
			s+='</text:p>\n'
			note=''
			if 'note' in info and info['note'] is not None:
				note= handleText(info['note'])
			if note!='':
				note=re.sub('（[^）]*?）$', '', note)
				s+='<text:p text:style-name="indexItem2">'
				s+= note
				s+='</text:p>\n'
			if 'names' in info:
				names=info['names']
				print(182, names, file=log)
				names=names.replace('\n', '; ')
				names=names.replace(',', ', ')
				if names!='': 
					# 若只有中文別名 就不顯示 [中文]
					languages=re.findall(r'\[[^\]/]+\]', names)
					if len(languages)<2:
						names=names.replace('[中文] ', '')
					print(190, names, file=log)
					s+='<text:p text:style-name="indexItem2">'
					s+='別名：' + names
					s+='</text:p>\n'
		newIndex+=s
	newIndex+='</text:section>'
	print(122)
	content=re.sub(r'<text:user-index .*?text:name="personNameIndex\d">(.*?)</text:user-index>', newIndex, content)
	print(124)
	return content

def reconstructPlaceIndex(content):
	print('reconstructPlaceIndex')
	mo=re.search(r'<text:user-index .*?text:name="placeNameIndex\d">(.*?)</text:user-index>', content, flags=re.DOTALL)
	indexDiv=mo.group(1)
	indexes=re.findall(r'<text:p .*?>\[key:(.*?)\](.*?)<text:tab/>(\d*?)</text:p>', indexDiv)
	for index in indexes:
		key=index[0]
		name=index[1]
		page=index[2]
		if key is None:
			print('error 266: key is None, index:', index)
			sys.exit()
		if placeIndexAdd(key,name,page):
			if placeInfo[key] is None:
				sys.exit('placeInfo[{}] is None'.format(key))
			if placeInfo[key]['name'] is None:
				sys.exit('place id:{} 名稱為 None'.format(key))
			if placeInfo[key]['name']!=name:
				placeIndexAdd(key, placeInfo[key]['name'], page)
		if 'p' not in placeInfo[key]: placeInfo[key]['p']=[]
		if page not in placeInfo[key]['p']: placeInfo[key]['p'].append(page)

def rebuildPlaceIndex(content):
	global placeIndex
	print('rebuildPlaceIndex')
	placeIndex=sorted(placeIndex)
	newIndex='<text:h text:style-name="Heading_20_1" text:outline-level="1">地名索引</text:h>'
	newIndex+='<text:h text:style-name="Heading_20_2" text:outline-level="2">地名索引</text:h>'
	newIndex+='<text:h text:style-name="Heading_20_4" text:outline-level="4">地名索引</text:h>'
	newIndex+='<text:p text:style-name="p">依漢語拼音排序 (破音字以一般讀音排序)</text:p>'
	newIndex+='<text:p text:style-name="Standard">注音符號對照漢語拼音簡表：</text:p>'
	newIndex+='<text:p text:style-name="Standard">{}</text:p>'.format(hypy_zy_table)
	newIndex+='<text:section text:style-name="{}" text:name="SectIndexPlaceName">'.format(sectionName)
	pyFirstChar=''
	for pi in placeIndex:
		py=pi[1]
		name=pi[2]
		key=pi[3]
		s=''
		try:
			c=pi[0][0].upper()
		except:
			print(287, pi)
			sys.exit()
		if c!=pyFirstChar:
			pyFirstChar=c
			s+='<text:h text:style-name="Heading_20_4" text:outline-level="4">{}</text:h>\n'.format(pyFirstChar)
		info=placeInfo[key]
		if name!=info['name']:
			s+='<text:p text:style-name="indexItem1">'
			s+=name+' '+py
			#print(name, py, zbx_chars.py2zy(py), file=log)
			s+=' <text:span text:style-name="place_id">({})</text:span>'.format(key)
			s+='：<text:span text:style-name="indexRef">'
			s+= formatPageNumber(placeIndexPage[key+name])
			#s+='【參】</text:span>'
			s+=' '+ ref_img()+' </text:span>'
			s+=info['name'] + '</text:p>\n'
		else:
			#s+='<text:p text:style-name="indexItem1">' + name
			s+='<text:p text:style-name="indexItem1">' + name+' '+py
			#print(name, py, zbx_chars.py2zy(py), file=log)
			s+=' <text:span text:style-name="place_id">({})</text:span>'.format(key)
			if 'long' in info:
				s+='<text:span text:style-name="longitude_and_latitude">'
				s+=' ({0}, {1})'.format(info['long'],info['lat']) # 經緯度
				s+='</text:span>'
			#s+=', '.join(info['p'])
			s+= '<text:span text:style-name="small">'
			s+= ' ' + formatPageNumber(info['p']) # 頁碼
			s+='</text:span>'
			s+='</text:p>\n'
			if 'districtModern' in info and isinstance(info['districtModern'], str):
				s+='<text:p text:style-name="indexItem2">行政區：'
				s+=info['districtModern'].rstrip('-').replace('\u3000','')
				s+='</text:p>\n'
			if 'cities' in info:
				s+='<text:p text:style-name="indexItem2">包含地名：'
				s+=info['cities']
				s+='</text:p>\n'
			note=''
			if 'note' in info and info['note'] is not None:
				note= handleText(info['note'])
			if note!='':
				note=re.sub('（[^）]*?）$', '', note)
				s+='<text:p text:style-name="indexItem2">'
				s+= note
				s+='</text:p>\n'
		newIndex+=s
	newIndex+='</text:section>'
	print(177)
	content=re.sub(r'<text:user-index .*?text:name="placeNameIndex\d">(.*?)</text:user-index>', newIndex, content)
	return content

def formatPageNumber(pages):
	''' p. 1, 2, 3 => p. 1-3'''
	newPages=[]
	for p in pages: 
		n=int(p)
		newPages.append([n,n])
	i=0
	while i<(len(newPages)-1):
		if (newPages[i][1]+1)==newPages[i+1][0]:
			newPages[i][1]=newPages[i+1][1]
			del newPages[i+1]
		else: i+=1
	r=''
	for p in newPages:
		if r!='': r+=', '
		if p[0]==p[1]: r+=str(p[0])
		elif p[1]-p[0]<2: r+=str(p[0])+insertStringWithStyle('f','italic')
		else: r+=str(p[0])+insertStringWithStyle('ff','italic')
	return r

def insertStringWithStyle(text, style):
	return '<text:span text:style-name="{1}">{0}</text:span>'.format(text, style)

def handle_rolename(mo):
	s=mo.group(1)
	tokens=re.findall('<text:note .*?>.*?</text:note>|<[^>]*?>[^<]*?<[^>]*?>|[\ud800-\udbff].|.', s)
	r=''
	for c in tokens:
		t='<text:span text:style-name="roleName">' + c + '</text:span>'
		r+=t
	return r

def read_name_char_yin():
	fi=open('name-char-yin.txt', 'r', encoding='utf8')
	r={}
	for line in fi:
		if line.startswith('#'): continue
		line=line.strip()
		t=line.split('\t')
		r[t[0]]=t[1]
	fi.close()
	return r

# main
name_char_yin=read_name_char_yin()
HanYuPinYinUnknow=[]
log=open('odt-phase2.log', 'w', encoding='utf8')

odtFile=os.path.join(inputFolder, 'sgsz-phase1.odt')
z=zipfile.ZipFile(odtFile, mode='r')
try:
	if os.path.exists(odtTemp): 
		shutil.rmtree(odtTemp)
	z.extractall(odtTemp)
except:
	sys.exit('請關閉資料夾: ' + odtTemp)
z.close()
shutil.copy(refpng, os.path.join(odtTemp, 'Pictures'))

contentFile=os.path.join(odtTemp,'content.xml')
fi=open(contentFile,'r',encoding='utf8')
content=fi.read()
fi.close()

mo=re.findall(r'draw:name="圖形(\d+)"', content)
count={}
count['graphic']=int(mo[-1])
print('graphic count: ', count['graphic'])

mo=re.search('<text:user-index text:style-name="([^"]*?)" text:name="personNameIndex1">', content)
sectionName=mo.group(1)
print(286, sectionName)

# 重做 place index
placeIndex=[]
placeIndexPage={}
print('load placeAuthority.pickle')
with open('placeAuthority.pickle', 'rb') as f:
	placeInfo = pickle.load(f)
reconstructPlaceIndex(content)
content=rebuildPlaceIndex(content)

# 重做 person index
personIndex=[]
personIndexPage={}
with open('personAuthority.pickle', 'rb') as f:
	personInfo = pickle.load(f)
reconstructPersonIndex(content)
content=rebuildPersonIndex(content)

print('段落間換行')
content=content.replace('</text:p><text:p', '</text:p>\n<text:p')

#content=re.sub('<text:span text:style-name="roleName">(.*?)</text:span>', handle_rolename, content)
#content=content.replace('</text:p>', '</text:p>\n')
with open(contentFile,'w',encoding='utf8') as fo:
	fo.write(content)

odtFile=os.path.join(inputFolder, 'sgsz.odt')
zbx_odt.packODT(odtTemp, odtFile)

if len(HanYuPinYinUnknow)>0:
	print('缺漢語拼音, 詳見 log')
	for s in HanYuPinYinUnknow:
		print('缺漢語拼音: [{}]'.format(s), file=log)
else:
	print('成功')