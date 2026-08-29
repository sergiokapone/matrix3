  document.getElementById('search').addEventListener('input', function (e) {
    var q = e.target.value.trim().toLowerCase();
    document.querySelectorAll('.card').forEach(function (card) {
      var hay = card.getAttribute('data-search');
      card.dataset.hidden = q && hay.indexOf(q) === -1 ? "true" : "false";
    });
    document.querySelectorAll('.semester-group').forEach(function (group) {
      var anyVisible = Array.from(group.querySelectorAll('.card'))
        .some(function (c) { return c.dataset.hidden !== "true"; });
      group.style.display = anyVisible ? "" : "none";
    });
  });

  // ---- стрілки пре-/постреквізитів: навести на рядок у списку - і
  // від нього до відповідної картки будується лінія ----
  (function () {
    var svg = document.getElementById('rel-arrows');
    var cardsById = {};
    document.querySelectorAll('.card[data-id]').forEach(function (c) {
      cardsById[c.getAttribute('data-id')] = c;
    });

    function sizeSvgToDocument() {
      svg.setAttribute('width', document.documentElement.scrollWidth);
      svg.setAttribute('height', document.documentElement.scrollHeight);
    }

    function pagePoint(rect, side) {
      // ліва чи права середина елемента, у координатах усього документа
      // (а не вьюпорта) - лінія лишається правильною при будь-якому скролі
      var x = side === 'left' ? rect.left : rect.right;
      return { x: x + window.scrollX, y: rect.top + rect.height / 2 + window.scrollY };
    }

    function clearArrow() {
      var path = svg.querySelector('path.rel-arrow');
      if (path) path.remove();
      document.querySelectorAll('.card.hl-target').forEach(function (c) {
        c.classList.remove('hl-target');
      });
    }

    document.querySelectorAll('.rel-list li[data-target]').forEach(function (li) {
      li.addEventListener('mouseenter', function () {
        clearArrow();
        var target = cardsById[li.getAttribute('data-target')];
        if (!target || target.dataset.hidden === "true") return;  // прихована пошуком

        sizeSvgToDocument();
        var liRect = li.getBoundingClientRect();
        var tgRect = target.getBoundingClientRect();
        var isPre = li.getAttribute('data-dir') === 'pre';

        // напрям стрілки відповідає реальному пререквізиту: для
        // пререквізиту вона веде ВІД цільової картки ДО поточної (той
        // предмет живить цей), для постреквізиту - навпаки, від
        // поточної картки ДО цільової
        var fromRect = isPre ? tgRect : liRect;
        var toRect = isPre ? liRect : tgRect;
        var fromGoingRight = toRect.left >= fromRect.left;
        var p1 = pagePoint(fromRect, fromGoingRight ? 'right' : 'left');
        var p2 = pagePoint(toRect, fromGoingRight ? 'left' : 'right');

        var midX = (p1.x + p2.x) / 2;
        var d = "M " + p1.x + " " + p1.y +
                " C " + midX + " " + p1.y + ", " + midX + " " + p2.y + ", " + p2.x + " " + p2.y;

        var path = document.createElementNS("http://www.w3.org/2000/svg", "path");
        path.setAttribute("d", d);
        path.setAttribute("class", "rel-arrow");
        path.setAttribute("marker-end", isPre ? "url(#arrow-pre)" : "url(#arrow-post)");
        path.setAttribute("stroke", isPre ? "#2f6fed" : "#e8590c");
        svg.appendChild(path);

        target.classList.add('hl-target');
      });
      li.addEventListener('mouseleave', clearArrow);
    });
  })();
