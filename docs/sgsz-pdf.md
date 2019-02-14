#宋高僧傳 PDF

by Ray Chou 2014.11.28-12.1

##InDesign Template 準備

InDesign 樣本檔：bin/indesign-template/styles.indd 

編輯這個檔案可以控制：

* 段落樣式
* 字元樣式
* 頁首

##InDesign 執行 script 環境設定

1. 進入 InDesign
2. 取得 script 存放路徑
    1. 功能表 視窗 => 公用程式 => 指令碼
    2. 在「使用者」上按右鍵 => 在「檔案總管」中顯現
3. 將 x2id.js 複製到以上路徑的 Script Panel 裡面
4. 此時在 InDesign 功能表 視窗 => 公用程式 => 指令碼 => 使用者 應該就可以看到該程式
5. 視需要修改 x2id.js 裡的 GIT_ROOT 常數，使其符合目前環境

##產生 InDesign 檔步驟

1. read-authority.py
    1. 從 Authority DB 讀取人名、地名資料，以便產生人名索引、地名索引。
    2. 這個程式執行過後，會產生 personAuthority.pickle, placeAuthority.pickle 給後續的程式使用。如果之後 Authority DB 沒有更新，便可以略過本步驟，直接執行下一步驟。
2. x2id.py
    1. 產生 sgsz1.xml => 呼叫 x2id2.py => 產生 sgsz.xml
3. 在 InDesign 裡執行 x2id.js
    * InDesign 功能表 視窗 => 公用程式 => 指令碼 => 使用者 => 在 x2id 上按右鍵 => 執行指令碼
    * x2id.js 會讀取
        * GIT_ROOT/bin/indesign-template/styles.indd
        * GIT_ROOT/output/indesign/sgsz.xml
        * GIT_ROOT/Song-GSZ/gaiji
    * 輸出 GIT_ROOT/output/indesign/sgsz.indd