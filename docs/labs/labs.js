// Каталог лабораторних робіт. Щоб додати лабу — додайте об'єкт у масив `items` потрібного розділу.
// file: шлях до аплету (HTML) відносно папки labs/
window.LABS = [
  {
    id: "mechanics", title: "Механіка", icon: "⚙️",
    items: [
      { id: "collision", title: "Зіткнення куль",
        desc: "Пружне та непружне зіткнення, закони збереження імпульсу й енергії.",
        file: "applets/mechanics/LabCollision.html", format: ["очна", "заочна"] },
    ],
  },
  { id: "thermodynamics", title: "Термодинаміка та молекулярна фізика", icon: "🌡️", items: [] },
  { id: "electromagnetism", title: "Електрика та магнетизм", icon: "⚡",
    items: [
      { id: "battery-vac", title: "ВАХ джерела ЕРС",
        desc: "Вольт-амперна характеристика джерела, ЕРС і внутрішній опір.",
        file: "applets/electromagnetism/lab_bench_battery.html", format: ["очна", "заочна"] },
      { id: "ac-lab", title: "Змінний струм: віртуальний практикум (роботи 1–3)",
        desc: "Віртуальний практикум зі змінного струму.",
        file: "applets/electromagnetism/ac_lab.html", format: ["очна", "заочна"] },
    ]  },
  { id: "optics", title: "Оптика", icon: "🔭", items: [] },
  { id: "atomic", title: "Атомна та ядерна фізика", icon: "⚛️", items: [] },
];
