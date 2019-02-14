#-*- coding:utf-8 -*-
''' 產生 OpenOffice ODT檔
環境: Windows 7, Python 3
'''
import os,shutil,string,zipfile

def zip_folder(z, folder_in, arc_name):
	print(folder_in, arc_name)
	l=os.listdir(folder_in)
	for s in l:
		p = folder_in + '/' + s
		if os.path.isdir(p): zip_folder(z, p, arc_name+'/'+s)
		else: z.write(p, arc_name+'/'+s)

def packODT(source, target):
	''' zip ODT folder to ODT file '''
	z=zipfile.ZipFile(target, 'w')
	z.write(source+'/mimetype', 'mimetype')
	z.write(source+'/content.xml', 'content.xml')
	z.write(source+'/manifest.rdf', 'manifest.rdf')
	z.write(source+'/meta.xml', 'meta.xml')
	z.write(source+'/settings.xml', 'settings.xml')
	z.write(source+'/styles.xml', 'styles.xml')
	z.write(source+'/META-INF/manifest.xml', 'META-INF/manifest.xml')
	if os.path.exists(source+'/Pictures'):
		zip_folder(z, source+'/Pictures', 'Pictures')
	z.close()

class odtWriter():
	def __init__(self, templateFolder, odtFolder):
		self.templateFolder=templateFolder
		self.odtFolder=odtFolder
		if os.path.exists(odtFolder): shutil.rmtree(odtFolder)
		shutil.copytree(templateFolder, odtFolder)
		self.fo=open(odtFolder+'/content.xml', 'a', encoding='utf8')
		self.config={
			'pageWidth' : "14.801cm",
			'pageHeight' : "21.001cm",
			'marginTop' : "2cm",
			'marginBottom' : "1.401cm",
			'marginLeft' : "2.499cm",
			'marginRight' : "2.499cm"
		}
	def save(self, fn):
		self.fo.write('</office:text></office:body></office:document-content>')
		self.fo.close()
		with open(self.odtFolder+'/styles.xml', 'r', encoding='utf8') as fi:
			s=fi.read()
		with open(self.odtFolder+'/styles.xml', 'w', encoding='utf8') as f:
			f.write(string.Template(s).substitute(self.config))
		packODT(self.odtFolder, fn)
