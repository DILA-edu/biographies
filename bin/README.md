# 佛教傳記文學

## 作業輔助程式

### format.py

1. 將 cRef 屬性值 標準化
  例如, 原為: CBETA, T39, no. 1799, p. 845, c22-23
  轉為: CBETA_T39_n1799_p845_c22-p845_c23
2. 將 `<placeName>` 內容中有半形空格區隔的, 再包 `<placeName>`
  例如: `<placeName xml:id="abc">金山 法鼓寺</placeName>`
  轉為: `<placeName xml:id="abc"><placeName>金山</placeName><placeName>法鼓寺</placeName></placeName>`

### tags.py

列出所有使用過的標記

## 輸出 InDesign

### read-authority.py

呼叫 Authority 網站 API 將人名、地名資料分別存入: personAuthority.pickle, placeAuthority.pickle

## 輸出 csv 給 DocuSky GIS

先執行 `ruby csv4gis1.rb` 讀取 authority 資料, 
如果之前執行過，而 authority 資料也沒有更新，就不必重複執行。
然後執行 `ruby csv4gis2.rb`.