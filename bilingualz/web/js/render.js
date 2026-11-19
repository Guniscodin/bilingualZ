/* DOM rendering: paragraphs in, underline state out. */
(function () {
  const BZ = (window.BZ = window.BZ || {});
  const LOW_CONFIDENCE = 0.55;

  const elements = { en: [], pt: [] };
  let pairMap = { en: [], pt: [] };
  let doc = null;

  function makeSegment(text, side, index, parent) {
    const node = document.createElement("p");
    node.className = "seg";
    node.dataset.side = side;
    node.dataset.index = String(index);

    const span = document.createElement("span");
    span.className = "text";
    span.textContent = text;
    node.appendChild(span);

    node.addEventListener("click", () => BZ.app.selectSegment(side, index));
    parent.appendChild(node);
    return node;
  }

  function mount(nextDoc) {
    doc = nextDoc;
    const bodyEn = document.getElementById("bodyEn");
    const bodyPt = document.getElementById("bodyPt");

    bodyEn.replaceChildren();
    bodyPt.replaceChildren();

    elements.en = doc.en.map((text, i) => makeSegment(text, "en", i, bodyEn));
    elements.pt = doc.pt.map((text, i) => makeSegment(text, "pt", i, bodyPt));

    rebuild();
  }

  /* Rebuild the pair -> element mapping. Needed after the engine re-aligns. */
  function rebuild() {
    if (!doc) return;
    pairMap = {
      en: doc.pairs.map((p) => p.en.map((i) => elements.en[i]).filter(Boolean)),
      pt: doc.pairs.map((p) => p.pt.map((i) => elements.pt[i]).filter(Boolean)),
    };

    for (const side of ["en", "pt"]) {
      for (const node of elements[side]) {
        node.classList.remove("lowconf", "active", "visited", "primary", "ghost");
      }
    }

    doc.pairs.forEach((pair) => {
      if (pair.score >= LOW_CONFIDENCE) return;
      pair.en.forEach((i) => elements.en[i] && elements.en[i].classList.add("lowconf"));
      pair.pt.forEach((j) => elements.pt[j] && elements.pt[j].classList.add("lowconf"));
    });

    paint(-1, BZ.app.state().index);
  }

  function paint(_previous, current) {
    if (!doc) return;
    doc.pairs.forEach((pair, index) => {
      const state = index < current ? "visited" : index === current ? "active" : "";
      for (const side of ["en", "pt"]) {
        const nodes = pairMap[side][index] || [];
        nodes.forEach((node, position) => {
          node.classList.toggle("active", state === "active");
          node.classList.toggle("visited", state === "visited");
          node.classList.toggle("ghost", state === "active" && position > 0);
        });
      }
    });
  }

  function scrollTo(index) {
    const target = (pairMap.en[index] || [])[0];
    if (target) target.scrollIntoView({ block: "center", behavior: "smooth" });
    const mirror = (pairMap.pt[index] || [])[0];
    if (mirror) mirror.scrollIntoView({ block: "center", behavior: "smooth" });
  }

  BZ.render = { mount, rebuild, paint, scrollTo };
})();
