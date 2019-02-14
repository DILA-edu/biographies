require 'csv'
require 'fileutils'
require 'json'
require 'nokogiri'
require 'net/http'
require 'set'

API = 'http://authority.dila.edu.tw/webwidget/getAuthorityData.php'
IN = '..'
OUT = '../output/csv4gis'

def read_file(fn)
  $serno = 0
  doc = open_xml(fn)

  doc.xpath("//linkGrp").each do |e|
    e_linkGrp(e)
  end
end

def read_folder(folder)
  print folder + ' '
  folder_path = File.join(IN, folder)

  Dir.entries(folder_path).each do |f|
    next unless f.end_with? '.xml'
    f_path = File.join(folder_path, f)
    read_file(f_path)
  end
end

def e_linkGrp(e)
  place = e.at_xpath('ptr[@type="place"]')
  return if place.nil?
  return if place['target'].include? 'unknown'

  id = place['target'].sub(/^#(.*)$/, '\1')
  return if id.start_with? 'PLG'
  
  $place_keys << id

  e.xpath('ptr[@type="person"]').each do |c|
    id = c['target'].sub(/^#(.*)$/, '\1')
    $person_keys << id
  end
end

def log_errors(type, keys)
  unless keys.empty?
    puts "#{keys.size}筆 #{type} keys 在 authority 找不到"
  end
  keys.each do |k|
    $errors << "#{k} 在 authority 找不到\n"
  end
end

def open_xml(fn)
  doc = File.open(fn) { |f| Nokogiri::XML(f) }
  doc.remove_namespaces!
  doc
end

def read_authority(type, id)
  params = { type: type, id: id}
  url = "#{API}?type=#{type}&id=#{id}"
  uri = URI(url)
  response = Net::HTTP.get(uri)
  r = JSON.parse(response)
  unless r.nil?
    r = r['data1']
  end
  r
end

def read_authority_keys(type, keys)
  r = {}
  (1..3).each do |i|
    puts "Loop #{i}"
    a = keys.to_a
    a.sort.each do |k|
      print " #{i} #{k} "
      h = read_authority(type, k)
      unless h.nil?
        r[k] = h
        keys.delete(k)
      end
    end
  end
  r
end

def save_authority(type, data)
  fn = File.join(OUT, "#{type}.json")
  s = JSON.pretty_generate(data)
  puts "write #{fn}"
  File.write(fn, s)
end

# main

$place_keys = Set.new
$person_keys = Set.new

puts "read xml"
folders = %w(Buxu_GSZ Jushi_Zhuan Liang_GSZ Ming_GSZ Mingsengzhuanchao Song_GSZ Tang_GSZ Xinxu_GSZ biQiuNi chuSanZangJiJi)
folders.each do |f|
  read_folder(f)
end

count_place = $place_keys.size
count_person = $person_keys.size

$errors = ''

r = read_authority_keys('person', $person_keys)
save_authority('person', r)

r= read_authority_keys('place', $place_keys)
save_authority('place', r)

puts "#{count_place} unique place keys"
puts "#{count_person} unique person keys"

log_errors('place', $place_keys)
log_errors('person', $person_keys)

unless $errors.empty?
  fn = 'csv4gis1.log'
  puts "有錯誤，請查看 #{fn}"
  File.write(fn, $errors)
end
