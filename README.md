# 獵人 HUNTER×HUNTER・角色出場劇情畫面

網頁：https://1234yyyyyy.github.io/hunter-characters/

## 產生器怎麼用
```bash
pip install mwparserfromhell opencc-python-reimplemented pillow
python3 make_char_page.py --wiki hunterxhunter --title "獵人 HUNTER×HUNTER" \
  --chars hxh_chars.txt --arcmap hxh_arcs.json --zhnames hxh_zhnames.json --captions hxh_captions_zh.json --download --out site
```
換別的作品（例：海賊王）：
1. `--wiki` 改成該作品 Fandom 子網域（onepiece.fandom.com → `onepiece`）。
2. 新增角色清單檔（一行一個英文角色頁名）。
3. 可選：篇章中文名 JSON（`--arcmap`）、中文分站沒有的角色中文名（`--zhnames`）。
4. 跑完把 `site/` 發布到 GitHub Pages。

資料來源：角色頁「Plot」各篇章裡的劇情圖與圖說；篇章頁的話數／集數；中文分站的簡介（轉繁體）。不自行編造出場資料，每個角色附來源連結。`build_report.json` 會列出缺漏。
樣板 `template.html` 決定外觀。約 40 個角色、含下載圖片約 1.5 分鐘。
圖說翻譯放在 `hxh_captions_zh.json`（英文圖說→中文，`intro:頁名`→中文簡介），檔案存在就會套用，英文原文以小字顯示在下方。
