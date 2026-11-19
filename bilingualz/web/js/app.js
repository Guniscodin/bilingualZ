/* Application state and actions. */
(function () {
  const BZ = (window.BZ = window.BZ || {});
  const LOW_CONFIDENCE = 0.55;

  const state = { doc: null, labels: {}, index: 0 };
  let progressTimer = null;

  const $ = (id) => document.getElementById(id);
  const clamp = (value, low, high) => Math.max(low, Math.min(high, value));

  const SAMPLE = {
    en: `In 1755, an earthquake destroyed most of Lisbon.

The king's minister, the Marquis of Pombal, ordered the city rebuilt from scratch.

His plan produced wide avenues, a grid of streets, and the first anti-seismic buildings in Europe.

The Baixa district still follows that grid today.`,
    pt: `Em 1755, um terramoto destruiu grande parte de Lisboa.

O ministro do rei, o Marquês de Pombal, ordenou a reconstrução da cidade de raiz.

O seu plano produziu avenidas largas, uma grelha de ruas e os primeiros edifícios antissísmicos da Europa.

O bairro da Baixa segue ainda hoje essa grelha.`,
  };

  /* ------------------------------------------------------------- boot ---- */
  document.addEventListener("DOMContentLoaded", boot);

  async function boot() {
    wire();

    const info = await BZ.api.translatorInfo().catch(() => null);
    describeTranslator(info);

    const docs = await BZ.api.list().catch(() => []);
    if (docs && docs.length) {
      try {
        await open(docs[0].id);
      } catch (_error) {
        showWelcome();
      }
    } else {
      showWelcome();
    }
  }

  function showWelcome() {
    state.doc = null;
    $("reader").hidden = true;
    $("welcome").hidden = false;
    $("docTitle").textContent = "No document open";
    $("counter").textContent = "";
    $("statusText").textContent = "";
  }

  /* ------------------------------------------------------------ state ---- */
  function apply(response) {
    const doc = response.doc;
    state.doc = doc;
    state.labels = response.labels || state.labels || {};
    state.index = clamp(state.index, 0, Math.max(doc.pairs.length - 1, 0));

    $("docTitle").textContent = doc.title;
    $("labelEn").textContent = state.labels.en || "English";
    $("labelPt").textContent = state.labels.pt || "Português";
    $("metaEn").textContent = doc.en.length + " paragraphs";
    $("metaPt").textContent = doc.pt.length + " paragraphs";
    $("reader").hidden = false;
    $("welcome").hidden = true;

    BZ.render.mount(doc);
    select(state.index, { scroll: true, silent: true });
    updateStatus();
  }

  /* Re-render pairs without rebuilding the paragraph nodes (text unchanged). */
  function refresh(response) {
    state.doc = response.doc;
    state.labels = response.labels || state.labels;
    state.index = clamp(state.index, 0, Math.max(response.doc.pairs.length - 1, 0));
    BZ.render.rebuild();
    updateCounter();
    updateStatus();
    BZ.render.scrollTo(state.index);
  }

  async function open(id) {
    const response = await BZ.api.get(id);
    closeAll();
    apply(response);
  }

  async function openMostRecent() {
    const docs = await BZ.api.list().catch(() => []);
    if (docs.length) {
      await open(docs[0].id);
    } else {
      showWelcome();
    }
  }

  /* --------------------------------------------------------- navigation -- */
  function select(index, options) {
    const opts = options || {};
    if (!state.doc || !state.doc.pairs.length) return;

    const next = clamp(index, 0, state.doc.pairs.length - 1);
    const previous = state.index;
    state.index = next;

    BZ.render.paint(previous, next);
    updateCounter();

    if (opts.scroll !== false) BZ.render.scrollTo(next);
    if (!opts.silent) queueProgress(next);
  }

  function next() {
    select(state.index + 1);
  }

  function prev() {
    select(state.index - 1);
  }

  function first() {
    select(0);
  }

  function last() {
    if (state.doc) select(state.doc.pairs.length - 1);
  }

  function selectSegment(side, index) {
    if (!state.doc) return;
    const found = state.doc.pairs.findIndex((pair) => pair[side].includes(index));
    if (found >= 0) select(found);
  }

  /* ------------------------------------------------------------- repair -- */
  async function nudge(delta) {
    if (!state.doc) return;
    if (state.doc.mode === "translate") {
      setTransientStatus("Machine-aligned document - nothing to nudge.");
      return;
    }
    const response = await BZ.api.nudge(state.doc.id, state.index, delta).catch(showError);
    if (response) refresh(response);
  }

  async function lock() {
    if (!state.doc || state.doc.mode === "translate") return;
    const response = await BZ.api.anchor(state.doc.id, state.index).catch(showError);
    if (response) refresh(response);
  }

  function toggleFocus() {
    document.body.classList.toggle("focus-mode");
  }

  /* ----------------------------------------------------------- progress -- */
  function queueProgress(index) {
    if (!state.doc) return;
    clearTimeout(progressTimer);
    progressTimer = setTimeout(() => {
      if (!state.doc) return;
      BZ.api.saveProgress(state.doc.id, index).catch(() => {});
    }, 400);
  }

  function updateCounter() {
    if (!state.doc) return;
    $("counter").textContent = state.index + 1 + " / " + state.doc.pairs.length;
  }

  function updateStatus() {
    const doc = state.doc;
    if (!doc) {
      $("statusText").textContent = "";
      return;
    }
    const unsure = doc.pairs.filter((pair) => pair.score < LOW_CONFIDENCE).length;
    const locked = (doc.forced || []).length;
    const bits = [];
    if (doc.mode === "translate") bits.push("machine aligned");
    if (unsure) bits.push(unsure + " to check");
    if (locked) bits.push(locked + " locked");
    $("statusText").textContent = bits.join("  ·  ");
  }

  let statusTimer = null;
  function setTransientStatus(message) {
    const node = $("statusText");
    node.textContent = message;
    clearTimeout(statusTimer);
    statusTimer = setTimeout(updateStatus, 2600);
  }

  function showError(error) {
    const message = error && error.message ? error.message : String(error);
    console.error(error);
    setTransientStatus(message);
    alert(message);
    return null;
  }

  /* ------------------------------------------------------------ dialogs -- */
  function openNew() {
    $("newOverlay").hidden = false;
    setTimeout(() => $("enText").focus(), 40);
  }

  async function openLibrary() {
    await renderLibrary();
    $("libraryOverlay").hidden = false;
  }

  function closeAll() {
    document.querySelectorAll(".overlay").forEach((overlay) => {
      overlay.hidden = true;
    });
  }

  async function renderLibrary() {
    const list = $("docList");
    const docs = await BZ.api.list().catch(() => []);
    list.replaceChildren();

    if (!docs.length) {
      const note = document.createElement("div");
      note.className = "empty-note";
      note.textContent = "Nothing here yet. Create a document first.";
      list.appendChild(note);
      return;
    }

    docs.forEach((entry) => {
      const row = document.createElement("div");
      row.className = "docrow";

      const name = document.createElement("div");
      name.className = "name";
      name.textContent = entry.title;

      const badge = document.createElement("span");
      badge.className = "badge";
      badge.textContent = entry.mode === "translate" ? "mt" : "dual";

      const pct = document.createElement("span");
      pct.className = "pct";
      pct.textContent = entry.total
        ? Math.round(((entry.progress + 1) / entry.total) * 100) + "%"
        : "0%";

      row.append(name, badge, pct);
      row.addEventListener("click", () => {
        open(entry.id).catch(showError);
      });
      list.appendChild(row);
    });
  }

  function setProgress(fraction, label) {
    const box = $("newProgress");
    if (fraction === null || fraction === undefined) {
      box.hidden = true;
      return;
    }
    box.hidden = false;
    box.querySelector("i").style.width = Math.round(clamp(fraction, 0, 1) * 100) + "%";
    $("newProgressText").textContent = label || "working";
  }

  /* Called from Python via window.evaluate_js during translation. */
  BZ.onProgress = (fraction, label) => setProgress(fraction, label);

  async function create() {
    const button = $("btnCreate");
    if (button.disabled) return;

    const tab = document.querySelector(".tab.active").dataset.tab;
    button.disabled = true;
    setProgress(0, "working");

    try {
      let response;
      if (tab === "parallel") {
        response = await BZ.api.createParallel({
          title: $("newTitle").value.trim(),
          en: $("enText").value,
          pt: $("ptText").value,
        });
      } else {
        response = await BZ.api.createTranslated({
          title: $("trTitle").value.trim(),
          source_lang: $("trSource").value,
          text: $("trText").value,
        });
      }
      closeAll();
      state.index = 0;
      apply(response);
    } catch (error) {
      showError(error);
    } finally {
      button.disabled = false;
      setProgress(null);
    }
  }

  function describeTranslator(info) {
    const note = $("trNote");
    if (!note) return;
    if (!info) {
      note.textContent = "Translation engine unavailable.";
      return;
    }
    const have = info.available || {};
    const parts = [];
    if (have.argos) parts.push("Argos (offline)");
    if (have.azure) parts.push("Azure (free tier key found)");
    note.textContent = parts.length
      ? "Engine: " + parts.join("  ·  ")
      : "No translation engine installed. Install argostranslate, or set " +
        "BILINGUALZ_AZURE_KEY to use the Azure free tier.";
  }

  /* --------------------------------------------------------------- wire -- */
  function wire() {
    $("btnNew").addEventListener("click", openNew);
    $("btnWelcomeNew").addEventListener("click", openNew);
    $("btnLibrary").addEventListener("click", () => openLibrary().catch(showError));
    $("btnWelcomeLibrary").addEventListener("click", () => openLibrary().catch(showError));
    $("btnCreate").addEventListener("click", create);

    document.querySelectorAll("[data-close]").forEach((node) => {
      node.addEventListener("click", closeAll);
    });

    document.querySelectorAll(".overlay").forEach((overlay) => {
      overlay.addEventListener("mousedown", (event) => {
        if (event.target === overlay) closeAll();
      });
    });

    document.querySelectorAll(".tab").forEach((tab) => {
      tab.addEventListener("click", () => {
        document.querySelectorAll(".tab").forEach((other) => {
          other.classList.toggle("active", other === tab);
        });
        const name = tab.dataset.tab;
        $("tabParallel").hidden = name !== "parallel";
        $("tabTranslate").hidden = name !== "translate";
        $("btnCreate").textContent = name === "parallel" ? "Align" : "Translate";
      });
    });

    $("btnSample").addEventListener("click", () => {
      $("enText").value = SAMPLE.en;
      $("ptText").value = SAMPLE.pt;
      $("newTitle").value = "The 1755 Lisbon earthquake";
      document.querySelector('.tab[data-tab="parallel"]').click();
    });
  }

  /* --------------------------------------------------------------- api -- */
  BZ.app = {
    state: () => state,
    open,
    openMostRecent,
    next,
    prev,
    first,
    last,
    select,
    selectSegment,
    nudge,
    lock,
    toggleFocus,
    openNew,
    openLibrary,
    closeAll,
  };
})();
