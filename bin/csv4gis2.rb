require 'cgi'
require 'csv'
require 'fileutils'
require 'json'
require 'nokogiri'
require 'set'

IN = '..'
OUT = '../output/csv4gis'

SOURCES = {
  'Buxu_GSZ' => 'Buxu Gaoseng Zhuan 補續高僧傳, by Minghe 明河, dated 1640',
  'Liang_GSZ' => 'Liang gaoseng zhuan 梁高僧傳, by Huijiao 慧皎, dated 519',
  'Ming_GSZ' => 'Ming gaoseng zhuan 明高僧傳, by the monk Ruxing 如惺, dated 1600',
  'Song_GSZ' => 'Song gaoseng zhuan 宋高僧傳, by 贊寧 (919-1001), dated 988',
  'Tang_GSZ' => 'Tang gaoseng zhuan 唐高僧傳, by Daoxuan 道宣 (596-667), dated 665',
  'biQiuNi' => 'Biqiuni  Zhuan 比丘尼傳, by Baocheng 寶唱, dated 516',
  'Mingsengzhuanchao' => 'Mingseng zhuan chao 名僧傳抄, dated 514',
  'chuSanZangJiJi' => 'Chu sanzang jiji 出三藏記集, dated about 500',
  'Jushi_Zhuan' => 'Jushi Zhuan 居士傳（卷1-29）, dated 18th century'
}

def convert_file(fn, dest)
  $serno = 0
  doc = open_xml(fn)
  read_text(doc)

  node = doc.at_xpath('//anchor')
  unless node.nil?
    if node.key? 'n'
      a = node['n'].split('.') # T.50.2063.0935c01
      $work = a[0] + a[1] + 'n' + a[2]
    else
      abort "#{fn} anchor 沒有 n"
    end
  end

  node = doc.at_xpath('//persName')
  return if node.nil?
  if node.key? 'key'
    $subject = node['key']
  else
    abort "#{fn} 第一個 persName 沒有 key"
  end

  basename = File.basename(fn, '.xml')
  dest_f = File.join(dest, "#{basename}.csv")
  CSV.open(dest_f, "wb") do |csv|
    csv << %w(id 地名 x y text)
    doc.xpath("//linkGrp").each do |e|
      e_linkGrp(e, csv)
    end
  end
end

def convert_folder(folder)
  $source_id = folder
  print folder + ' '
  folder_path = File.join(IN, folder)
  target = File.join(OUT, folder)
  unless File.directory?(target)
    FileUtils.mkdir_p(target)
  end

  Dir.entries(folder_path).each do |f|
    next unless f.end_with? '.xml'
    f_path = File.join(folder_path, f)
    convert_file(f_path, target)
  end
end

def e_g(e)
  # <g ref="#F6FAA6"/>
  '{' + e['ref'][1..-1] + '}'
end

def e_lb(e)
  n = e['n']
  "<lb #{n}>"
end

def e_linkGrp(e, csv)
  place = e.at_xpath('ptr[@type="place"]')
  return if place.nil?
  return if place['target'].include? 'unknown'

  place_id = place['target'].sub(/^#(.*)$/, '\1')
  return if place_id.start_with? 'PLG'
  
  place_info = $places[place_id]
  return if place_info.nil?

  text = 'The Person(s) '
  a = []
  $persons = []
  e.xpath('ptr[@type="person"]').each do |c|
    s = e_ptr_person(c)
    a << s unless s.nil?
  end
  text += a.join(',')
  text += " was/were in the place #{place_info['name']}<br>"

  text += e_linkGrp_text(e)
  text += "Source: #{SOURCES[$source_id]}<br>"
  text += "CBETA: <a href='http://cbetaonline.dila.edu.tw/#{$linehead}'>#{$linehead}</a>"

  if place_info['long'].nil? or place_info['long'].empty?
    $no_coordinates << place_id
  end

  if $persons.include? $subject # 如果 linkGrp 裡有 傳主
    $serno += 1
    row = [$serno]
  else
    row = [nil]
  end

  row << place_info['name']
  row << place_info['long']
  row << place_info['lat']
  row << text
  csv << row
end

def e_linkGrp_text(e)
  link = e.at_xpath('link')
  a = link['targets'].split
  n1 = a[0].sub(/^#(.*)$/, '\1')
  n2 = a[1].sub(/^#(.*)$/, '\1')
  $linehead = "#{$work}_p#{n1}"

  doc = e.document
  i = $lbs.find_index(n1)
  return '' if i.nil?
  r = ""
  $lbs[i..-1].each do |lb|
    break if lb > n2
    if r.size > 50
      r += '⋯⋯'
      break
    end
    r += $text[lb]
  end
  return '' if r.empty?
  "「#{r}」<br>"
end

def e_ptr_person(e)
  id = e['target'].sub(/^#(.*)$/, '\1')
  $persons << id
  info = $people[id]
  return nil if info.nil?
  info['name']
end

def handle_node(e)
  return '' if e.comment?
  return handle_text(e) if e.text?
  r = case e.name
  when 'linkGrp', 'orig', 'sic' then ''
  when 'g'  then e_g(e)
  when 'lb' then e_lb(e)
  else traverse(e)
  end
  r
end

def handle_text(e)
  s = e.content().chomp
  return '' if s.empty?

  case e.parent.name
  when 'app'
    return ''
  when 'div'
    return '' if s.gsub(/\s/, '').empty?
  end

  # cbeta xml 文字之間會有多餘的換行
  s.gsub!(/[\n\r]/, '')
  
  # 把 & 轉為 &amp;
  r = CGI.escapeHTML(s)

  r
end

def open_xml(fn)
  doc = File.open(fn) { |f| Nokogiri::XML(f) }
  doc.remove_namespaces!
  doc
end

def read_authority_from_json_file(type)
  fn = File.join(OUT, "#{type}.json")
  puts "read #{fn}"
  s = File.read(fn)
  JSON.parse(s)
end

def read_text(doc)
  text = traverse(doc.root)
  $lbs = []
  $text = {}
  a = text.split(/(<lb [^>]*?>)/)
  lb = nil
  a.each do |s|
    if s.match(/^<lb ([^>]*?)>$/)
      lb = $1
      $lbs << lb
    else
      unless lb.nil? or s.empty?
        $text[lb] = s
      end
    end
  end
end

def traverse(e)
  r = ''
  e.children.each { |c| 
    s = handle_node(c)
    r += s
  }
  r
end

# main
$errors = ''
$no_coordinates = Set.new
$places = read_authority_from_json_file('place')
$people = read_authority_from_json_file('person')

# 2019-02-14 伯雍說《新續高僧傳》Xinxu_GSZ 先不做
folders = %w(Buxu_GSZ Jushi_Zhuan Liang_GSZ Ming_GSZ Mingsengzhuanchao Song_GSZ Tang_GSZ biQiuNi chuSanZangJiJi)
folders.each do |f|
  convert_folder(f)
end

puts "\n產生資料放在 #{OUT}"

unless $no_coordinates.empty?
  fn = 'csv4gis2.log'
  puts "有錯誤，請查看 #{fn}"
  File.open(fn, 'w') do |f|
    f.puts "以下缺座標："
    $no_coordinates.each do |id|
      f.puts id
    end
  end
end