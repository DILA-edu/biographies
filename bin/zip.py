#-*- coding:utf-8 -*-

import datetime, glob, os, re, zipfile

folder_out='../output/zip/'

config={
  'buxu': {
    'folder': 'Buxu_GSZ',
    'title': 'Buxu Gaoseng Zhuan 補續高僧傳, by Minghe 明河, dated 1640',
    'cbeta': 'CD 2010',
    'zip': 'buxu-gaoseng-zhuan',
    'wrapper': 'wrapper-buxu'
  },
  'liang': {
    'folder': 'Liang_GSZ',
    'title': 'Liang gaoseng zhuan 梁高僧傳, by Huijiao 慧皎, dated 519',
    'cbeta': 'CD 2008',
    'zip': 'liang-gaoseng-zhuan',
    'wrapper': 'wrapper-liang'
  },
  'ming': {
    'folder': 'Ming_GSZ',
    'title': 'Ming gaoseng zhuan 明高僧傳, by the monk Ruxing 如惺, dated 1600',
    'cbeta': 'CD 2009',
    'zip': 'ming-gaoseng-zhuan',
    'wrapper': 'wrapper-ming'
  },
  'song': {
    'folder': 'Song_GSZ',
    'title': 'Song gaoseng zhuan 宋高僧傳, by 贊寧 (919-1001), dated 988',
    'cbeta': 'CD 2008, CD 2009',
    'zip': 'song-gaoseng-zhuan',
    'wrapper': 'wrapper-song'
  },
  'tang': {
    'folder': 'Tang_GSZ',
    'title': 'Tang gaoseng zhuan 唐高僧傳, by Daoxuan 道宣 (596-667), dated 665',
    'cbeta': 'CD 2008',
    'zip': 'tang-gaoseng-zhuan',
    'wrapper': 'wrapper-tang'
  },
  'biqiuni': {
    'folder': 'biQiuNi',
    'title': 'Biqiuni  Zhuan 比丘尼傳, by Baocheng 寶唱, dated 516',
    'cbeta': 'CD 2009',
    'zip': 'biqiuni-zhuan',
    'wrapper': 'wrapper-biqiuni'
  },
  'mscc': {
    'folder': 'Mingsengzhuanchao',
    'title': 'Mingseng zhuan chao 名僧傳抄, dated 514',
    'cbeta': 'CD 2009',
    'zip': 'mingseng-zhuan-chao',
    'wrapper': 'MSCCwrapper-Mingsengzhuanchao'
  },
  'cszjj': {
    'folder': 'chuSanZangJiJi',
    'title': 'Chu sanzang jiji 出三藏記集, dated about 500',
    'cbeta': 'CD 2010',
    'zip': 'chu-sanzang-jiji',
    'wrapper': 'wrapper-chuSanZangJiJi'
  },
  'Jushi_Zhuan': {
    'folder': 'Jushi_Zhuan',
    'title': 'Jushi Zhuan 居士傳（卷1-29）, dated 18th century',
    'cbeta': 'CD 2010',
    'zip': 'Jushi_(1-29)',
    'wrapper': 'JSZwrapper-JuShiZhuan'
  }
}

if not os.path.exists(folder_out):
  os.makedirs(folder_out)

fi=open('readme_template.txt','r',encoding='utf8')
readme_template=fi.read()
for gid in config:
  print(gid)
  
  config[gid]['date']=datetime.datetime.now().strftime('%d-%m-%Y')
  config[gid]['date']=datetime.datetime.now().strftime('%Y-%m-%d')
  readme=readme_template % config[gid]
  fo=open(folder_out+'readme.txt','w',encoding='utf8')
  fo.write(readme)
  fo.close()
  
  wrapper_xml=config[gid]['wrapper']+'.xml'
  wrapper=os.path.join('..',config[gid]['folder'],wrapper_xml)
  with open(wrapper,'r',encoding='utf8') as fi:
    s=fi.read()
  s=re.sub('<\?oxygen .*?>', '', s)
  wrapper_path=os.path.join(folder_out,wrapper_xml)
  with open(wrapper_path, 'w', encoding='utf8') as fo:
    fo.write(s)
  
  zip_name = config[gid]['zip']
  z=zipfile.ZipFile(folder_out+zip_name+'.zip', 'w')
  folder_in='../'+config[gid]['folder']
  files=os.listdir(folder_in)
  rncIncluded=False
  for s in files:
    if s==wrapper_xml:
      z.write(wrapper_path, zip_name+'/'+s)
    elif s.endswith('.xml'):
      z.write(folder_in+'/'+s, zip_name+'/'+s)
    elif s.endswith('.rnc'):
      z.write(folder_in+'/'+s, zip_name+'/'+s)
      rncIncluded=True
  z.write(folder_out+'readme.txt', zip_name+'/readme.txt')
  if not rncIncluded:
    z.write('../Schema/gisSchema.rnc', zip_name+'/gisSchema.rnc')
  folder_in = os.path.join(folder_in, 'gaiji')
  if os.path.exists(folder_in):
    files=os.listdir(folder_in)
    for s in files:
      z.write(folder_in+'/'+s, zip_name+'/gaiji/'+s)
  z.close()
#-*- coding:utf-8 -*-

import datetime, glob, os, re, zipfile

folder_out='../output/zip/'

config={
  'buxu': {
    'folder': 'Buxu_GSZ',
    'title': 'Buxu Gaoseng Zhuan 補續高僧傳, by Minghe 明河, dated 1640',
    'cbeta': 'CD 2010',
    'zip': 'buxu-gaoseng-zhuan',
    'wrapper': 'wrapper-buxu'
  },
  'liang': {
    'folder': 'Liang_GSZ',
    'title': 'Liang gaoseng zhuan 梁高僧傳, by Huijiao 慧皎, dated 519',
    'cbeta': 'CD 2008',
    'zip': 'liang-gaoseng-zhuan',
    'wrapper': 'wrapper-liang'
  },
  'ming': {
    'folder': 'Ming_GSZ',
    'title': 'Ming gaoseng zhuan 明高僧傳, by the monk Ruxing 如惺, dated 1600',
    'cbeta': 'CD 2009',
    'zip': 'ming-gaoseng-zhuan',
    'wrapper': 'wrapper-ming'
  },
  'song': {
    'folder': 'Song_GSZ',
    'title': 'Song gaoseng zhuan 宋高僧傳, by 贊寧 (919-1001), dated 988',
    'cbeta': 'CD 2008, CD 2009',
    'zip': 'song-gaoseng-zhuan',
    'wrapper': 'wrapper-song'
  },
  'tang': {
    'folder': 'Tang_GSZ',
    'title': 'Tang gaoseng zhuan 唐高僧傳, by Daoxuan 道宣 (596-667), dated 665',
    'cbeta': 'CD 2008',
    'zip': 'tang-gaoseng-zhuan',
    'wrapper': 'wrapper-tang'
  },
  'biqiuni': {
    'folder': 'biQiuNi',
    'title': 'Biqiuni  Zhuan 比丘尼傳, by Baocheng 寶唱, dated 516',
    'cbeta': 'CD 2009',
    'zip': 'biqiuni-zhuan',
    'wrapper': 'wrapper-biqiuni'
  },
  'mscc': {
    'folder': 'Mingsengzhuanchao',
    'title': 'Mingseng zhuan chao 名僧傳抄',
    'cbeta': 'CD 2009',
    'zip': 'mingseng-zhuan-chao',
    'wrapper': 'MSCCwrapper-Mingsengzhuanchao'
  },
  'cszjj': {
    'folder': 'chuSanZangJiJi',
    'title': 'Chu sanzang jiji 出三藏記集',
    'cbeta': 'CD 2010',
    'zip': 'chu-sanzang-jiji',
    'wrapper': 'wrapper-chuSanZangJiJi'
  },
  'Jushi_Zhuan': {
    'folder': 'Jushi_Zhuan',
    'title': 'Jushi Zhuan 居士傳',
    'cbeta': 'CD 2010',
    'zip': 'Jushi',
    'wrapper': 'JSZwrapper-JuShiZhuan'
  }
}

if not os.path.exists(folder_out):
  os.makedirs(folder_out)

fi=open('readme_template.txt','r',encoding='utf8')
readme_template=fi.read()
for gid in config:
  print(gid)
  
  config[gid]['date']=datetime.datetime.now().strftime('%d-%m-%Y')
  config[gid]['date']=datetime.datetime.now().strftime('%Y-%m-%d')
  readme=readme_template % config[gid]
  fo=open(folder_out+'readme.txt','w',encoding='utf8')
  fo.write(readme)
  fo.close()
  
  wrapper_xml=config[gid]['wrapper']+'.xml'
  wrapper=os.path.join('..',config[gid]['folder'],wrapper_xml)
  with open(wrapper,'r',encoding='utf8') as fi:
    s=fi.read()
  s=re.sub('<\?oxygen .*?>', '', s)
  wrapper_path=os.path.join(folder_out,wrapper_xml)
  with open(wrapper_path, 'w', encoding='utf8') as fo:
    fo.write(s)
  
  zip_name = config[gid]['zip']
  z=zipfile.ZipFile(folder_out+zip_name+'.zip', 'w')
  folder_in='../'+config[gid]['folder']
  files=os.listdir(folder_in)
  rncIncluded=False
  for s in files:
    if s==wrapper_xml:
      z.write(wrapper_path, zip_name+'/'+s)
    elif s.endswith('.xml'):
      z.write(folder_in+'/'+s, zip_name+'/'+s)
    elif s.endswith('.rnc'):
      z.write(folder_in+'/'+s, zip_name+'/'+s)
      rncIncluded=True
  z.write(folder_out+'readme.txt', zip_name+'/readme.txt')
  if not rncIncluded:
    z.write('../Schema/gisSchema.rnc', zip_name+'/gisSchema.rnc')
  folder_in = os.path.join(folder_in, 'gaiji')
  if os.path.exists(folder_in):
    files=os.listdir(folder_in)
    for s in files:
      z.write(folder_in+'/'+s, zip_name+'/gaiji/'+s)
  z.close()
