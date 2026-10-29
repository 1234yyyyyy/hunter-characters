#!/usr/bin/env python3
"""作品角色出場劇情畫面 產生器
用法: python3 make_char_page.py --wiki hunterxhunter --title "獵人 HUNTER×HUNTER" --chars chars.txt --out site/
資料全部取自 Fandom 維基 (MediaWiki API)：角色頁 Plot 章節裡的劇情圖與圖說、各篇章頁的話數/集數、中文分站的簡介。
"""
import argparse, json, re, sys, time, html, urllib.parse, urllib.request
import mwparserfromhell as mwp
import opencc
T = opencc.OpenCC('s2twp')
UA = {'User-Agent': 'Mozilla/5.0 charpage-generator'}

def api(base, **p):
    p.update(format='json', formatversion=2)
    url = base + '?' + urllib.parse.urlencode(p)
    for i in range(4):
        try:
            with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=30) as r:
                return json.load(r)
        except Exception as e:
            time.sleep(2 * (i + 1)); err = e
    raise err

def plain(s):
    s = mwp.parse(s).strip_code()
    return re.sub(r'\s+', ' ', s).strip()

def parse_ranges(arc_text):
    """從篇章頁 infobox 取得話數與集數（原文照抄）"""
    w = mwp.parse(arc_text)
    out = {}
    for t in w.filter_templates():
        for k in ('chapters', 'episodes'):
            if t.has(k):
                out[k] = plain(str(t.get(k).value).replace('<br />', ' / ').replace('<br>', ' / '))
        if out: break
    return out

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--wiki', default='hunterxhunter', help='Fandom 子網域，例如 hunterxhunter、onepiece')
    ap.add_argument('--zhwiki', default=None, help='中文分站 api 路徑，預設 https://<wiki>.fandom.com/zh/api.php')
    ap.add_argument('--title', default='獵人 HUNTER×HUNTER')
    ap.add_argument('--chars', required=True, help='角色英文頁名清單檔，一行一個')
    ap.add_argument('--arcmap', default=None, help='JSON：篇章英文名→中文名')
    ap.add_argument('--zhnames', default=None, help='JSON：英文頁名→中文名（中文分站沒有該角色時用）')
    ap.add_argument('--max-scenes', type=int, default=6)
    ap.add_argument('--theme', default='#5fd38a')
    ap.add_argument('--download', action='store_true', help='把圖片下載到 images/（建議，Fandom 擋熱連結）')
    ap.add_argument('--out', default='site')
    a = ap.parse_args()
    t0 = time.time()
    base = f'https://{a.wiki}.fandom.com/api.php'
    zhbase = a.zhwiki or f'https://{a.wiki}.fandom.com/zh/api.php'
    arcmap = json.load(open(a.arcmap, encoding='utf-8')) if a.arcmap else {}
    zhnames = json.load(open(a.zhnames, encoding='utf-8')) if a.zhnames else {}
    names = [l.strip() for l in open(a.chars, encoding='utf-8') if l.strip() and not l.startswith('#')]
    arc_cache, chars, gaps = {}, [], []
    for title in names:
        d = api(base, action='parse', page=title, prop='wikitext|langlinks', redirects=1)
        if 'parse' not in d: gaps.append(f'{title}: 找不到頁面'); continue
        P = d['parse']; real = P['title']; wt = mwp.parse(P['wikitext'])
        zh = next((l['title'] for l in P.get('langlinks', []) if l['lang'] == 'zh'), None)
        name, intro = zhnames.get(real, real), ''
        if zh:
            name = zhnames.get(real) or T.convert(zh)
            z = api(zhbase, action='parse', page=zh, prop='wikitext', section=0, redirects=1)
            if 'parse' in z:
                body = re.sub(r'\{\{[\s\S]*?\n\}\}', '', z['parse']['wikitext'], count=1)
                body = re.sub(r'<ref[^>]*/>|<ref[\s\S]*?</ref>', '', body)
                txt = plain(body)
                m = re.match(r'(.+?。.*?。)', txt)
                intro = T.convert((m.group(1) if m else txt)[:160])
        if not intro:  # 退回英文簡介
            lead = mwp.parse(str(wt.get_sections(include_lead=True, flat=True)[0]))
            for tp in lead.filter_templates(recursive=False):
                try: lead.remove(tp)
                except ValueError: pass
            lead = re.sub(r'<ref[\s\S]*?(/>|</ref>)', '', str(lead))
            txt = plain(lead); m = re.match(r'(.+?\.)\s', txt + ' ')
            intro = (m.group(1) if m else txt)[:260]
        # 劇情章節裡的圖
        scenes = []
        for sec in wt.get_sections(levels=[3]):
            head = plain(str(sec.filter_headings()[0].title))
            if not head.lower().endswith('arc'): continue
            arc = head
            if arc not in arc_cache:
                ad = api(base, action='parse', page=arc, prop='wikitext', section=0, redirects=1)
                arc_cache[arc] = parse_ranges(ad['parse']['wikitext']) if 'parse' in ad else {}
            for lk in sec.filter_wikilinks():
                tt = str(lk.title).strip()
                if not re.match(r'(?i)(file|image):', tt) or not lk.text: continue
                raw = re.sub(r'\[\[(?:[^|\]]*\|)?([^\]]*)\]\]', r'\1', str(lk.text))
                raw = re.sub(r'\{\{[^{}]*\}\}', '', raw)
                parts = [p for p in raw.split('|') if not re.fullmatch(r'\s*(thumb|thumbnail|right|left|center|frameless|upright.*|\d+px|x?\d+px|\d+x\d+px)\s*', p)]
                cap = plain(parts[-1]) if parts else ''
                if cap: scenes.append({'file': tt.split(':', 1)[1].strip(), 'arc': arc, 'en': cap})
        if not scenes: gaps.append(f'{name}: 角色頁劇情段落沒有圖片'); continue
        # 平均挑：每個篇章先取一張，再依序補
        pick, seen = [], set()
        for s in scenes:
            if s['arc'] not in seen: pick.append(s); seen.add(s['arc'])
        for s in scenes:
            if len(pick) >= a.max_scenes: break
            if s not in pick: pick.append(s)
        order = {s['file']: i for i, s in enumerate(scenes)}
        pick = sorted(pick[:a.max_scenes], key=lambda s: order[s['file']])
        ii = api(base, action='query', titles='|'.join('File:' + s['file'] for s in pick), prop='imageinfo', iiprop='url', iiurlwidth=800)
        urls = {}
        for pg in ii['query']['pages']:
            if pg.get('imageinfo'): urls[pg['title'].split(':', 1)[1]] = pg['imageinfo'][0].get('thumburl') or pg['imageinfo'][0]['url']
        norm = {k.replace('_', ' '): v for k, v in urls.items()}
        out = []
        for s in pick:
            u = norm.get(s['file'].replace('_', ' '))
            if not u: continue
            r = arc_cache.get(s['arc'], {})
            out.append({'img': u, 'arc': arcmap.get(s['arc'], s['arc']), 'range': ' ｜ '.join(v for v in (r.get('chapters'), r.get('episodes')) if v), 'caption': s['en']})
        chars.append({'id': re.sub(r'\W+', '-', real.lower()), 'name': name, 'en': real, 'intro': intro,
                      'src': f'https://{a.wiki}.fandom.com/wiki/' + urllib.parse.quote(real.replace(' ', '_')), 'scenes': out})
        print(f'  ✓ {name} ({real}) {len(out)} 場', file=sys.stderr)
    import os; os.makedirs(a.out, exist_ok=True)
    if a.download:  # Fandom 會擋外站引用圖片，下載縮成 720px 寬 JPEG 存在 images/
        from PIL import Image; import io, hashlib
        os.makedirs(os.path.join(a.out, 'images'), exist_ok=True)
        for c in chars:
            for s in c['scenes']:
                fn = 'images/' + hashlib.md5(s['img'].encode()).hexdigest()[:12] + '.jpg'
                p = os.path.join(a.out, fn)
                if not os.path.exists(p):
                    try:
                        raw = urllib.request.urlopen(urllib.request.Request(s['img'], headers=UA), timeout=30).read()
                        im = Image.open(io.BytesIO(raw)).convert('RGB')
                        if im.width > 720: im = im.resize((720, round(im.height * 720 / im.width)), Image.LANCZOS)
                        im.save(p, 'JPEG', quality=82)
                    except Exception as e:
                        gaps.append(f"{c['name']}: 圖片下載失敗 {e}"); continue
                s['img'] = fn
    tpl = open(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'template.html'), encoding='utf-8').read()
    page = (tpl.replace('__TITLE__', html.escape(a.title)).replace('__THEME__', a.theme)
               .replace('__WIKI__', a.wiki).replace('__DATA__', json.dumps(chars, ensure_ascii=False).replace('</', '<\\/')))
    open(os.path.join(a.out, 'index.html'), 'w', encoding='utf-8').write(page)
    json.dump({'characters': len(chars), 'scenes': sum(len(c['scenes']) for c in chars), 'gaps': gaps, 'seconds': round(time.time() - t0)},
              open(os.path.join(a.out, 'build_report.json'), 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    print(f'完成：{len(chars)} 角色，{time.time()-t0:.0f} 秒；缺漏 {gaps}', file=sys.stderr)

if __name__ == '__main__':
    main()
