/* ============================================================
   MONARCH CASTLE — live instruments
   BNTI and ESGMap read their REAL published data at runtime.
   If a feed can't be reached, the last good snapshot stands
   (the publish-gate principle, applied to the website itself).
   No localStorage. Respects reduced-motion.
   ============================================================ */
(function () {
  "use strict";
  document.documentElement.classList.add("js");
  var reduceMotion = window.matchMedia("(prefers-reduced-motion: reduce)").matches;

  /* ---------- Scroll reveal ---------- */
  var revealEls = document.querySelectorAll(".reveal");
  if ("IntersectionObserver" in window && !reduceMotion) {
    var io = new IntersectionObserver(function (entries) {
      entries.forEach(function (e) {
        if (e.isIntersecting) { e.target.classList.add("in"); io.unobserve(e.target); }
      });
    }, { threshold: 0.1, rootMargin: "0px 0px -6% 0px" });
    revealEls.forEach(function (el) { io.observe(el); });
    var forceAll = function () {
      revealEls.forEach(function (el) {
        if (parseFloat(getComputedStyle(el).opacity) < 0.99) { el.style.opacity = "1"; el.style.transform = "none"; }
      });
    };
    var snapVisible = function () {
      revealEls.forEach(function (el) {
        var r = el.getBoundingClientRect();
        if (r.top < (window.innerHeight || 0) && r.bottom > 0 && parseFloat(getComputedStyle(el).opacity) < 0.99) {
          el.style.transition = "none"; el.style.opacity = "1"; el.style.transform = "none";
        }
      });
    };
    setTimeout(snapVisible, 1600);
    setTimeout(forceAll, 3200);
    window.addEventListener("scroll", snapVisible, { passive: true });
    document.addEventListener("visibilitychange", function () { if (!document.hidden) setTimeout(snapVisible, 80); });
  } else {
    revealEls.forEach(function (el) { el.classList.add("in"); });
  }

  /* ---------- Topbar scrolled state ---------- */
  var topbar = document.querySelector(".topbar");
  var onScroll = function () { topbar.classList.toggle("scrolled", window.scrollY > 12); };
  window.addEventListener("scroll", onScroll, { passive: true });
  onScroll();

  /* ============================================================
     BNTI — live from the real published snapshot
     ============================================================ */
  var BNTI_URL = "https://raw.githubusercontent.com/akgularda/border-neighbor-threat-index/main/bnti_data.json";
  // Last good snapshot — real values captured 2026-06-14 03:06 UTC.
  var BNTI_FALLBACK = {
    main_index: 3.59, status: "STABLE",
    generated_at: "2026-06-14T03:06:06", next_update: "2026-06-14T05:00:00",
    active_scan: false, version: "2.0.0", events_total: 48,
    countries: { Armenia: 6.0, Bulgaria: 5.87, Iran: 5.62, Georgia: 4.65, Syria: 2.24, Greece: 1.0, Iraq: 1.0 }
  };

  function bandFor(v) { if (v >= 7) return "critical"; if (v >= 5) return "elevated"; return "stable"; }
  function hm(iso) { return (iso && iso.length >= 16) ? iso.slice(11, 16) : "—"; }
  function sumEvents(countries) {
    try { return Object.keys(countries).reduce(function (s, k) { var c = countries[k]; return s + (c && c.events ? c.events.length : 0); }, 0); }
    catch (e) { return "—"; }
  }

  var el = {
    val: document.getElementById("compValue"),
    band: document.getElementById("compBand"),
    sub: document.getElementById("compDelta"),
    marker: document.getElementById("gaugeMarker"),
    nodes: document.getElementById("neighborNodes"),
    pillVal: document.getElementById("pillVal"),
    pillBand: document.getElementById("pillBand"),
    pillBandB: document.getElementById("pillBandB"),
    v2: document.getElementById("compValue2"),
    b2: document.getElementById("compBand2"),
    live: document.querySelector(".inst-head .live"),
    liveLabel: document.getElementById("liveLabel"),
    ts: document.getElementById("instTs"),
    scanEvents: document.getElementById("scanEvents"),
    scanState: document.getElementById("scanState"),
    scanNext: document.getElementById("scanNext"),
    srcNote: document.getElementById("srcNote")
  };

  function setText(node, txt) { if (node) node.textContent = txt; }

  function renderBNTI(d, isLive) {
    var comp = d.main_index;
    var statusU = (d.status || bandFor(comp)).toUpperCase();
    var band = (d.status || bandFor(comp)).toLowerCase();
    setText(el.val, comp.toFixed(1));
    if (el.band) { el.band.textContent = statusU; el.band.setAttribute("data-band", band); }
    if (el.marker) el.marker.style.left = Math.max(0, Math.min(100, ((comp - 1) / 9) * 100)) + "%";
    setText(el.sub, "UPDATED " + hm(d.generated_at) + " UTC");

    setText(el.pillVal, comp.toFixed(1));
    if (el.pillBand) { el.pillBand.textContent = statusU; el.pillBand.style.color = band === "critical" ? "var(--alert)" : "var(--ink)"; }
    if (el.pillBandB) { el.pillBandB.textContent = statusU; el.pillBandB.style.color = band === "critical" ? "var(--alert)" : "var(--ink)"; }
    setText(el.v2, comp.toFixed(1));
    if (el.b2) { el.b2.textContent = statusU; el.b2.setAttribute("data-band", band); }

    // neighbors, sorted high → low
    if (el.nodes) {
      var arr = Object.keys(d.countries).map(function (k) {
        var c = d.countries[k];
        return { name: k, index: (typeof c === "number" ? c : c.index) };
      }).sort(function (a, b) { return b.index - a.index; });
      el.nodes.innerHTML = "";
      arr.forEach(function (n) {
        var row = document.createElement("div");
        row.className = "node";
        row.setAttribute("data-state", bandFor(n.index));
        row.innerHTML =
          '<span class="name">' + n.name + '</span>' +
          '<span class="bar"><i style="width:' + (n.index * 10) + '%"></i></span>' +
          '<span class="score">' + n.index.toFixed(1) + '</span>';
        el.nodes.appendChild(row);
      });
    }

    setText(el.scanEvents, (d.events_total != null ? d.events_total : sumEvents(d.countries)));
    setText(el.scanState, d.active_scan ? "SCANNING" : "IDLE");
    setText(el.scanNext, hm(d.next_update) + " UTC");
    setText(el.liveLabel, isLive ? "LIVE" : "LAST GOOD");
    if (el.live) el.live.classList.toggle("stale", !isLive);
    setText(el.srcNote, isLive ? "Source · bnti_data.json" : "Last good snapshot · held");
  }

  // show the last good snapshot immediately, then try the live feed
  renderBNTI(BNTI_FALLBACK, false);

  function loadBNTI() {
    fetch(BNTI_URL, { cache: "no-store" })
      .then(function (r) { if (!r.ok) throw 0; return r.json(); })
      .then(function (j) {
        if (!j || !j.meta || !j.countries) throw 0;
        renderBNTI({
          main_index: j.meta.main_index, status: j.meta.status,
          generated_at: j.meta.generated_at, next_update: j.meta.next_update,
          active_scan: j.meta.active_scan, version: j.meta.version,
          events_total: sumEvents(j.countries), countries: j.countries
        }, true);
      })
      .catch(function () { /* keep last good snapshot */ });
  }
  loadBNTI();
  if (!reduceMotion) setInterval(loadBNTI, 5 * 60 * 1000);

  // ticking UTC clock
  function fmtTime() {
    var d = new Date();
    function p(n) { return (n < 10 ? "0" : "") + n; }
    return p(d.getUTCHours()) + ":" + p(d.getUTCMinutes()) + ":" + p(d.getUTCSeconds()) + " UTC";
  }
  if (el.ts) { el.ts.textContent = fmtTime(); if (!reduceMotion) setInterval(function () { el.ts.textContent = fmtTime(); }, 1000); }

  /* ============================================================
     ESGMap — live renewable-electricity share (Our World in Data)
     ============================================================ */
  var ESG_URL = "https://raw.githubusercontent.com/akgularda/esgmap/master/public/api/metric/renewable.json";
  var ESG_SHOW = ["NOR", "BRA", "DEU", "TUR", "CHN", "USA"];
  var ESG_NAMES = { NOR: "Norway", BRA: "Brazil", DEU: "Germany", TUR: "Türkiye", CHN: "China", USA: "United States" };
  var ESG_FALLBACK = { NOR: 99, BRA: 86.6, DEU: 59.1, TUR: 43.3, CHN: 37, USA: 25.6 };
  var esgWrap = document.getElementById("esgRows");
  var esgYear = document.getElementById("esgYear");

  function renderESG(getVal, isLive) {
    if (!esgWrap) return;
    esgWrap.innerHTML = "";
    ESG_SHOW.forEach(function (iso) {
      var v = getVal(iso);
      if (v == null) return;
      var row = document.createElement("div");
      row.className = "lrow";
      row.innerHTML =
        '<span class="ln">' + ESG_NAMES[iso] + '</span>' +
        '<span class="lb"><i style="width:' + Math.max(2, Math.min(100, v)) + '%"></i></span>' +
        '<span class="lv">' + Math.round(v) + '%</span>';
      esgWrap.appendChild(row);
    });
    if (esgYear) esgYear.textContent = isLive ? "LIVE · OWID" : "OWID · last good";
  }
  renderESG(function (iso) { return ESG_FALLBACK[iso]; }, false);
  fetch(ESG_URL, { cache: "no-store" })
    .then(function (r) { if (!r.ok) throw 0; return r.json(); })
    .then(function (j) {
      var map = {};
      (j.values || []).forEach(function (v) { map[v.iso3] = v.value; });
      renderESG(function (iso) { return map[iso]; }, true);
    })
    .catch(function () { /* keep fallback */ });

  /* ---------- Smooth anchor focus ---------- */
  document.querySelectorAll('a[href^="#"]').forEach(function (a) {
    a.addEventListener("click", function (e) {
      var id = a.getAttribute("href");
      if (id.length < 2) return;
      var target = document.querySelector(id);
      if (!target) return;
      e.preventDefault();
      window.scrollTo({ top: target.getBoundingClientRect().top + window.scrollY - 80, behavior: reduceMotion ? "auto" : "smooth" });
      target.setAttribute("tabindex", "-1");
      target.focus({ preventScroll: true });
    });
  });
})();
