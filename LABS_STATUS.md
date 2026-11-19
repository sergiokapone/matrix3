# Віртуальні лабораторні — статус (2026-11-11)

## Що працює
- Сторінка на сайті кафедри: https://apd.ipt.kpi.ua/for_stud/virtualni-laboratorni-roboti/
  - WordPress page id **11694**, батько — «Студенту» (page id **111**), опублікована.
  - Пункт меню `main-ua` id **11695** (батько — пункт меню «Студенту», id 123).
  - Вміст: банер `wp-content/uploads/2026/11/VirtualLab.jpg`, вступ, iframe на GitHub Pages з параметром `?v=<timestamp>` (скидання кешу), скрипт автовисоти.
- Каталог і аплети хостяться на GitHub Pages: https://sergiokapone.github.io/matrix3/labs/ (джерело — `docs/labs/`).

## Структура `docs/labs/`
- `index.html` — вкладки розділів + картки (кнопка «Відкрити на весь екран» → аплет у новій вкладці; «переглянути тут» → `lab.html`).
- `lab.html` — перегляд лаби на всю ширину, кнопки «окрема сторінка» / «весь екран».
- `labs.js` — **каталог лаб** (єдине місце, де додаються лаби).
- `labs.css`, `embed.js` (автовисота iframe).
- `applets/<розділ>/` — файли аплетів.

## Лаби
| Розділ | Лаба | Файл |
|---|---|---|
| Механіка | Зіткнення куль | applets/mechanics/LabCollision.html |
| Електрика та магнетизм | ВАХ джерела ЕРС | applets/electromagnetism/lab_bench_battery.html |
| Електрика та магнетизм | Змінний струм (роботи 1–3) | applets/electromagnetism/ac_lab.html |
| Термодинаміка / Оптика / Атомна фізика | — порожньо — | — |

Джерела: `ForKairo/MechEngLab/LabCollision/`, `ElMag/ElMagConspect/docs/applets/` (+ `assets/theme.js`, `panel-toggle.js`).

## Як додати лабу
1. Скопіювати аплет (і його `assets/`, якщо є) у `docs/labs/applets/<розділ>/`.
2. Додати запис у `docs/labs/labs.js`.
3. `git add docs/labs && git commit && git push` — сторінка на сайті оновиться сама.
4. Користувачам може знадобитись Ctrl+F5 (кеш). Для нових відвідувачів оновити `?v=` в iframe: скрипт у scratchpad `update_page.py` (оновлює page 11694 через `core/wordpress_client.py`, креденшіали з `.env`).

## Відкрите / ідеї
- Порожні розділи: термодинаміка, оптика, атомна фізика — чекають на аплети.
- Описи лаб у `labs.js` складені за назвами — перевірити.
- Усі лаби позначені «очна/заочна» — уточнити.
- Логотип «Hueman» на банері — перевірити, чи доречний.
- Закомічено: `docs/labs`, `docs/index.html`. Незакомічені зміни в `Scheme/` і `docs/requisites_bachelor_2026_ua.html` — не мої.
