# dx3-mio 主頁（iframe 嵌入用）

DX3（ダブルクロス The 3rd Edition）跑團主頁。固定設計畫素 **2560×1440**，等比縮放適配任意 iframe 尺寸（非 16:9 自動 letterbox）。
版面參考 IRIS STUDIO galgame 風格（標題 → 點擊切換選單 → 角色詳情），視覺套用 DX3 OVERED UI 暗色科幻主題。

## 檔案
| 檔案 | 用途 |
| --- | --- |
| `index.html` | 主頁面（stage 骨架 + 4 個畫面容器） |
| `styles.css` | DX3 暗色主題、2560×1440 縮放、切換動畫 |
| `app.js` | 載入 `data.json`、渲染各畫面、切換邏輯 |
| `data.json` | **唯一文本來源**：標題／選單／玩家／NPC／規則連結 |
| `assets/` | 圖片素材（背景、前景主角、玩家立繪） |
| `embed-test.html` | 多尺寸 iframe 嵌入測試頁 |
| `.nojekyll` | 關閉 GitHub Pages 的 Jekyll 處理 |

## 改內容（不需動程式）
所有文字都在 **`data.json`**：
- `meta.titleLine1 / titleLine2`：主頁兩行大標題（目前為佔位文字，替換成正式團名/標題）。
- `meta.dx3SubtitleJP`：上方日文小標（固定為 `ダブルクロス The 3rd Edition`）。
- `meta.rulesUrl`：「規則參考」連結（目前指向 Google Sites 規則頁，新分頁開啟）。
- `players[]`：玩家角色。`name / furigana / tags / motto / intro / image`。
- `npcs[]`：登場 NPC（已預留 6 位）。`image` 留空會顯示「立繪待補」佔位框；補圖時把 `image` 指向 `assets/檔名.png`。
- `intro` 內以**空白行**分段。

> 立繪/前景主角位置可在 `styles.css` 頂部 `:root` 的 `--hero-*` 變數微調。

### 深連結（直接開到指定畫面）
網址加 hash 可直接開到對應畫面，方便分享或在 iframe 中指定起始頁：
`#menu`（主選單）、`#players`（玩家角色）、`#npc`（登場 NPC）；無 hash 則為標題畫面。

## 本地預覽
`fetch('data.json')` 需要 http（直接 `file://` 開會被瀏覽器擋）。於專案目錄擇一執行：

```bash
python -m http.server 8000
```
然後開 `http://localhost:8000`（嵌入測試：`http://localhost:8000/embed-test.html`）。
VS Code 使用者也可用 **Live Server** 擴充。

## 部署到 GitHub Pages
1. 建立 repo 並推上全部檔案（含 `assets/`）：
   ```bash
   git init
   git add .
   git commit -m "DX3-mio main page"
   git branch -M main
   git remote add origin https://github.com/<帳號>/<repo>.git
   git push -u origin main
   ```
2. GitHub repo → **Settings → Pages** → Source 選 **Deploy from a branch** → Branch 選 `main` / 根目錄 `/ (root)` → Save。
3. 數十秒後可用 `https://<帳號>.github.io/<repo>/` 開啟。

## 在別的網站嵌入
```html
<iframe src="https://<帳號>.github.io/<repo>/"
        width="1280" height="720"
        style="border:0; aspect-ratio:16/9; max-width:100%;"
        allowfullscreen></iframe>
```
> 「規則參考」連到 Google Sites，因其禁止被 iframe 嵌入，故一律以新分頁開啟。
