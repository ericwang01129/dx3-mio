/* =========================================================
   DX3-mio iframe 主頁 — 邏輯
   1) 等比縮放固定 2560×1440 舞台以適配 iframe
   2) 載入 data.json（唯一文本來源）並渲染各畫面
   3) 標題 → 點擊 → 選單 → 玩家/NPC/規則 的切換
   ========================================================= */
(function () {
  "use strict";

  var BASE_W = 2560, BASE_H = 1440;
  var stage = document.getElementById("stage");

  /* ---------- 1) 等比縮放置中 ---------- */
  function fit() {
    var s = Math.min(window.innerWidth / BASE_W, window.innerHeight / BASE_H);
    stage.style.transform = "translate(-50%, -50%) scale(" + s + ")";
  }
  window.addEventListener("resize", fit);
  fit();

  /* ---------- 小工具 ---------- */
  function el(id) { return document.getElementById(id); }
  function setText(id, txt) { var n = el(id); if (n) n.textContent = txt == null ? "" : txt; }
  function esc(s) {
    return String(s == null ? "" : s)
      .replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;");
  }
  function paragraphs(text) {
    return String(text || "")
      .split(/\n{2,}/)
      .map(function (p) { return "<p>" + esc(p).replace(/\n/g, "<br>") + "</p>"; })
      .join("");
  }

  /* ---------- 畫面切換 ---------- */
  var VIEWS = ["view-title", "view-menu", "view-players", "view-npc"];
  function showView(id) {
    VIEWS.forEach(function (v) {
      var n = el(v);
      if (n) n.classList.toggle("is-active", v === id);
    });
  }

  /* 以 URL hash 深連結到指定畫面（#menu / #players / #npc，預設標題） */
  var HASH_MAP = { menu: "view-menu", players: "view-players", npc: "view-npc" };
  function applyHash() {
    var h = (location.hash || "").replace("#", "").toLowerCase();
    var target = HASH_MAP[h] || "view-title";
    showView(target);
    if (target === "view-players") selectChar("players", 0);
    if (target === "view-npc") selectChar("npc", 0);
  }

  /* ---------- 2) 載入資料並渲染 ---------- */
  function init() {
    fetch("data.json", { cache: "no-cache" })
      .then(function (r) {
        if (!r.ok) throw new Error("HTTP " + r.status);
        return r.json();
      })
      .then(render)
      .catch(showError);
  }

  function showError(err) {
    var box = el("loading");
    box.classList.add("is-error");
    box.classList.remove("is-hidden");
    el("loading-text").innerHTML =
      "無法載入 data.json（" + esc(err && err.message) + "）<br><br>" +
      "請以 http 伺服器開啟此頁（例如於專案目錄執行<br>" +
      "<b>python -m http.server</b> 後開 http://localhost:8000）。<br>" +
      "直接用 file:// 開啟會被瀏覽器擋下 fetch。";
  }

  function render(data) {
    var meta = data.meta || {};
    var menu = data.menu || {};

    /* —— 標題畫面 —— */
    setText("t-tagline", meta.tagline);
    setText("t-subtitle", meta.dx3SubtitleJP);
    setText("t-title1", meta.titleLine1);
    setText("t-title2", meta.titleLine2);
    setText("t-hint", meta.clickHint);

    /* —— 主選單頭 —— */
    setText("m-tagline", meta.tagline);
    setText("m-subtitle", meta.dx3SubtitleJP);

    /* —— 主選單項目 —— */
    buildMainMenu(menu, meta);

    /* —— 玩家 / NPC —— */
    setText("players-tab", menu.playersTab || "PLAYER CHARACTER");
    setText("npc-tab", menu.npcTab || "NON PLAYER CHARACTER");
    buildCharSection("players", data.players || [], menu);
    buildCharSection("npc", data.npcs || [], menu);

    /* —— 標題頁點擊任意處 → 選單 —— */
    el("view-title").addEventListener("click", function () { showView("view-menu"); });

    /* —— 深連結支援 —— */
    applyHash();
    window.addEventListener("hashchange", applyHash);

    /* —— 收起載入畫面 —— */
    el("loading").classList.add("is-hidden");
  }

  /* ---------- 主選單 ---------- */
  function buildMainMenu(menu, meta) {
    var nav = el("main-menu");
    nav.innerHTML = "";

    addMenuBtn(nav, menu.players, "PLAYER", function () {
      showView("view-players"); selectChar("players", 0);
    });
    addMenuBtn(nav, menu.npc, "N P C", function () {
      showView("view-npc"); selectChar("npc", 0);
    });
    addMenuBtn(nav, menu.rules, "RULES", function () {
      if (meta.rulesUrl) window.open(meta.rulesUrl, "_blank", "noopener");
    });
    addMenuBtn(nav, menu.backTitle, "TITLE", function () {
      showView("view-title");
    }, true);
  }

  function addMenuBtn(nav, label, en, onClick, isBack) {
    var b = document.createElement("button");
    b.className = "menu-item" + (isBack ? " is-back" : "");
    b.type = "button";
    b.innerHTML = esc(label) + (en ? '<span class="mi-en">' + esc(en) + "</span>" : "");
    b.addEventListener("click", function (e) { e.stopPropagation(); onClick(); });
    nav.appendChild(b);
  }

  /* ---------- 角色區（玩家 / NPC 共用） ---------- */
  var CHAR_STATE = {}; // { players: [...], npc: [...] }

  function buildCharSection(key, list, menu) {
    CHAR_STATE[key] = list;
    var nav = el(key + "-menu");
    nav.innerHTML = "";

    list.forEach(function (c, i) {
      var b = document.createElement("button");
      b.className = "submenu-item";
      b.type = "button";
      b.dataset.index = i;
      b.textContent = c.name || ("登場人物 " + (i + 1));
      b.addEventListener("click", function () { selectChar(key, i); });
      nav.appendChild(b);
    });

    var back = document.createElement("button");
    back.className = "submenu-item is-back";
    back.type = "button";
    back.textContent = menu.backMenu || "返回選單";
    back.addEventListener("click", function () { showView("view-menu"); });
    nav.appendChild(back);

    if (list.length) selectChar(key, 0);
  }

  function selectChar(key, index) {
    var list = CHAR_STATE[key] || [];
    var c = list[index];
    if (!c) return;

    /* 子選單高亮 */
    var nav = el(key + "-menu");
    Array.prototype.forEach.call(nav.querySelectorAll(".submenu-item"), function (b) {
      if (b.classList.contains("is-back")) return;
      b.classList.toggle("is-current", String(b.dataset.index) === String(index));
    });

    /* 立繪 */
    var art = el(key + "-art");
    if (c.image) {
      art.innerHTML =
        '<img src="' + esc(c.image) + '" alt="' + esc(c.name) + '">';
    } else {
      art.innerHTML =
        '<div class="art-empty"><span class="ae-zh">立繪待補</span>' +
        '<span class="ae-en">NO IMAGE</span></div>';
    }

    /* 詳情 */
    var tags = (c.tags || []).map(function (t) {
      return '<span class="char-tag">' + esc(t) + "</span>";
    }).join("");

    var detail = el(key + "-detail");
    detail.innerHTML =
      (tags ? '<div class="char-tags">' + tags + "</div>" : "") +
      (c.furigana ? '<div class="char-furigana">' + esc(c.furigana) + "</div>" : "") +
      '<h1 class="char-name">' + esc(c.name) + "</h1>" +
      (c.motto ? '<blockquote class="char-motto">' + esc(c.motto) + "</blockquote>" : "") +
      '<div class="char-intro">' + paragraphs(c.intro) + "</div>";

    /* 重播淡入動畫 */
    detail.style.animation = "none";
    void detail.offsetWidth;
    detail.style.animation = "art-in .45s ease both";
  }

  /* ---------- 啟動 ---------- */
  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", init);
  } else {
    init();
  }
})();
