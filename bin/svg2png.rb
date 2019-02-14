# 把 svg 轉為 png
# 需求
# ubuntu
# sudo apt-get install libmagick++-dev
# sudo gem install rmagick

require 'RMagick'
include Magick

Dir["gaiji-svg/*"].each { |f|
	print f
	g = Image.read(f)
	new = 'gaiji-png/' + File.basename(f).gsub(/\.svg$/, '.png')
	puts ' -> ' + new
	g[0].write(new)
}