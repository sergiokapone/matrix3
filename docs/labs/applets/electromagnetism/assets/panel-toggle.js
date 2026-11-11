// Згортання керування в аплетах. Три випадки:
//  1) плаваюча панель #panel: кнопка першим рядком панелі;
//  2) блоки .controls у потоці сторінки: одна кнопка перед першим, згортає всі;
//  3) бічна колонка aside.params (її вміст перемальовується скриптом сторінки):
//     заголовок-псевдоелемент, клік по ньому згортає колонку.
(function () {
  var TXT = 'Керування';
  function css(t) { var s = document.createElement('style'); s.textContent = t; document.head.appendChild(s); }
  function label(b, c, name) {
    b.textContent = (c ? '▸ ' : '▾ ') + name;
    b.setAttribute('aria-expanded', c ? 'false' : 'true');
  }
  var BTN = '.pt-btn{display:block;text-align:left;font:inherit;font-weight:600;font-size:13px;' +
            'background:transparent;color:inherit;border:0;padding:0 0 2px;cursor:pointer}';

  function mkBtn(onToggle) {
    var b = document.createElement('button');
    b.type = 'button'; b.className = 'pt-btn';
    var c = false; label(b, c, TXT);
    b.addEventListener('click', function () { c = !c; onToggle(c); label(b, c, TXT); });
    return b;
  }

  function init() {
    var p = document.getElementById('panel');
    if (p) {
      if (p.querySelector('.pt-btn')) return;
      css(BTN + '#panel .pt-btn{width:100%}#panel.collapsed>:not(.pt-btn){display:none!important}' +
          '#panel.collapsed{width:auto!important;max-width:none!important}#panel.collapsed .pt-btn{padding:0}');
      p.insertBefore(mkBtn(function (c) { p.classList.toggle('collapsed', c); }), p.firstChild);
      return;
    }
    var ctl = document.querySelectorAll('.controls');
    if (ctl.length) {
      css(BTN + '.pt-btn{margin-top:10px}body.ctl-collapsed .controls{display:none!important}');
      ctl[0].parentNode.insertBefore(
        mkBtn(function (c) { document.body.classList.toggle('ctl-collapsed', c); }), ctl[0]);
      return;
    }
    var as = document.querySelectorAll('aside.params');
    if (as.length) {
      css('aside.params::before{content:"▾ Параметри";display:block;font-weight:600;font-size:13px;cursor:pointer;padding:2px 0 6px}' +
          'aside.params.collapsed::before{content:"▸ Параметри";padding-bottom:2px}' +
          'aside.params.collapsed>*{display:none!important}');
      Array.prototype.forEach.call(as, function (a) {
        a.addEventListener('click', function (e) {
          if (e.target === a) a.classList.toggle('collapsed');
        });
      });
    }
  }
  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', init);
  else init();
})();
