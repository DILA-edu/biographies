require 'fileutils'
require 'nokogiri'
require_relative 'ray'

include Ray

OUT = '../output/ner'

def e_date(e)
  $time_count += 1
  $status << 'B_Time'
  traverse(e)
  $status.pop
end

def e_g(e)
  id = e['ref'].sub(/^#/, '')  
  output_char("[#{id}]")
end

def e_gap(e)
  return '' if e.parent.name == 'supplied'
  
  extent = e['extent']
  output('□…□') if extent=='unknown'
  
  output('□' * extent.to_i)
end

def e_persName(e)
  if e.parent.name == 'persName'
    return traverse(e)
  end

  $person_count += 1
  $status << 'B_Person'
  traverse(e)
  $status.pop
end

def e_placeName(e)
  if e.parent.name == 'placeName'
    return traverse(e)
  end

  $place_count += 1
  $status << "B_Place"
  traverse(e)
  $status.pop
end

def exist_name_entity_tag?(doc)
  return false if doc.nil?

  body = doc.at_xpath('//body')
  return true if body.at_xpath('.//persName')
  return true if body.at_xpath('.//placeName')
  return true if body.at_xpath('.//date')
  false
end

def handle_book(xml_wrapper)
  doc = open_xml(xml_wrapper)
  return unless exist_name_entity_tag?(doc)

  puts xml_wrapper
  fn = File.join(OUT, "#{$book}.txt")
  $fo = File.open(fn, 'w')
  traverse(doc.root)
  $fo.close

  s = File.read(fn)

  # 如果連續多個空白行，只留下一個空白行
  s.gsub!(/\n{3,}/, "\n\n")

  # 如果空白行在 下引號 之前，將空白行移到 下引號 之後
  s.gsub!(/([。！？])\tO\n\n」\tO\n/, "\\1\tO\n」\tO\n\n")

  File.write(fn, s)
end

def handle_node(e)
  return '' if e.comment?
  return handle_text(e) if e.text?

  case e.name
  when 'facsimile', 'figDesc', 'linkGrp', 'note', 'orig', 'sic', 'teiHeader'
    ''
  when 'byline', 'cell', 'closer', 'div', 'head', 'item', 'l', 'list', 'p', 'table'
    traverse(e)
    $fo.puts
  when 'date'      then e_date(e)
  when 'g'         then e_g(e)
  when 'gap'       then e_gap(e)
  when 'persName'  then e_persName(e)
  when 'placeName' then e_placeName(e)
  else traverse(e)
  end
end

def handle_text(e)
  s = e.content.strip
  output(s)
end

def open_xml(fn)
  puts "read #{fn}"
  folder = File.dirname(fn)
  text = File.read(fn)
  text.scan(/<xi:include href="(.*?.xml)"/) do |f,|
    p = File.join(folder, f)
    puts "#{f} 不存在" unless File.exist?(p)
  end
  doc = File.open(fn) { |f| Nokogiri::XML(f) }
  begin
    doc.do_xinclude
  rescue StandardError => e
    puts "#{fn} 執行 xinclude 失敗"
    puts e.message  
    puts e.backtrace.inspect  
    return nil
  end

  doc.remove_namespaces!
end

def output(s)
  return if s.empty?
  s2a(s).each do |c|
    output_char(c)
  end
end

def output_char(c)
  case $status.last
  when 'B_Person', 'B_Place', 'B_Time'
    $fo.puts c + "\t" + $status.last
    $status[-1] = $status.last.sub(/^B/, 'I')
  when 'I_Person', 'I_Place', 'I_Time'
    $fo.puts c + "\t" + $status.last
  when 'O'
    $fo.puts c + "\tO"
  end
  $fo.puts if '。！？'.include?(c)
  $total += 1
end

# 將字串轉為矩陣，字串之中可能有組字式
def s2a(s)
  s.scan(/\[[^\]]+\]|./)
end

def traverse(e)
  e.children.each { |c| handle_node(c) }
end

FileUtils.makedirs(OUT)
$status = ['O']
$total = 0
$person_count = 0
$place_count = 0
$time_count = 0

Dir['../*'].sort.each do |folder|
  $book = File.basename(folder)
  Dir["#{folder}/*wrapper*"].each do |f|
    handle_book(f)
  end
end

puts "\n總字數: " + n2s($total)
puts "人名: " + n2s($person_count)
puts "地名: " + n2s($place_count)
puts "時間: " + n2s($time_count)