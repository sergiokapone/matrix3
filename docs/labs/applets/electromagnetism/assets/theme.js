/* Спільне перемикання теми для аплетів. Підключається в <head> кожного аплета.
   Ключ localStorage спільний з книгою (book.js), тому тема збігається з сайтом.
   Тема лежить в html[data-theme="light|dark"]; якщо не задана — діє системна.
   matchMedia('(prefers-color-scheme: dark)') підмінено: .matches і подія 'change'
   відображають обрану тему, тож код аплетів не доводиться переписувати. */
(function () {
  var KEY = 'elmag-book-theme', root = document.documentElement;
  var Q = /prefers-color-scheme\s*:\s*dark/;
  var realMM = window.matchMedia ? window.matchMedia.bind(window) : null;
  var sys = realMM ? realMM('(prefers-color-scheme: dark)') : { matches: false };
  var fakes = [];

  function stored() { try { var t = localStorage.getItem(KEY); return t === 'dark' || t === 'light' ? t : null; } catch (e) { return null; } }
  function isDark() { var t = root.getAttribute('data-theme'); return t ? t === 'dark' : !!sys.matches; }
  function apply(t) { if (t) root.setAttribute('data-theme', t); else root.removeAttribute('data-theme'); }

  apply(stored());

  if (realMM) {
    window.matchMedia = function (q) {
      if (!Q.test(String(q))) return realMM(q);
      var f = { media: String(q), onchange: null, _l: [],
        get matches() { return isDark(); },
        addEventListener: function (t, fn) { if (t === 'change') this._l.push(fn); },
        removeEventListener: function (t, fn) { this._l = this._l.filter(function (x) { return x !== fn; }); },
        addListener: function (fn) { this.addEventListener('change', fn); },
        removeListener: function (fn) { this.removeEventListener('change', fn); },
        dispatchEvent: function () { return true; } };
      fakes.push(f);
      return f;
    };
  }

  var btn;
  function label() { if (btn) { btn.textContent = isDark() ? '☀' : '☾'; btn.title = isDark() ? 'Світла тема' : 'Темна тема'; btn.setAttribute('aria-label', btn.title); } }
  function notify() {
    label();
    var ev = { matches: isDark(), media: '(prefers-color-scheme: dark)' };
    fakes.forEach(function (f) {
      f._l.slice().forEach(function (fn) { try { fn.call(f, ev); } catch (e) { console.error(e); } });
      if (typeof f.onchange === 'function') f.onchange(ev);
    });
    window.dispatchEvent(new CustomEvent('themechange', { detail: { dark: isDark() } }));
  }
  function set(t) { apply(t); try { localStorage.setItem(KEY, t); } catch (e) {} notify(); }

  if (sys.addEventListener) sys.addEventListener('change', function () { if (!stored()) notify(); });
  window.addEventListener('storage', function (e) { if (e.key === KEY) { apply(stored()); notify(); } });

  function mount() {
    btn = document.createElement('button');
    btn.type = 'button'; btn.id = 'theme-toggle-applet';
    btn.style.cssText = 'position:fixed;top:6px;right:6px;z-index:2147483000;width:30px;height:30px;padding:0;margin:0;' +
      'border-radius:50%;border:1px solid #8888;background:rgba(128,128,128,.18);color:inherit;font:16px/1 system-ui,sans-serif;' +
      'cursor:pointer;opacity:.75;backdrop-filter:blur(3px)';
    btn.onmouseenter = function () { btn.style.opacity = 1; };
    btn.onmouseleave = function () { btn.style.opacity = .75; };
    btn.onclick = function () { set(isDark() ? 'light' : 'dark'); };
    document.body.appendChild(btn);
    label();
  }
  if (document.body) mount(); else document.addEventListener('DOMContentLoaded', mount);

  window.AppletTheme = { isDark: isDark, set: set };
})();
