# 在兩個地名或人名之間插入空白, 以斷開底線
# 標題裡面不必加

require 'nokogiri'

BASE = '../output/indesign'
IN = File.join(BASE, 'sgsz2.xml')
OUT = File.join(BASE, 'sgsz.xml')

def check_prev_node(e)
  prev = e.previous
  return if prev.nil?
  r = case prev.name
  when 'persName', 'placeName'
    insert_sep(e)
  when 'span'
    insert_sep(e) if prev['rend'] == 'name'
  end
end

def e_p(e)
  # 標題裡的不處理
  return if e.key?('rend') and e['rend'].match(/^h\d+$/)
  traverse(e)
end

def e_span(e)
  check_prev_node(e) if e['rend'] == 'name'
  traverse(e)
end

def handle_node(e)
  return if e.comment?
  return if e.text?

  case e.name
  when 'p'         then e_p(e)
  when 'persName'  then check_prev_node(e)
  when 'placeName' then check_prev_node(e)
  when 'span'      then e_span(e)
  else traverse(e)
  end
end

def insert_sep(e)
  span = Nokogiri::XML::Node.new "span", $doc
  span['rend'] = "underline_separator"
  span.content = " "
  e.add_previous_sibling(span)
end

def traverse(e, mode='html')
  e.children.each { |c| 
    handle_node(c)
  }
end

puts "read #{IN}"
$doc = File.open(IN) { |f| Nokogiri::XML(f) }
traverse($doc.root)
puts "write #{OUT}"
f = File.open(OUT, 'w:BOM|UTF-8')
f.write "\uFEFF"
f.write $doc.to_xhtml(encoding: 'UTF-8')