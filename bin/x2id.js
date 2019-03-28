#include "/c/Program Files (x86)/Adobe/Adobe InDesign CS6/Scripts/XML Rules/glue code.jsx";
/*
請將本程式及 sgsz.cfg 複製到 InDesign script 所在資料夾 (假設為 [SCRIPT])
然後修改 [SCRIPT]/sgsz.cfg 裡的參數符合自己的電腦環境

Author:: Ray Chou
Date:: 2015.3.20
*/

var config = {};
read_config('sgsz.cfg');

var key_containers = {}; // 人名、地名 所在的 container
var hyper_text_dest_count = 0;
var in_footnote = false;

/*
InDesign 未支援 array.indexOf(), 以下程式片段可提供此功能
*/
if (!Array.prototype.indexOf)
{
  Array.prototype.indexOf = function(elt /*, from*/)
  {
    var len = this.length;

    var from = Number(arguments[1]) || 0;
    from = (from < 0)
         ? Math.ceil(from)
         : Math.floor(from);
    if (from < 0)
      from += len;

    for (; from < len; from++)
    {
      if (from in this &&
          this[from] === elt)
        return from;
    }
    return -1;
  };
}

function read_config(fn) {
  var folder = (new File($.fileName)).parent; // 取得 script 所在路徑
  var file = File(folder+"/"+fn);
  file.open('r');
  var s;
  while (!file.eof) {
    s = file.readln().split('=');
    config[s[0]] = s[1];
  }
}

/*
  取得物件所在頁面
  return: object Page
*/
function find_page (o)
{
  try
    {
    if (o.hasOwnProperty ("parentPage"))
      return o.parentPage;
    if (o.constructor.name == "Page")
      return o;
    switch (o.parent.constructor.name)
      {
      case "Character": return find_page (o.parent);
      case "Cell": return find_page (o.parent.texts[0].parentTextFrames[0]);
      case "Table" : return find_page (o.parent);
      case "TextFrame" : return find_page (o.parent);
      case "Group" : return find_page (o.parent);
      case "Story": return find_page (o.parentTextFrames[0]);
      case "Footnote": return find_page (o.parent.storyOffset);
      case "Page" : return o.parent;
      }
    }
    catch (_) {return ""}
} // find_page

function has_attribute(node, key) {
  var attr = node.xmlAttributes.itemByName(key);
  if (attr != null) {
    return true;
  } else {
    return false;
  }
}

function get_attribute(node, key) {
  var attr = node.xmlAttributes.itemByName(key);
  if (attr != null) {
    return attr.value;
  } else {
    return '';
  }
}

// 根據 key 取得所在頁碼
function get_pages_by_key(k) {
  var pages = [];
  var p;
  var a = key_containers[k]; // 根據 key 取得所在位置 insertion_point
  var j;
  for (i = 0; i < a.length; i++) {  
    //p = a[i].parentTextFrames[0].parentPage.name;
    p = find_page(a[i]);
    j = pages.indexOf(p.name);
    if (j < 0) { // 如果這個 頁數 還沒有出現過
      pages.push(p.name);
    }
  }; 
  return pages.join();
}

function mySetup(){
  doc.viewPreferences.horizontalMeasurementUnits = MeasurementUnits.points;
  doc.viewPreferences.verticalMeasurementUnits = MeasurementUnits.points;
  with(doc.documentPreferences){
    pageHeight = "23cm";
    pageWidth = "17cm";
    pagesPerDocument = parseInt(config['doc_pages']);
  }
}

/* 
每一頁都建一個 text frame, 並在上下頁之間建立連結.
*/
function addTextFrames() {
  var page;
  var prev_text_frame;
  var new_text_frame;
  for (i=0; i<doc.pages.length; i++){
    page = doc.pages.item(i);
    new_text_frame = page.textFrames.add(
      {geometricBounds:myGetBounds(doc, page, i)}
    );
    new_text_frame.name = 'body';
    if (i!=0) {
      new_text_frame.previousTextFrame = prev_text_frame;
    }
    prev_text_frame = new_text_frame;
  }
}

function myGetBounds(doc, myPage, i){
  var myPageWidth = doc.documentPreferences.pageWidth;
  var myPageHeight = doc.documentPreferences.pageHeight
  if ((myPage.side == PageSideOptions.leftHand) || (i==0)) {
    var myX1 = myPage.marginPreferences.left;
    var myX2 = myPageWidth - myPage.marginPreferences.right;
  } else {
    var myX1 = myPage.marginPreferences.right + myPageWidth;
    var myX2 = myPageWidth + myPageWidth - myPage.marginPreferences.left;
  }
  var myY1 = myPage.marginPreferences.top;
  var myY2 = myPageHeight - myPage.marginPreferences.bottom;
  return [myY1, myX1, myY2, myX2];
}
/*
function create_header() {
  var text_var = doc.textVariables.item("h1"); 
  var width = doc.documentPreferences.pageWidth;
  var height = doc.documentPreferences.pageHeight;
  var i;
  var page;
  for (i=0; i<doc.pages.length; i++){
    page = doc.pages.item(i);
    var style = "header-right";
    if ((page.side == PageSideOptions.leftHand) || (i==0)) {
      var myX1 = page.marginPreferences.left;
      var myX2 = width - page.marginPreferences.right;
      if (i!=0) {
        style = "header-left";
      }
    } else {
      var myX1 = page.marginPreferences.right + width;
      var myX2 = width + width - page.marginPreferences.left;
    }
    var myY1 = 20;
    var myY2 = 50;
    var text_frame = page.textFrames.add(
      { geometricBounds: [myY1, myX1, myY2, myX2]}
    );
    text_frame.parentStory.insertionPoints.item(-1).textVariableInstances.add({associatedTextVariable:text_var});
    
    var p_style = doc.paragraphStyles.item(style);
    text_frame.parentStory.paragraphs.item(-1).applyParagraphStyle(p_style, true);
    
    var c_style = doc.characterStyles.item('normal');
    text_frame.paragraphs[-1].applyCharacterStyle(c_style);
  }
}

function create_footer() {
  var text_var = doc.textVariables.item("h1"); 
  var width = doc.documentPreferences.pageWidth;
  var height = doc.documentPreferences.pageHeight;
  var i;
  var page;
  for (i=0; i<doc.pages.length; i++){
    page = doc.pages.item(i);
    var style;
    if ((page.side == PageSideOptions.leftHand) || (i==0)) {
      var myX1 = page.marginPreferences.left;
      var myX2 = width - page.marginPreferences.right;
      if (i==0) {
        style = "footer-right";
      } else {
        style = "footer-left";
      }
    } else {
      var myX1 = page.marginPreferences.right + width;
      var myX2 = width + width - page.marginPreferences.left;
      style = "footer-right";
    }
    var myY1 = 610;
    var myY2 = 640;
    var text_frame = page.textFrames.add(
      { geometricBounds: [myY1, myX1, myY2, myX2]}
    );
    
    text_frame.parentStory.insertionPoints.item(-1).contents = page.name;
    
    var p_style = doc.paragraphStyles.item(style);
    text_frame.parentStory.paragraphs.item(-1).applyParagraphStyle(p_style, true);
    
    var c_style = doc.characterStyles.item('normal');
    text_frame.paragraphs[-1].applyCharacterStyle(c_style);
  }
}
*/
function write(s, parent) {
  if (typeof parent === 'undefined') {
    parent = '';
  }
  var container = my_story.insertionPoints.item(-1);
  if (parent == 'footnote') {
    container = my_story.footnotes.lastItem().insertionPoints.item(-1);
  }
  container.contents = s;
  return container
}

function apply_c_style(style, parent) {
  if (typeof parent === 'undefined') {
    parent = '';
  }
  var c_style = doc.characterStyles.item(style);
  if (c_style==null) {
    log.writeln('p style not exist:' + style);
    alert('char style not exist: ' + style);
  }
  container = my_story.insertionPoints.item(-1);
  if (parent == 'footnote') {
    container = my_story.footnotes.lastItem().insertionPoints.item(-1);
  }
  container.applyCharacterStyle(c_style);
}

function apply_p_style(style) {
  var p_style = doc.paragraphStyles.item(style);
  /*
  if (p_style==null) {
    log.writeln('p style not exist:' + style);
  }
  */
  my_story.paragraphs.item(-1).applyParagraphStyle(p_style, true);
}

function xmlRuleForBack() {
  this.name = "XmlRuleForBack";
  this.xpath = "//back";
  this.apply = function(myElement, myRuleProcessor){
    __processChildren(myRuleProcessor);
    return false;
  }
}

function xmlRuleForBody() {
  this.name = "XmlRuleForBody";
  this.xpath = "//body";
  this.apply = function(myElement, myRuleProcessor){
    __processChildren(myRuleProcessor);
    return false;
  }
}

/* 人名索引頁碼 */
function xmlRuleForIndexPersonPages() {
  this.name = "XmlRuleForIndexPersonPages";
  this.xpath = "//index_person_pages";
  this.apply = function(myElement, myRuleProcessor){
    var k = myElement.xmlAttributes.itemByName('key').value;
    var n = myElement.xmlAttributes.itemByName('name');
    if (n != null) {
      k += n.value;
    }
    if (key_containers.hasOwnProperty(k)) {
      apply_c_style('index-key');
      var s = get_pages_by_key(k);
      write(s);
    }
    return false;
  }
}

function xmlRuleForIndexPlacePages() {
  this.name = "XmlRuleForIndexPlacePages";
  this.xpath = "//index_place_pages";
  this.apply = function(myElement, myRuleProcessor){
    var k = myElement.xmlAttributes.itemByName('key').value;
    var n = myElement.xmlAttributes.itemByName('name');
    if (n != null) {
      k += n.value;
    }
    if (key_containers.hasOwnProperty(k)) {
      apply_c_style('index-key');
      var s = get_pages_by_key(k);
      write(s);
    }
    return false;
  }
}

function xmlRuleForFootnote() {
  this.name = "XmlRuleForFootnote";
  this.xpath = "//footnote";
  this.apply = function(myElement, myRuleProcessor){
    var myFootnote = my_story.insertionPoints.item(-1).footnotes.add();
    
    var attr = myElement.xmlAttributes.itemByName('marker_style');
    if (attr != null) {
      var style = attr.value;
      var c_style = doc.characterStyles.item(style);
      app.findGrepPreferences.findWhat = "(?<=.)~F";
      matches = doc.findGrep();
      matches[matches.length-1].applyCharacterStyle(c_style);
    }
    return false;
  }
}

function xmlRuleForHeader() {
  this.name = "XmlRuleForHeader";
  this.xpath = "//header";
  this.apply = function(myElement, myRuleProcessor){
    write(myElement.contents);
    apply_p_style('text-variable-header');
    write("\r");
    return false;
  }
}

function xmlRuleForImg() {
  this.name = "XmlRuleForImg";
  this.xpath = "//img";
  this.apply = function(myElement, myRuleProcessor){
    var parent = myElement.parent.markupTag.name;
    var width = get_attribute(myElement, 'width');
    var height = get_attribute(myElement, 'height');
    var img_src = get_attribute(myElement, 'src');
    var type = get_attribute(myElement, 'type');
    if (type=='g') {
      img_src = config['gaiji'] + '/' + img_src
    }
    var myInsertionPoint = my_story.insertionPoints.item(-1);
    if (parent == 'footnote') {
      myInsertionPoint = my_story.footnotes.lastItem().insertionPoints.item(-1);
    }
    // var frame = myInsertionPoint.textFrames.add();
    var frame = myInsertionPoint.rectangles.add();
    
    // geometricBounds 跟 visibleBounds 有誤差
    // 請參考 http://www.indiscripts.com/post/2009/10/work-around-the-width-height-gap
    //frame.geometricBounds = [0, 0, height, width];
    frame.visibleBounds = [0, 0, height, width];
    
    with(frame.anchoredObjectSettings){
      anchoredPosition = AnchorPosition.INLINE_POSITION;
    }
    frame.place(File(img_src), false);
    with (frame.frameFittingOptions) {
      autoFit = true;
      topCrop = -40; // 裁切量, 負值表示留空
      bottomCrop = -60;
      leftCrop = -45;
      rightCrop = -45;
      fittingOnEmptyFrame = EmptyFrameFittingOptions.CONTENT_TO_FRAME; // 使內容符合框架大小
    }

    //frame.fit (FitOptions.CONTENT_TO_FRAME);  // the entire image fits inside your frame
    //frame.fit (FitOptions.PROPORTIONALLY);  // scales down proportionally
    //frame.fit (FitOptions.CENTER_CONTENT);
    return false;
  }
}

function xmlRuleForP() {
  this.name = "XmlRuleForP";
  this.xpath = "//p";
  this.apply = function(myElement, myRuleProcessor){
    __processChildren(myRuleProcessor);
    var style = 'p';
    var attr = myElement.xmlAttributes.itemByName('rend');
    if (attr != null) {
      style = attr.value;
    }
    apply_p_style(style);
    write("\r");
    return false;
  }
}

function xmlRuleForP2() {
  this.name = "XmlRuleForP2";
  this.xpath = "//p";
  this.apply = function(myElement, myRuleProcessor){
    __processChildren(myRuleProcessor);
    return false;
  }
}

function xmlRuleForPb() {
  this.name = "XmlRuleForPb";
  this.xpath = "//pb";
  this.apply = function(myElement, myRuleProcessor){
    var myInsertionPoint = my_story.insertionPoints.item(-1);
    var myAnchoredFrame = myInsertionPoint.textFrames.add();
    var myBounds = myAnchoredFrame.geometricBounds;
    //make the frame 14 points tall by 40 points wide.
    var myArray = [myBounds[0], myBounds[1], myBounds[0]+14, myBounds[1]+40];
    myAnchoredFrame.geometricBounds = myArray;
    
    myAnchoredFrame.contents = myElement.xmlAttributes.itemByName('n').value;
    
    // 設段落樣式為 pb
    var p_style = doc.paragraphStyles.item('pb');
    myAnchoredFrame.paragraphs[-1].applyParagraphStyle(p_style);
    
    var c_style = doc.characterStyles.item('normal');
    myAnchoredFrame.paragraphs[-1].applyCharacterStyle(c_style);

    with(myAnchoredFrame.anchoredObjectSettings){
      anchoredPosition = AnchorPosition.anchored;
      spineRelative = true;
      horizontalReferencePoint = AnchoredRelativeTo.pageMargins;
      verticalAlignment = VerticalAlignment.centerAlign;
      anchorXoffset = 5;
    }
    return false;
  }
}

function xmlRuleForPersName() {
  this.name = "XmlRuleForPersName";
  this.xpath = "//persName";
  this.apply = function(myElement, myRuleProcessor){
    var attr = myElement.xmlAttributes.itemByName('rend');
    var style;
    if (attr != null) {
      style = attr.value;
    } else {
      style = 'normal';
    }
    apply_c_style(style);
    var container = write(myElement.contents);

    var attr = myElement.xmlAttributes.itemByName('key');
    if (attr != null) {
      var key = attr.value;
      save_key_container(key, container);
      
      var name = myElement.xmlAttributes.itemByName('name').value;
      key += name;
      save_key_container(key, container);
    }

    return false;
  }
}

/* 記錄 人名、地名 所在頁碼 */
function save_key_container(key, container) {
  if (key in key_containers) { // 如果這個 key 已經出現過
    var containers = key_containers[key];
    var i = containers.indexOf(container);
    if (i < 0) { // 如果這個 key 在這一頁還沒有出現過
      key_containers[key].push(container);
    }
  } else {
    key_containers[key] = [container];
  }
}

function xmlRuleForPlaceName() {
  this.name = "XmlRuleForPlaceName";
  this.xpath = "//placeName";
  this.apply = function(myElement, myRuleProcessor){
    //var insertion_point = my_story.insertionPoints.item(-1);
    var attr = myElement.xmlAttributes.itemByName('rend');
    var style;
    if (attr != null) {
      style = attr.value;
    } else {
      style = 'normal';
    }
    apply_c_style(style);
    var container = write(myElement.contents);

    var attr = myElement.xmlAttributes.itemByName('key');
    if (attr != null) {
      var key = attr.value;
      save_key_container(key, container); // 以地名的 key 記錄 插入位置
      var name = myElement.xmlAttributes.itemByName('name').value;
      // 以地名的 key 加上名稱 記錄頁碼, 因為文本裡用的地名可能不是 authority db 裡的常名
      key += name;
      save_key_container(key, container); 
    }
    return false;
  }
}

function xmlRuleForSpan() {
  //log.writeln('xmlRuleForSpan');
  this.name = "XmlRuleForSpan";
  this.xpath = "//span";
  this.apply = function(myElement, myRuleProcessor){
    //log.write(myElement.contents);
    var style="normal";
    if (myElement.xmlAttributes.length>0) {
      style = myElement.xmlAttributes.itemByName('rend').value;
    }
    parent = myElement.parent.markupTag.name;
    apply_c_style(style, parent);
    write(myElement.contents, parent);
    return false;
  }
  //log.writeln('...end xmlRuleForSpan')
}

var log = new File(config['log']);
log.open( "w" );

var doc = app.open(File(config['style_template']));
mySetup()
addTextFrames();

doc.xmlElements.item(0).importXML(File(config['xml_source']));
var my_story = doc.stories.item(0);
var my_story = doc.pages.item(0).textFrames.itemByName('body').parentStory;

/*
  第一階段，只處理 body
*/
var rule_set = new Array (
  new xmlRuleForBody,
  new xmlRuleForFootnote,
  new xmlRuleForHeader,
  new xmlRuleForImg,
  new xmlRuleForP,
  new xmlRuleForPb,
  new xmlRuleForPersName,
  new xmlRuleForPlaceName,
  new xmlRuleForSpan,
);
__processRuleSet(doc.xmlElements.item(0), rule_set);

/*
  將 persName, placeName 所在頁碼填入最後的索引
  因為當頁數很多的時候，索引取得的頁數會不正確，差一頁
  所以第一階段 body 都做完後，希望頁數固定了，再來做後面的 back
  這時再去取得頁碼
*/
log.writeln('handle back');
var rule_set = new Array (
  new xmlRuleForBack,
  new xmlRuleForHeader,
  new xmlRuleForIndexPersonPages,
  new xmlRuleForIndexPlacePages,
  new xmlRuleForP,
  new xmlRuleForSpan
);
__processRuleSet(doc.xmlElements.item(0), rule_set);

log.close()
app.activeDocument.save(new File(config['output_file'])); 
alert('done')