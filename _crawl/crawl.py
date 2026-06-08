# -*- coding: utf-8 -*-
"""
爬取 new Google Sites (doublecross3rd) 全部子頁面，渲染後抽主內容，
輸出成本地簡潔 HTML 到 ../rules/，含共用側邊導覽與 rules.css。
內容為 JS 渲染，故用 headless Edge --dump-dom 取得渲染後 DOM。
"""
import os, re, sys, time, subprocess, urllib.request, urllib.parse, hashlib
from bs4 import BeautifulSoup, Tag

sys.stdout.reconfigure(encoding="utf-8")

EDGE = r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"
HOST = "https://sites.google.com"
ROOT = "/site/doublecross3rd/"
HERE = os.path.dirname(os.path.abspath(__file__))
PROJ = os.path.dirname(HERE)
OUT = os.path.join(PROJ, "rules")
IMGDIR = os.path.join(OUT, "img")
DOMCACHE = os.path.join(HERE, "dom")
UDIR = os.path.join(os.environ.get("TEMP", HERE), "edge_crawl")
os.makedirs(OUT, exist_ok=True)
os.makedirs(IMGDIR, exist_ok=True)
os.makedirs(DOMCACHE, exist_ok=True)

KEEP_ATTR = {"a": ["href"], "img": ["src", "alt"], "td": ["colspan", "rowspan"], "th": ["colspan", "rowspan"]}
BLOCK_KEEP = {"h1","h2","h3","h4","h5","h6","p","ul","ol","li","table","thead","tbody","tr","td","th",
              "blockquote","hr","img","a","figure","figcaption","br","strong","b","em","i","u","s",
              "sup","sub","code","pre"}

# ---------------- helpers ----------------
def norm_path(href):
    """把任意 href 正規化成 site 內 decoded 路徑（去掉 host / query / 結尾斜線），非站內回傳 None。"""
    if not href: return None
    href = href.strip()
    if href.startswith("#"): return None
    p = urllib.parse.urlparse(href)
    if p.netloc and "sites.google.com" not in p.netloc:
        return None
    path = urllib.parse.unquote(p.path)
    if ROOT not in path:
        return None
    path = path[path.index(ROOT):]
    if len(path) > len(ROOT) and path.endswith("/"):
        path = path[:-1]
    return path

def url_for(path):
    return HOST + urllib.parse.quote(path)

def render(path):
    """headless Edge 渲染並回傳 DOM 字串（含快取）。"""
    key = hashlib.md5(path.encode("utf-8")).hexdigest()
    cache = os.path.join(DOMCACHE, key + ".html")
    if os.path.exists(cache) and os.path.getsize(cache) > 2000:
        return open(cache, encoding="utf-8", errors="replace").read()
    url = url_for(path)
    try:
        r = subprocess.run(
            [EDGE, "--headless", "--disable-gpu", "--no-sandbox",
             "--virtual-time-budget=9000", "--user-data-dir=" + UDIR, "--dump-dom", url],
            capture_output=True, timeout=70)
        dom = r.stdout.decode("utf-8", "replace")
    except Exception as e:
        print("   render FAIL", e); dom = ""
    if len(dom) > 2000:
        open(cache, "w", encoding="utf-8").write(dom)
    return dom

def lca(nodes):
    if not nodes: return None
    anc = list(nodes[0].parents)
    for n in nodes[1:]:
        ap = set(n.parents)
        anc = [a for a in anc if a in ap]
    return anc[0] if anc else None

def content_root(soup):
    z = soup.select(".zfr3Q")
    root = lca(z)
    if root is None:
        root = soup.find(attrs={"role": "main"})
    return root

def page_title(soup, path):
    root = content_root(soup)
    if root:
        h = root.find(["h1","h2"])
        if h and h.get_text(strip=True):
            return h.get_text(strip=True)
    seg = path[len(ROOT):].split("/")[-1] if path != ROOT else "首頁"
    return seg or "首頁"

# ---------------- discover (BFS) ----------------
def discover():
    seen, order, queue = set(), [], [ROOT]
    while queue:
        path = queue.pop(0)
        if path in seen: continue
        seen.add(path); order.append(path)
        print(f"[discover {len(order)}] {path}")
        dom = render(path)
        soup = BeautifulSoup(dom, "html.parser")
        for a in soup.find_all("a", href=True):
            np = norm_path(a["href"])
            if np and np not in seen and np not in queue:
                queue.append(np)
    return order

# ---------------- clean ----------------
def download_img(src, imgmap):
    if not src or src.startswith("data:"): return None
    if "gstatic.com" in src or src.endswith(".svg"): return None
    if src in imgmap: return imgmap[src]
    try:
        full = src if src.startswith("http") else (HOST + src)
        req = urllib.request.Request(full, headers={"User-Agent": "Mozilla/5.0"})
        data = urllib.request.urlopen(req, timeout=40).read()
    except Exception as e:
        print("   img FAIL", e); return None
    ext = ".png"
    low = src.lower()
    for e in (".jpg", ".jpeg", ".gif", ".webp", ".png"):
        if e in low: ext = e; break
    name = f"img{len(imgmap)+1:03d}{ext}"
    open(os.path.join(IMGDIR, name), "wb").write(data)
    imgmap[src] = "img/" + name
    return imgmap[src]

def clean(root, path2file, imgmap, title=None):
    """把 content_root 轉成簡潔 HTML 字串。"""
    soup = BeautifulSoup(str(root), "html.parser")
    # 移除雜訊
    for sel in ["script","style","noscript","svg","button","[role=navigation]","nav","header","footer"]:
        for n in soup.select(sel): n.decompose()
    for n in soup.find_all(attrs={"aria-hidden": "true"}): n.decompose()

    # zfr3Q 文字塊 -> p（除非本身是標題或含表格/清單）
    for d in soup.select(".zfr3Q"):
        if d.name in ("h1","h2","h3","h4","h5","h6"): continue
        if d.find(["table","ul","ol","h1","h2","h3","h4","h5","h6"]): continue
        d.name = "p"
    # role=heading -> hN
    for d in soup.find_all(attrs={"role": "heading"}):
        lvl = d.get("aria-level", "3")
        try: lvl = max(2, min(6, int(lvl)))
        except: lvl = 3
        d.name = "h" + str(lvl)

    # 移除與頁標題重複的第一個區塊（避免標題出現兩次）
    if title:
        tnorm = re.sub(r"\s", "", title)
        for e in soup.find_all(["h1","h2","h3","h4","h5","h6","p"]):
            if re.sub(r"\s", "", e.get_text()) == tnorm:
                e.decompose(); break

    # 圖片下載 + 改寫
    for im in soup.find_all("img"):
        local = download_img(im.get("src", ""), imgmap)
        if local: im["src"] = local
        else: im.decompose()

    # 連結改寫
    for a in soup.find_all("a"):
        np = norm_path(a.get("href", ""))
        if np and np in path2file:
            a["href"] = path2file[np]
        elif a.get("href", "").startswith("http"):
            a["target"] = "_blank"; a["rel"] = "noopener"
        else:
            a.unwrap(); continue

    # 去屬性
    for t in soup.find_all(True):
        keep = KEEP_ATTR.get(t.name, [])
        for at in list(t.attrs):
            if at not in keep: del t[at]

    # 反覆 unwrap 非白名單標籤（保留子內容）
    changed = True
    while changed:
        changed = False
        for t in soup.find_all(True):
            if t.name not in BLOCK_KEEP:
                t.unwrap(); changed = True; break

    html = str(soup)
    html = re.sub(r"(\s*<p>\s*</p>\s*)+", "\n", html)      # 空段落
    html = re.sub(r"\n{3,}", "\n\n", html)
    return html.strip()

# ---------------- sidebar ----------------
def build_sidebar(order, titles, path2file, current=None):
    items = []
    for p in order:
        depth = p[len(ROOT):].count("/") if p != ROOT else 0
        cls = "side-link" + (" current" if p == current else "")
        items.append(
            f'<a class="{cls}" style="padding-left:{12+depth*16}px" href="{path2file[p]}">{titles[p]}</a>'
        )
    return '<nav class="rules-side">\n' + "\n".join(items) + "\n</nav>"

PAGE_TMPL = """<!DOCTYPE html>
<html lang="zh-Hant"><head>
<meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{title} — Double Cross 3rd</title>
<link rel="stylesheet" href="rules.css">
</head><body>
<div class="rules-wrap">
{sidebar}
<main class="rules-main">
<h1 class="rules-title">{title}</h1>
<article class="rules-content">
{content}
</article>
<p class="rules-src">原始來源：<a href="{src}" target="_blank" rel="noopener">Google Sites</a>（本地存檔）</p>
</main>
</div>
</body></html>
"""

def main():
    order = discover()
    print(f"\n共 {len(order)} 個頁面\n")

    # 解析所有頁面
    soups, titles = {}, {}
    for p in order:
        s = BeautifulSoup(render(p), "html.parser")
        soups[p] = s
        titles[p] = page_title(s, p)

    # 配檔名（首頁=index.html，其餘 pNN.html，依 order）
    path2file = {}
    n = 0
    for p in order:
        if p == ROOT:
            path2file[p] = "index.html"
        else:
            n += 1; path2file[p] = f"p{n:02d}.html"

    # 產生每頁
    imgmap = {}
    for p in order:
        root = content_root(soups[p])
        body = clean(root, path2file, imgmap, titles[p]) if root else "<p>（無內容）</p>"
        sidebar = build_sidebar(order, titles, path2file, current=p)
        out = PAGE_TMPL.format(title=titles[p], sidebar=sidebar, content=body, src=url_for(p))
        open(os.path.join(OUT, path2file[p]), "w", encoding="utf-8").write(out)
        print(f"  寫出 {path2file[p]}  <- {titles[p]}  ({len(body)} chars)")

    print(f"\n完成：{len(order)} 頁，{len(imgmap)} 張圖片 -> {OUT}")

if __name__ == "__main__":
    main()
