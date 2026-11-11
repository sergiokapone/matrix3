// Коли сторінка відкрита в iframe (на сайті кафедри) — повідомляє батьківській сторінці свою висоту.
(function () {
  if (window.self === window.top) return;
  function send() {
    var h = Math.ceil(document.body.getBoundingClientRect().height);
    parent.postMessage({ labsHeight: h }, "*");
  }
  window.addEventListener("load", send);
  window.addEventListener("resize", send);
  if (window.ResizeObserver) new ResizeObserver(send).observe(document.body);
})();
