// Theme and language before first paint, so the page doesn't flash.
(function () {
  var d = document.documentElement, t = null, l = null;
  try { t = localStorage.getItem("theme"); l = localStorage.getItem("lang"); } catch (e) { /* storage blocked */ }
  if (t === "light" || t === "dark") d.dataset.theme = t;
  var nav = (navigator.language || "en").slice(0, 2).toLowerCase();
  d.lang = l || (["cs", "sk", "de", "en"].indexOf(nav) >= 0 ? nav : "en");
})();
