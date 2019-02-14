# coding: utf_8_sig
''' 將 TEI XML 轉為 OpenOffice ODT
只執行第一卷: x2odt.py -j 1
執行1~15卷: x2odt.py -b 1 -e 15
'''
import collections, logging, os, pickle, re, shutil, sys
from optparse import OptionParser
from lxml import etree
import sw_xml, zbx_odt, zbx_authority

__author__ = 'Ray Chou'
__email__ = 'zhoubx@gmail.com'
__license__ = 'GPL http://www.gnu.org/licenses/gpl.txt'
__date__ = '2011.7.12'

teiBase = '../Song_GSZ'
odtTemp='../output/odt-temp'
section_index='Sect2'
folder_out='../output/odt'
logFilename='x2odt.log'
QUEZI='../Song_GSZ/gaiji'

ancestors = []
count=collections.Counter()
level=collections.Counter()
level['list-max']=0
opened={'block':''}
charStyle=[]
current_pb=''
styles=[]
globals={
	'div-level':0,
	'first_head':True, 
	'head-level':0,
	'heading1':'',
	'heading2':'',
	'note2ptr':{}, 
	'current_apps':{}, 
	'lb' : '',
	'note_count': 0,
	'note_ser': collections.OrderedDict(),
	'pb':'', 
	'page number for margin':'',
	'endnotes':'',
	'endnote-ser':{},
}

def inherit_style(css):
	if len(styles)==0:
		return css.copy()
	
	r = styles[-1].copy()
	for k, v in css.items():
		if k in r:
			if k == 'margin-left':
				i = int(r[k].replace('em', '')) + int(v.replace('em', ''))
				r[k] = '{}em'.format(i)
			else:
				r[k] = v
		else:
			r[k] = v
	return r
	
def handle_text(s, mode='tag'):
	if s is None: return ''
	if mode=='tag':
		s=s.replace('&', '&amp;')
		s=s.replace('\n', '')
	r = s
	if mode=='tag':
		r = ''
		font_size = ''
		if len(styles)>1:
			css = styles[-1]
			font_size = css.get('font-size', '')
		# 同一行如果有兩個5碼Unicode, 第二個5碼Unicode會呈現不出來, 所以必須指定 ExtB 字型
		# 例如 g084: 𢌞映負險。加以𣸧洞迷嵐
		for c in s:
			if c > '\uFFFF':
				if 'head' in ancestors:
					if font_size  == 'small':
						r += span('ExtBSmall', c)
					else:
						r += span('ExtB', c)
				else:
					if font_size  == 'small':
						if 'persName' in ancestors:
							r += span('persName_ExtB_Small', c)
						elif 'placeName' in ancestors:
							r += span('placeName_ExtB_Small', c)
						else:
							r += span('ExtBSmall', c)
					else:
						if 'persName' in ancestors:
							r += span('persName_ExtB', c)
						elif 'placeName' in ancestors:
							r += span('placeName_ExtB', c)
						else:
							r += span('ExtB', c)
			else:
				r += c
	return r

def traverse(node):
	r=handle_text(node.text)
	for n in node.iterchildren(): 
		r+=handle_node(n)
		r+=handle_text(n.tail)
	return r

def dateFormat(d):
	pre=''
	s=d
	if d.startswith('-'): 
		pre='-'
		s=d[1:]
	elif d.startswith('+'):
		s=d[1:]
	return pre + s.lstrip('0').replace('-','.').replace('.0', '.')

def get_ancestors(e):
	r=[]
	for ancestor in e.iterancestors():
		r.append(ancestor.tag)
	return r

def has_ancestor(e, anc):
	r=[]
	for a in e.iterancestors():
		if a.tag == anc:
			return True
	return False

def get_text(e):
	r=''
	if e.tag==etree.Comment: return ''
	if e.tag=='sic': return ''
	elif e.tag=='orig': return ''
	else:
		r=handle_text(e.text, mode='text')
		for n in e.iterchildren(): 
			r+=get_text(n)
			if e.tag!='choice':
				r+=handle_text(n.tail, mode='text')
	return r

def create_footnote(s):
	global count
	new='text:anchor-type="as-char" svg:y="-0.27cm" svg:width="0.32cm" svg:height="0.32cm"'
	s=re.sub('<draw:frame draw:style-name="fr2" draw:name="(.*?)" text:anchor-type="as-char" svg:y=".*?" svg:width=".*?" svg:height=".*?"', r'<draw:frame draw:style-name="fr2" draw:name="\1" '+new, s)
	count['footnote']+=1
	r='<text:note text:id="ftn{0}" text:note-class="footnote">'.format(count['footnote'])
	r+=' <text:note-citation>A</text:note-citation>'
	r+=' <text:note-body>'
	r+='  <text:p text:style-name="Footnote">{0}</text:p>'.format(s)
	r+=' </text:note-body>'
	r+='</text:note>'
	return r

def create_endnote(id):
	global count, globals
	if id in globals['endnote-ser']:
		n=globals['endnote-ser'][id]
	else:
		count['endnote']+=1
		n=count['endnote']
		globals['endnote-ser'][id]=n
		if id not in notes:
			sys.exit('error 106: 有 <ptr target="#{0}"> 但是沒有 <note id="{0}">'.format(id))
		text=notes[id]
		#globals['endnotes']+='<text:p text:style-name="Endnote">【{}】 {}</text:p>'.format(n, text)
		globals['endnotes']+='<text:p text:style-name="Endnote">[{}] {}</text:p>'.format(n, text)
	# 因為【】視覺上太佔空間, 所以改用 []
	#r=open_char_style('endnote_anchor') + '【{}】'.format(n) + close_char_style()
	r=open_char_style('endnote_anchor') + '[{}]'.format(n) + close_char_style()
	return r

def handle_cell(e):
	r='<table:table-cell table:style-name="表格1.A1" office:value-type="string"'
	if e.get('cols') is not None:
		r+=' table:number-columns-spanned="{}"'.format(e.get('cols'))
	if e.get('rows') is not None:
		r+=' table:number-rows-spanned="{}"'.format(e.get('rows'))
	r+='>\n'
	if len(e)>0 and e[0].tag=='p':
		r+=traverse(e)
	else:
		r+=openBlock(type='p', style='Standard')
		r+=traverse(e)
		r+=closeBlock()+'\n'
	r+='</table:table-cell>\n'
	return r

def handle_choice(e):
	r=''
	if e.find('sic') is not None and e.find('corr') is not None:
		corr=handle_node(e.find('corr'))
		sic=handle_node(e.find('sic'))
		s=e.findtext('note')
		r=corr
		if len(globals['current_apps'])>0: # 如果 choice 是包在 app 裏, 就不產生 footnote
			print('choice在app裡, lb:', globals['lb'], file=log)
			# 已經有校勘, 就一定會有大正藏是什麼字, 就不必再說原大正藏作什麼了
			#if s is None:
			#	s='原《大正藏》作「{}」。'.format(sic)
			if s is not None:
				for k in globals['current_apps']: 
					globals['current_apps'][k]+=s
					print('\t'+k, file=log)
		else:
			if s is None:
				s='底本「{0}」的勘誤。'.format(sic)
			r += create_footnote(s)
	elif e.find('orig') is not None and e.find('reg') is not None:
		reg=handle_node(e.find('reg'))
		orig=handle_node(e.find('orig'))
		s=e.findtext('note')
		if s is None:
			s='底本「{0}」的通用字。'.format(orig)
		r=reg
		if len(globals['current_apps'])>0:
			for k in globals['current_apps']: globals['current_apps'][k]+=s
		else:
			r+=create_footnote(s)
	return r

def date_abbr(pre, d1, d2):
	t1=d1.split('.')
	t2=d2.split('.')
	# 如果有「約」, 而且起迄年份相同, 就只顯示年份
	if pre!='' and t1[0]==t2[0]:
		return pre+t1[0]
	return pre+'{0}~{1}'.format(d1, d2)

def handle_date(e):
	print('<date>', 'key:', e.get('key'), file=log)
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
		r=open_char_style('dynasty') + r + close_char_style()
	else:
		s=''
		if e.get('when-iso') is not None:
			#r+=open_char_style('date-iso')
			#r+='({})'.format(dateFormat(e.get('when-iso')))
			#r+=close_char_style()
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
				#r+=open_char_style('date-iso')
				#r+='('+pre+date_abbr(dateFormat(d1), dateFormat(d2))+')'
				#r+=close_char_style()
				s=date_abbr(pre, dateFormat(d1), dateFormat(d2))
		if s!='':
			if globals['mode']=='notes':
				r+='('+s+')'
			else: r+=create_footnote(s)
	print(r, file=log)
	return r

def icon(wit):
	icons={
		'ref': 'ref.svg',
		'CBETA': 'cbeta.svg',
		'大': 'da.svg',
		'宋': 'song.svg',
		'元': 'yuan.svg',
		'范': 'fan.svg',
		'磧': 'qi.svg',
		'南藏': 'nan.svg',
	}
	t=re.split('[【】]', wit)
	r=[]
	for c in t:
		if c=='': continue
		if c in icons:
			count['graphic']+=1
			s='''<draw:frame draw:style-name="fr1" draw:name="圖形{0}" text:anchor-type="as-char"
  svg:y="-0.3cm" svg:width="0.36cm" svg:height="0.36cm"
  draw:z-index="0">
  <draw:image xlink:href="Pictures/{1}" xlink:type="simple" xlink:show="embed" xlink:actuate="onLoad"/>
</draw:frame>'''.format(count['graphic'], icons[c])
		else: s='【{}】'.format(c)
		r.append(s)
	return ' '.join(r)

def handle_g(e):
	global count
	ref=e.get('ref')
	if not ref.startswith('#'):
		print('error 250 ref 屬性應該要以 # 開頭: <g ref="{}">'.format(ref))
		return ''
	url=ref[1:]+'.svg'
	source=os.path.join(QUEZI, ref[1:]+'.svg')
	if not os.path.exists(source):
		print('error 255: '+source+' not exists')
		return '{'+ref+'}'
	target=os.path.join(odtTemp,'Pictures',url)
	shutil.copyfile(source, target)
	count['graphic']+=1
	args = {
		'g': count['graphic'],
		'url': url
	}
	if globals['mode'] == 'notes':
		args['y'] = '-0.32cm'
		args['width'] = '0.32cm'
		args['height'] = '0.32cm'
	else:
		args['y'] = '-0.4cm'
		args['width'] = '0.38cm'
		args['height'] = '0.38cm'
	r='''<draw:frame draw:style-name="fr2" draw:name="圖形{g}" text:anchor-type="as-char" svg:y="{y}" svg:width="{width}" svg:height="{height}" draw:z-index="0">
  <draw:image xlink:href="Pictures/{url}" xlink:type="simple" xlink:show="embed" xlink:actuate="onLoad"/>
 </draw:frame>'''.format(**args)
	return r

def handle_graphic(e):
	global count
	url=e.get('url')
	folder=re.sub(r'(\d)B(\d\d\d)P\d\d\d\.jpg', r'\1Book\2', url)
	source=os.path.join(jpgBase,folder,url)
	target=os.path.join(odtTemp,'Pictures',url)
	shutil.copyfile(source, target)
	count['graphic']+=1
	#r=openBlock('p', "Text_20_body")
	r='''<draw:frame draw:style-name="fr1" draw:name="圖形{0}" text:anchor-type="as-char"
  style:rel-width="90%" style:rel-height="90%" svg:width="0.041cm" svg:height="0.041cm"
  draw:z-index="0">
  <draw:image xlink:href="Pictures/{1}" xlink:type="simple" xlink:show="embed" xlink:actuate="onLoad"/>
 </draw:frame>'''.format(count['graphic'], url)
	return r
	
def heading(level, s):
	if globals['first_head']:
		style='content_begin'
		globals['first_head']=False
	else:
		style='Heading_20_{}'.format(level)
	r=openBlock('h', style, level)
	r+=s
	r+=closeBlock()
	return r

def error(msg):
	print(msg)
	print('pb:', globals['pb'], 'lb:', globals['lb'])
	print()

def check_name(key, name):
	if ' ' in name: error('警告: 名稱裡有空白字元, key:{}, name:[{}]'.format(key,name))
	if name.startswith('（'): error('警告: 名稱的第一個字元是（, key:{}, name:{}'.format(key,name))
	if name.startswith('>'): error('警告: 名稱的第一個字元是>, key:{}, name:{]'.format(key,name))
	if name.startswith('['): error('警告: 名稱的第一個字元是[, key:{}, name:{}'.format(key,name))

def handle_name(e):
	if 'head' in get_ancestors(e): # 如果在 head 裡, 就不加底線
		r=traverse(e)
	else:
		r = '<text:span text:style-name="underline_space"> </text:span>'
		r += open_char_style('name')
		r += traverse(e)
		r += close_char_style()
		r += '<text:span text:style-name="underline_space"> </text:span>'
	
	# 兩個名稱中間的底線要斷開
	#if followed_by_name(e):
	r+='<text:span text:style-name="underline_separator">　</text:span>'
	return r

def handle_persName(e):
	key=e.get('key')
	r=''
	if (key is not None) and (key!='unknown') and key!='' and 'note' not in get_ancestors(e):
		name=get_text(e)
		check_name(key,name)
		if (len(name)>1) or (key not in name_keys_len2):
			r='<text:user-index-mark text:string-value="[key:{0}]{1}" text:index-name="personNameIndex" text:outline-level="1"/>'.format(key,name)
	if has_ancestor(e, 'head'):
		r+=traverse(e)
	else:
		if len(charStyle)>0 and charStyle[-1]=='small': 
			style='persNameSmall'
		else: 
			style='persName'
		r+=open_char_style(style)
		r+=traverse(e)
		r+=close_char_style()
	
	return r

def handle_placeName(e):
	key=e.get('key')
	#print('handle_placeName key='+str(key), file=log)
	r=''
	if (key is not None) and (key!='unknown') and 'note' not in get_ancestors(e):
		name=get_text(e)
		check_name(key,name)
		r='<text:user-index-mark text:string-value="[key:{0}]{1}" text:index-name="placeNameIndex" text:outline-level="1"/>'.format(key,name)
		
	s=traverse(e)
	if has_ancestor(e, 'head'):
		r+=s
	else: 
		if e.find('placeName') is None:
			# 內文上標, 需要一個把底線拉在下面的 space
			r += '<text:span text:style-name="underline_space"> </text:span>'
			r += '<text:span text:style-name="placeName">{}</text:span>'.format(s)
			r += '<text:span text:style-name="underline_space"> </text:span>'
			# 兩個名稱中間的底線要斷開
			r+='<text:span text:style-name="underline_separator">　</text:span>'
		else: # 如果是 placeName 又包 placeName, 外層的 placeName 不加底線
			r += s
	
	return r

def followed_by_name(e):
	next=e.getnext()
	while next is not None and next.tag=='lb':
		next=next.getnext()
	if next is not None and next.tag in ('name', 'placeName','persName'):
		return True
	return False

def handle_table(e):
	global count
	count['table']+=1
	r='<table:table table:name="表格{}" table:style-name="表格1">\n'.format(count['table'])
	cols=0
	row=e.find('row')
	for cell in row.iterchildren('cell'):
		if cell.get('cols') is None: cols+=1
		else: cols+=int(cell.get('cols'))
	r+='<table:table-column table:style-name="表格1.A" table:number-columns-repeated="{}"/>\n'.format(cols)
	r+=traverse(e)+'\n'
	r+='</table:table>\n'
	return r

def handle_anchor(e):
	r=''
	id=e.get('id')
	if id is not None:
		print('anchor id:', id, file=log)
		app_id=id[3:]
		if app_id not in appId2Ser:
			print('anchor ID 在 sgszApparatus.xml 不存在: '+id, file=error_log)
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
						r+=create_footnote(s)
						print(330, r, file=log)
					del globals['current_apps'][app_id]
	return r

def handle_head(e):
	parent=e.getparent()
	if parent.tag=='cell':
		r=openBlock('p', 'cell_head', globals['head-level'])
		r+=traverse(e)
		r+=closeBlock()
		return r

	# 過濾標題中的連結, 給目錄、頁首用
	head=traverse(e)
	pure_head=re.sub(r'<text:span text:style-name="small">\[<text:bookmark.*?</text:a>\]</text:span>', '', head)
	pure_head=re.sub('<text:user-index-mark .*?/>', '', pure_head)
	pure_head=re.sub('<text:note .*?</text:note>', '', pure_head, flags=re.DOTALL)
	#pure_head=re.sub(r'<text:span text:style-name="endnote_anchor">【\d+】</text:span>', '', pure_head)
	pure_head=re.sub(r'<text:span text:style-name="endnote_anchor">\[\d+\]</text:span>', '', pure_head)
	pure_head=pure_head.replace('<text:span text:style-name="underline_separator">　</text:span>', '')
	r=''
	
	# 標題1 給 頁首 用
	if globals['div-level']==1:
		heading1=pure_head
		globals['juan']=pure_head
		child_div=parent.find('div')
		type=child_div.get('type')
		if type is not None:
			heading1+=' ‧ '+type
		r+=heading(1, heading1)
		globals['heading1']=heading1
	
	# 標題2~3 給目錄用
	r+=heading(globals['head-level']+1, pure_head)
	# 如果是某個傳的開頭, 就 show 行號
	if parent.tag=='div' and parent.get('id') is not None:
		globals['page number for margin']=margin(globals['lb'])
	if len(pure_head)>20:
		head = head.replace('（', '<text:line-break/>（')
	r+=heading(globals['head-level']+3, head)
	return r

def handle_div(e):
	if (e.get('type')=='juan'):
		# 只做某一卷
		if options.juan is not None:
			if e.get('n')!=options.juan:
				return ''
		# 指定卷數範圍
		if options.juan_begin is not None and options.juan_end is not None:
			n = int(e.get('n'))
			if (n < options.juan_begin) or (n > options.juan_end):
				return ''
			
	# 只做某一個傳
	if options.zhuang is not None:
		id=e.get('id')
		z=options.zhuang
		if id!=z:
			if len(e.xpath('descendant::div[@id="{}"]'.format(z)))==0:
				if len(e.xpath('ancestor::div[@id="{}"]'.format(z)))==0:
					return ''
	r=''
	#if 'id' in e.attrib:
	#	globals['pb_buf']=globals['pb']
	globals['div-level']+=1
	if globals['div-level']>level['div-max']: level['div-max']=globals['div-level']
	if globals['div-level']==2:
		if 'juan' in globals: heading1=globals['juan']
		else: heading1=''
		type=e.get('type')
		if type is not None:
			heading1+=' ‧ '+type
			if heading1!=globals['heading1']:
				r+=heading(1, heading1)
				globals['heading1']=heading1
	if e.find('head') is not None:
		globals['head-level']+=1
		r+=traverse(e)
		globals['head-level']-=1
	else:
		r+=traverse(e)
	globals['div-level']-=1
	return r

def margin(n):
	return '''<draw:frame text:anchor-type="char" draw:z-index="0"
			draw:style-name="gr1" draw:text-style-name="P1"
			svg:width="2cm" svg:height="0.5cm" 
			svg:x="0cm" svg:y="0cm">
		<draw:text-box>
			<text:p text:style-name="P1"><text:span text:style-name="T1">{}</text:span></text:p>
		</draw:text-box>
		</draw:frame>'''.format(n)

def handle_note(e, css):
	r=''
	if css.get('display','')=='none': return ''
	if e.get('place')=='inline': r=create_footnote(traverse(e))
	elif 'id' in e.attrib:
		note_id=e.get('id')
		if note_id in globals['note2ptr']: # 有用到的 note 才出來
			r+=openBlock('p', 'ListItem1')+'['
			bookmark='ptr'+globals['lb']+note_id
			#r+='<text:bookmark text:name="note{0}"/>{0}'.format(note_id)
			r+='<text:bookmark text:name="note{}"/>{}'.format(note_id, globals['note_ser'][note_id])
			r+=']'+traverse(e)
			if note_id in globals['note2ptr']:
				#r+= '(Link back to: '
				r+=' '
				s=''
				for ptr in globals['note2ptr'][note_id]:
					if s!='': s+=', '
					mo=re.match(r'ptr(\d+)([a-z])(\d\d)', ptr)
					t=mo.group(1).lstrip('0')+mo.group(2)+mo.group(3).lstrip('0')
					s+='<text:a xlink:type="simple" xlink:href="#{0}">{1}</text:a>'.format(ptr, t)
					#r+='<text:a xlink:type="simple" xlink:href="#{0}">{0}</text:a>, '.format(ptr)
				#r+=')'
				r+=s
			r+=closeBlock()
	return r

def handle_seg(e):
	if e.get('type') in ('note', 'pronunciation'):
		return ''
		
	r = ''
	if ('head' in ancestors) and ('display:inline' not in e.get('rend')):
		r+=openBlock('p', 'p')
	css=parse_css(e.get('rend'))
	if ('font-size' in css) and (css['font-size']=='small'):
		r+=write_string(' ', 'ming')
		r+=open_char_style('small')
		s=traverse(e)
		if s.startswith('（') and s.endswith('）'): s=s[1:-1]
		r+=s
		r+=close_char_style()
		r+=write_string(' ', 'ming')
	else: r=traverse(e)
	return r

def handle_node(e):
	global globals, notes, ancestors, styles
	tag=e.tag
	if tag==etree.Comment: return ''
	
	print('handle_node()'+tag, file=log)
	
	# rend='visibility:hidden' 不呈現
	css=parse_css(e.get('rend'))
	if 'visibility' in css and css['visibility']=='hidden':
		return ''

	# 繼承上一層樣式
	if len(styles)==0:
		style=css.copy()
	else:
		style = inherit_style(css)
	styles.append(style)

	parent=e.getparent().tag
	ancestors.append(e.tag)
	r=''
	if tag=='add':
		s=traverse(e)
		r+=s
		s='原《大正藏》無「{}」。'.format(s)
		r += create_footnote(s)
	elif tag=='anchor': r=handle_anchor(e)
	elif tag=='byline':
		r+=openBlock('p', 'byline')
		r+=traverse(e)
		r+=closeBlock()
	elif tag=='caesura':
		r=open_char_style('ming') # 因為 HAN NOM 字型的全形空白很小, 所以要換明體
		r+='　'
		r+=close_char_style()
	elif tag=='cell': r=handle_cell(e)
	elif tag=='choice': r=handle_choice(e)
	elif tag=='closer':
		r+=openBlock('p', 'closer')
		r+=traverse(e)
		r+=closeBlock()
	elif tag=='date': r=handle_date(e)
	elif tag=='div': r=handle_div(e)
	elif tag=='figDesc': 
		#r+=openBlock('p', 'Standard')
		r+=traverse(e)+'<text:line-break/>'
		#r+=closeBlock()
	elif tag=='figure': 
		r+=openBlock('p', 'figure')
		r+=traverse(e)
		r+=closeBlock()
	elif tag=='g':
		r+=handle_g(e)
	elif tag=='gap':
		extent = e.get('extent')
		if extent=='unknown': 
			r='[底本缺...]'
		else:
			# insert U+303F, "〿"
			r='\u303f' * int(extent)
	elif tag=='graphic': r+=handle_graphic(e)
	elif tag=='head': r+=handle_head(e)
	elif tag=='item':
		style='ListItem{}'.format(level['list'])
		r+=openBlock('p', style)
		r+=traverse(e)
		r+=closeBlock()
	elif tag=='l':
		r+=openBlock('p', 'lg')
		r+=traverse(e)
		r+=closeBlock()
	elif tag=='lb':
		globals['lb']=e.get('n')
		print('n:', globals['lb'], file=log)
	elif tag=='list': 
		level['list']+=1
		if level['list']>level['list-max']: level['list-max']=level['list']
		count['list']+=1
		r+=traverse(e)
		level['list']-=1
	elif tag=='milestone':
		if e.get('rend')=='pagebreak':
			r='<text:p text:style-name="page_break"></text:p>'
	elif tag=='name': r=handle_name(e)
	elif tag=='note': r=handle_note(e, css)
	elif tag=='p':
		if 'table' in get_ancestors(e): style='Standard'
		else: style='p'
		r+=openBlock('p', style)
		#r+='&lt;{}>'.format(globals['lb'])
		r+=traverse(e)
		r+=closeBlock()+'\n'
	elif tag=='pb':
		n=e.get('n')
		if n is not None:
			n=n.lstrip('0')
			print('p. ', n, file=log)
			globals['pb']=n
			#globals['pb_buf']=n
			# 在 margin 上顯示頁碼
			s=margin(n)
			if opened['block']=='': globals['page number for margin']=s
			else: 
				r=s
				globals['page number for margin']=''
	elif tag=='persName': r=handle_persName(e)
	elif tag=='placeName': r=handle_placeName(e)
	elif tag=='ptr':
		if css.get('display', '')=='none': return ''
		if globals['mode']=='notes': return ''
		type=e.get('type')
		if type is None or type=='glossary':
			target=handle_text(e.get('target'))
			note_id=target[1:]
			r=create_endnote(note_id)
			'''
			if note_id not in globals['note_ser']:
				globals['note_count']+=1
				globals['note_ser'][note_id]=globals['note_count']
			r=open_char_style('endnote_anchor')
			bookmark='ptr'+globals['lb']+note_id
			r+='<text:bookmark text:name="{}"/>'.format(bookmark)
			if note_id not in globals['note2ptr']: globals['note2ptr'][note_id]=[]
			globals['note2ptr'][note_id].append(bookmark)
			r+='<text:a xlink:type="simple" xlink:href="#note{}">'.format(note_id)
			r+='{}</text:a>'.format(globals['note_ser'][note_id])
			r+=close_char_style()
			'''
	elif tag=='roleName':
		if 'small' in charStyle: 
			style='small'
			r=open_char_style(style)
			r+=traverse(e)
			r+=close_char_style()
		else: 
			# persName 裡面的 roleName 不要底線
			style='roleName'
			r=open_char_style(style)
			r+=traverse(e)
			r+=close_char_style()
	elif tag=='row':
		r='<table:table-row>\n'
		r+=traverse(e)
		r+='</table:table-row>\n'
	elif tag=='seg':
		r = handle_seg(e)
	elif tag=='space':
		r=open_char_style('ming') # 因為 HAN NOM 字型的全形空白很小, 所以要換明體
		if e.get('unit')=='chi_chars':
			r+='　' * int(e.get('quantity'))
		else: r+=' '* int(e.get('quantity'))
		r+=close_char_style()
	elif tag=='supplied':
		s = traverse(e)
		note = '各本無「{}」，編輯者新增。'.format(s)
		r += s + create_footnote(note)
	elif tag=='table': r=handle_table(e)
	else:
		r=traverse(e)
	ancestors.pop()
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

def openBlock(type, style, level=None):
	global globals
	r=''
	if opened['block']!='': r=opened['block'] # 如果有未關閉的 block, 要先 close
	if type=='h': r+='\n'
	r += '<text:{0} text:style-name="{1}"'.format(type,style)
	if level is not None:
		r+=' text:outline-level="{}"'.format(level)
	r+='>'
	if globals['page number for margin']!='':
		r+=globals['page number for margin']
		globals['page number for margin']=''
	opened['block']='</text:{}>'.format(type)
	return r

def closeBlock():
	r=''
	if opened['block']!='': 
		r+=opened['block']
		opened['block']=''
	return r

def write_string(text, style_name=None):
	r=''
	if style_name is not None:
		r+='<text:span text:style-name="{}">'.format(style_name)
	r+=text
	if style_name is not None:
		r+='</text:span>'
	return r

def open_char_style(style):
	r=''
	if len(charStyle)>0:
		r+='</text:span>'
		if charStyle[-1] in ('persName', 'persNameSmall'): # 如果人名尚未結束
			if 'persName' not in style:
				# 內文上標, 需要一個把底線拉在下面的 space
				r += '<text:span text:style-name="underline_space"> </text:span>'
	charStyle.append(style)
	if style in ('dynasty', 'persName', 'persNameSmall'):
		# 內文上標, 需要一個把底線拉在下面的 space
		r += '<text:span text:style-name="underline_space"> </text:span>'
	r+='<text:span text:style-name="{}">'.format(style)
	return r

def close_char_style():
	r ='</text:span>'
	style = charStyle.pop()
	if style in ('dynasty', 'persName', 'persNameSmall'):
		# 內文上標, 需要一個把底線拉在下面的 space
		r += '<text:span text:style-name="underline_space"> </text:span>'
		# 兩個名稱中間的底線要斷開
		r+='<text:span text:style-name="underline_separator">　</text:span>'
	
	if len(charStyle)>0:
		style=charStyle[-1]
		r+='<text:span text:style-name="{}">'.format(style)
	return r
	
def span(style, text):
	''' 回傳一個 <text:span>....</text:span>, 樣式是 style, 內容是 text '''
	r = open_char_style(style)
	r += text
	r += close_char_style()
	return r

def out(s):
	writer.fo.write(s)

def writePersonIndex():
	out('''<text:user-index text:style-name="{}" text:name="personNameIndex1">
        <text:user-index-source text:use-index-marks="true" text:index-name="personNameIndex">
          <text:index-title-template text:style-name="User_20_Index_20_Heading">人名索引</text:index-title-template>
          <text:user-index-entry-template text:outline-level="1"
            text:style-name="User_20_Index_20_1">
            <text:index-entry-text/>
            <text:index-entry-tab-stop style:type="right" style:leader-char="."/>
            <text:index-entry-page-number/>
          </text:user-index-entry-template>
          <text:user-index-entry-template text:outline-level="2"
            text:style-name="User_20_Index_20_2">
            <text:index-entry-text/>
            <text:index-entry-tab-stop style:type="right" style:leader-char="."/>
            <text:index-entry-page-number/>
          </text:user-index-entry-template>
          <text:user-index-entry-template text:outline-level="3"
            text:style-name="User_20_Index_20_3">
            <text:index-entry-text/>
            <text:index-entry-tab-stop style:type="right" style:leader-char="."/>
            <text:index-entry-page-number/>
          </text:user-index-entry-template>
          <text:user-index-entry-template text:outline-level="4"
            text:style-name="User_20_Index_20_4">
            <text:index-entry-text/>
            <text:index-entry-tab-stop style:type="right" style:leader-char="."/>
            <text:index-entry-page-number/>
          </text:user-index-entry-template>
          <text:user-index-entry-template text:outline-level="5"
            text:style-name="User_20_Index_20_5">
            <text:index-entry-text/>
            <text:index-entry-tab-stop style:type="right" style:leader-char="."/>
            <text:index-entry-page-number/>
          </text:user-index-entry-template>
          <text:user-index-entry-template text:outline-level="6"
            text:style-name="User_20_Index_20_6">
            <text:index-entry-text/>
            <text:index-entry-tab-stop style:type="right" style:leader-char="."/>
            <text:index-entry-page-number/>
          </text:user-index-entry-template>
          <text:user-index-entry-template text:outline-level="7"
            text:style-name="User_20_Index_20_7">
            <text:index-entry-text/>
            <text:index-entry-tab-stop style:type="right" style:leader-char="."/>
            <text:index-entry-page-number/>
          </text:user-index-entry-template>
          <text:user-index-entry-template text:outline-level="8"
            text:style-name="User_20_Index_20_8">
            <text:index-entry-text/>
            <text:index-entry-tab-stop style:type="right" style:leader-char="."/>
            <text:index-entry-page-number/>
          </text:user-index-entry-template>
          <text:user-index-entry-template text:outline-level="9"
            text:style-name="User_20_Index_20_9">
            <text:index-entry-text/>
            <text:index-entry-tab-stop style:type="right" style:leader-char="."/>
            <text:index-entry-page-number/>
          </text:user-index-entry-template>
          <text:user-index-entry-template text:outline-level="10"
            text:style-name="User_20_Index_20_10">
            <text:index-entry-text/>
            <text:index-entry-tab-stop style:type="right" style:leader-char="."/>
            <text:index-entry-page-number/>
          </text:user-index-entry-template>
        </text:user-index-source>
        <text:index-body>
          <text:index-title text:style-name="Sect1" text:name="personNameIndex1_Head">
            <text:p text:style-name="User_20_Index_20_Heading">人名索引</text:p>
          </text:index-title>
        </text:index-body>
      </text:user-index>'''.format(section_index))

def writePlaceIndex():
	out('''<text:user-index text:style-name="{}" text:name="placeNameIndex1">
        <text:user-index-source text:use-index-marks="true" text:index-name="placeNameIndex">
          <text:index-title-template text:style-name="User_20_Index_20_Heading">地名索引</text:index-title-template>
          <text:user-index-entry-template text:outline-level="1"
            text:style-name="User_20_Index_20_1">
            <text:index-entry-text/>
            <text:index-entry-tab-stop style:type="right" style:leader-char="."/>
            <text:index-entry-page-number/>
          </text:user-index-entry-template>
          <text:user-index-entry-template text:outline-level="2"
            text:style-name="User_20_Index_20_2">
            <text:index-entry-text/>
            <text:index-entry-tab-stop style:type="right" style:leader-char="."/>
            <text:index-entry-page-number/>
          </text:user-index-entry-template>
          <text:user-index-entry-template text:outline-level="3"
            text:style-name="User_20_Index_20_3">
            <text:index-entry-text/>
            <text:index-entry-tab-stop style:type="right" style:leader-char="."/>
            <text:index-entry-page-number/>
          </text:user-index-entry-template>
          <text:user-index-entry-template text:outline-level="4"
            text:style-name="User_20_Index_20_4">
            <text:index-entry-text/>
            <text:index-entry-tab-stop style:type="right" style:leader-char="."/>
            <text:index-entry-page-number/>
          </text:user-index-entry-template>
          <text:user-index-entry-template text:outline-level="5"
            text:style-name="User_20_Index_20_5">
            <text:index-entry-text/>
            <text:index-entry-tab-stop style:type="right" style:leader-char="."/>
            <text:index-entry-page-number/>
          </text:user-index-entry-template>
          <text:user-index-entry-template text:outline-level="6"
            text:style-name="User_20_Index_20_6">
            <text:index-entry-text/>
            <text:index-entry-tab-stop style:type="right" style:leader-char="."/>
            <text:index-entry-page-number/>
          </text:user-index-entry-template>
          <text:user-index-entry-template text:outline-level="7"
            text:style-name="User_20_Index_20_7">
            <text:index-entry-text/>
            <text:index-entry-tab-stop style:type="right" style:leader-char="."/>
            <text:index-entry-page-number/>
          </text:user-index-entry-template>
          <text:user-index-entry-template text:outline-level="8"
            text:style-name="User_20_Index_20_8">
            <text:index-entry-text/>
            <text:index-entry-tab-stop style:type="right" style:leader-char="."/>
            <text:index-entry-page-number/>
          </text:user-index-entry-template>
          <text:user-index-entry-template text:outline-level="9"
            text:style-name="User_20_Index_20_9">
            <text:index-entry-text/>
            <text:index-entry-tab-stop style:type="right" style:leader-char="."/>
            <text:index-entry-page-number/>
          </text:user-index-entry-template>
          <text:user-index-entry-template text:outline-level="10"
            text:style-name="User_20_Index_20_10">
            <text:index-entry-text/>
            <text:index-entry-tab-stop style:type="right" style:leader-char="."/>
            <text:index-entry-page-number/>
          </text:user-index-entry-template>
        </text:user-index-source>
        <text:index-body>
          <text:index-title text:style-name="Sect1" text:name="placeNameIndex1_Head">
            <text:p text:style-name="User_20_Index_20_Heading">地名索引</text:p>
          </text:index-title>
        </text:index-body>
      </text:user-index>'''.format(section_index))

def write_toc():
	out('''<text:table-of-content text:style-name="Sect1" text:protected="true" text:name="內容目錄1">
        <text:table-of-content-source text:outline-level="3">
          <text:index-title-template text:style-name="Contents_20_Heading">內容目錄</text:index-title-template>
          <text:table-of-content-entry-template text:outline-level="1"
            text:style-name="Contents_20_1">
            <text:index-entry-chapter/>
            <text:index-entry-text/>
            <text:index-entry-tab-stop style:type="right" style:leader-char="."/>
            <text:index-entry-page-number/>
          </text:table-of-content-entry-template>
          <text:table-of-content-entry-template text:outline-level="2"
            text:style-name="Contents_20_2">
            <text:index-entry-chapter/>
            <text:index-entry-text/>
            <text:index-entry-tab-stop style:type="right" style:leader-char="."/>
            <text:index-entry-page-number/>
          </text:table-of-content-entry-template>
          <text:table-of-content-entry-template text:outline-level="3"
            text:style-name="Contents_20_3">
            <text:index-entry-chapter/>
            <text:index-entry-text/>
            <text:index-entry-tab-stop style:type="right" style:leader-char="."/>
            <text:index-entry-page-number/>
          </text:table-of-content-entry-template>
        </text:table-of-content-source>
        <text:index-body>
          <text:index-title text:style-name="Sect2" text:name="內容目錄1_Head">
            <text:p text:style-name="Contents_20_Heading">內容目錄</text:p>
          </text:index-title>
        </text:index-body>
      </text:table-of-content>''')
	#<text:p text:style-name="page_break"></text:p>

def readApps(tei):
	global appsContent, appId2Ser
	globals['mode']='notes'
	back = tei.find('.//back')
	appsContent=collections.OrderedDict()
	appId2Ser={}
	r={}
	count=0
	for n in back.iter('app'):
		appId=n.get('from')[3:]
		s=''
		lem=n.find('lem')
		#s+=lem.get('wit')
		if lem is None:
			print('832 app 無 lem', appId)
			sys.exit()
		s+=icon(lem.get('wit'))+' '
		#s+=lem.get('wit')
		s+=handle_node(lem)
		
		# rdg 內容相同的, 合併為一個 rdg
		rdgs=collections.OrderedDict()
		for c in n.iterchildren('rdg'):
			wit=c.get('wit')
			rdg=handle_node(c)
			if rdg in rdgs: rdgs[rdg]+=wit
			else: rdgs[rdg]=wit
			
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

def readNotes(tree):
	global globals
	globals['mode']='notes'
	back = tei.find('.//back')
	r={}
	for n in back.iter('note'):
		id=n.get('id')
		if id is not None:
			r[id]=traverse(n)
	globals['mode']=''
	return r

def read_names(tree, tag):
	global name_keys_len2
	name_len1 = set()
	for n in tree.iter(tag):
		k = n.get('key')
		if (k is None) or (k=='unknown') or (k==''):
			continue
		name = get_text(n)
		if len(name) > 1:
			name_keys_len2.add(k)

if __name__ == '__main__':
	usage = "usage: %prog [options]"
	parser = OptionParser(usage)
	parser.add_option("-z", action="store", type="string", dest="zhuang", help="某個傳的id")
	parser.add_option("-j", action="store", type="string", dest="juan", help="只輸出某一卷")
	parser.add_option("-b", action="store", type="int", dest="juan_begin", help="起始卷數")
	parser.add_option("-e", action="store", type="int", dest="juan_end", help="起始卷數")
	(options, args) = parser.parse_args()
	
	print('load placeAuthority.pickle')
	with open('placeAuthority.pickle', 'rb') as f:
		placeInfo = pickle.load(f)

	xml_file = os.path.join(teiBase, 'wrapper-song.xml')
	print(xml_file)
	tei = etree.parse(xml_file)
	tei.xinclude()
	#tei = tei.getroot()
	tei = sw_xml.stripNamespaces(tei)
	
	writer=zbx_odt.odtWriter('odt-template',odtTemp)
	write_toc()
	
	log=open(logFilename, mode='w', encoding='utf8')
	error_log=open('x2odt-error.log', mode='w', encoding='utf8')
	
	notes=readNotes(tei)
	apps=readApps(tei)
	
	# 把人名、地名 長度在2個字(含)以上的 先找出來
	name_keys_len2 = set()
	read_names(tei, 'persName')
	read_names(tei, 'placeName')
	
	content=''
	body = tei.find('.//body')
	for n in body.iterchildren():
		content+=handle_node(n)
	content+=closeBlock()
	
	# 如果底線之後不是底線, 就不必區隔
	content = re.sub('<text:span text:style-name="underline_separator">　</text:span>([^<])', r'\1', content)
	
	writer.fo.write(content)
	content=''
	
	'''out('<text:h text:style-name="Heading_20_1" text:outline-level="1">校勘</text:h>\n')
	out('<text:h text:style-name="Heading_20_2" text:outline-level="2">校勘</text:h>\n')
	out('<text:h text:style-name="Heading_20_4" text:outline-level="4">校勘</text:h>\n')
	content=''
	for k in appsContent:
		content+=openBlock('p', 'ListItem1')
		content+='[{}]'.format(appsContent[k]) + k
		content+=closeBlock()
	writer.fo.write(content)'''
	
	'''print('處理 glossary', file=log)
	divs=tei.xpath('//back/div[@type="glossary"]')
	content=traverse(divs[0])
	out('<text:h text:style-name="Heading_20_1" text:outline-level="1">詞彙表</text:h>\n')
	out('<text:h text:style-name="Heading_20_2" text:outline-level="2">詞彙表</text:h>\n')
	out('<text:h text:style-name="Heading_20_4" text:outline-level="4">詞彙表</text:h>\n')
	writer.fo.write(content)
	'''

	'''
	print('處理 endnote')
	content=''
	for id in globals['note_ser']:
		n=tei.xpath('//note[@id="{}"]'.format(id))
		if len(n)==0:
			print('933 找不到 note', id)
			sys.exit()
		content+=handle_node(n[0])
	'''
	out('<text:h text:style-name="Heading_20_1" text:outline-level="1">註解</text:h>\n')
	out('<text:h text:style-name="Heading_20_2" text:outline-level="2">註解</text:h>\n')
	out('<text:h text:style-name="Heading_20_4" text:outline-level="4">註解</text:h>\n')
	out(globals['endnotes'])

	writePlaceIndex()
	writePersonIndex()

	#out('<text:h text:style-name="Heading_20_1a" text:outline-level="1">註解</text:h>\n')
	#out('<text:h text:style-name="Heading_20_2" text:outline-level="2">註解</text:h>\n')

	fn_out=os.path.join(folder_out, 'sgsz-phase1.odt')
	writer.save(fn_out)
	
	print('max list level:', level['list-max'])
	print('max div level:', level['div-max'])
	print('graphic count: {}'.format(count['graphic']))