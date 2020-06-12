require 'csv'
require 'nokogiri'

TODO = {
  'Liang_GSZ' => '梁高僧傳',
  'Tang_GSZ' => '唐高僧傳',
  'Song_GSZ' => '宋僧傳',
  'Ming_GSZ' => '明高僧傳'
}
OUT = '../output/biographies.tsv'

def e_div(e)
  return unless e.key? 'type'
  $type = e['type']
  return if %w[apparatus notes frontmatter glossary juan 卷首 卷尾].include? $type
  return if %w[gsz0723a13yiJingPianLun gsz0753a03yiJiePianLun gsz0789b11xiChanPianLun gsz0811a20mingLuPianLun gsz0819b25huFaPianLun gsz0854b08ganTongPianLun gsz0861a12yiShenPianLun gsz0871c27duSongPianLun gsz0888a07xingFuPianLun gsz0899a26zaKeShengDePianLun].include? e['id']

  if e['id'] == 'gsz0425a03sengQiePoLuo'
    $name = '僧伽婆羅'
  else
    node = e.at_xpath('.//persName')
    if node.nil?
      puts "找不到 persName"
      puts "div id: #{e['id']}"
      abort
    end
    $name = node.content.gsub(' ', '')
  end
  traverse(e)
  ''
end

def e_g(e)
  id = e['ref'].sub(/^#/, '')  
  "[#{id}]"
end

def e_gap(e)
  return '' if e.parent.name == 'supplied'
  
  extent = e['extent']
  output('□…□') if extent=='unknown'
  
  output('□' * extent.to_i)
end

def handle_biography(fn)
  puts "read #{fn}"
  doc = File.open(fn) { |f| Nokogiri::XML(f) }
  doc.do_xinclude
  doc.remove_namespaces!
  doc.xpath('//div').each do |e|
    e_div(e)
  end
end

def handle_node(e)
  return '' if e.comment?
  return handle_text(e) if e.text?

  case e.name
  when 'facsimile', 'figDesc', 'linkGrp', 'note', 'orig', 'sic', 'teiHeader'
    ''
  when 'byline', 'cell', 'closer', 'div', 'head', 'item', 'l', 'list', 'p', 'table'
    s = traverse(e)
    $csv << [$title, $type, $name, s]
    ''
  when 'g'         then e_g(e)
  when 'gap'       then e_gap(e)
  else traverse(e)
  end
end

def handle_text(e)
  s = e.content.strip
  s.gsub(/[\n\t ]/, '')
end

def traverse(e)
  r = ''
  e.children.each do |c| 
    r += handle_node(c)
  end
  r
end

$csv = CSV.open(OUT, "wb", col_sep: "\t")
$csv << %w[傳別 分類 高僧 段落內文]
TODO.each_pair do |k, v|
  $bid = k
  $title = v
  fn = Dir["../#{k}/wrapper*.xml"].first
  handle_biography(fn)
end