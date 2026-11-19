/* Thin wrapper around the pywebview bridge.
 *
 * If the page is opened in a normal browser (no Python behind it) every call
 * falls through to an in-memory mock so the UI can be developed and inspected
 * without launching the desktop app.
 */
(function () {
  const BZ = (window.BZ = window.BZ || {});

  function bridge() {
    return window.pywebview && window.pywebview.api ? window.pywebview.api : null;
  }

  function bridgeReady() {
    if (bridge()) return Promise.resolve();
    return new Promise((resolve) => {
      let settled = false;
      const done = () => {
        if (!settled) {
          settled = true;
          resolve();
        }
      };
      window.addEventListener("pywebviewready", done, { once: true });
      const started = Date.now();
      const poll = setInterval(() => {
        if (bridge() || Date.now() - started > 2500) {
          clearInterval(poll);
          done();
        }
      }, 50);
    });
  }

  async function call(name, ...args) {
    await bridgeReady();
    const api = bridge();
    if (api && typeof api[name] === "function") {
      return api[name](...args);
    }
    if (MOCK[name]) return MOCK[name](...args);
    throw new Error("No bridge for " + name);
  }

  /* ------------------------------------------------------------ mock ---- */
  const mockDocs = new Map();

  function splitParagraphs(text) {
    const normalised = (text || "").replace(/\r\n?/g, "\n").trim();
    let blocks = normalised.split(/\n\s*\n/).map((b) => b.replace(/\s+/g, " ").trim());
    blocks = blocks.filter(Boolean);
    if (blocks.length <= 1) {
      const lines = normalised.split("\n").map((l) => l.trim()).filter(Boolean);
      if (lines.length > 1) blocks = lines;
    }
    return blocks;
  }

  function mockPayload(doc) {
    const labels = { en: "English", pt: "Português" };
    if (doc.mode === "translate") {
      labels[doc.source_lang === "en" ? "pt" : "en"] += " - machine";
    }
    return { doc, labels };
  }

  const MOCK = {
    async ping() {
      return { ok: true, version: "mock", home: "(browser mock)" };
    },
    async translator_info() {
      return { name: "mock", available: { argos: false, azure: false } };
    },
    async list_documents() {
      return Array.from(mockDocs.values()).map((d) => ({
        id: d.id,
        title: d.title,
        mode: d.mode,
        total: d.pairs.length,
        progress: d.progress,
        created_at: d.created_at,
      }));
    },
    async get_document(id) {
      const doc = mockDocs.get(id);
      if (!doc) throw new Error("Unknown document " + id);
      return mockPayload(doc);
    },
    async delete_document(id) {
      return { deleted: mockDocs.delete(id) };
    },
    async create_parallel(payload) {
      const en = splitParagraphs(payload.en);
      const pt = splitParagraphs(payload.pt);
      if (!en.length || !pt.length) throw new Error("Both sides need some text.");
      const count = Math.max(en.length, pt.length);
      const pairs = [];
      for (let i = 0; i < count; i++) {
        pairs.push({
          en: i < en.length ? [i] : [],
          pt: i < pt.length ? [i] : [],
          score: 0.94,
        });
      }
      const doc = {
        id: "mock-" + mockDocs.size,
        title: (payload.title || en[0] || "Sample").slice(0, 90),
        mode: "parallel",
        en,
        pt,
        pairs,
        forced: [],
        progress: 0,
        source_lang: "en",
        created_at: new Date().toISOString(),
      };
      mockDocs.set(doc.id, doc);
      return mockPayload(doc);
    },
    async create_translated(payload) {
      const segs = splitParagraphs(payload.text);
      if (!segs.length) throw new Error("Nothing to translate.");
      const source = payload.source_lang === "en" ? "en" : "pt";
      const target = source === "en" ? "pt" : "en";
      const translated = segs.map((s) => "[" + target + "] " + s);
      const doc = {
        id: "mock-" + mockDocs.size,
        title: (payload.title || segs[0] || "Sample").slice(0, 90),
        mode: "translate",
        en: source === "en" ? segs : translated,
        pt: source === "pt" ? segs : translated,
        pairs: segs.map((_, i) => ({ en: [i], pt: [i], score: 1.0 })),
        forced: [],
        progress: 0,
        source_lang: source,
        created_at: new Date().toISOString(),
      };
      mockDocs.set(doc.id, doc);
      return mockPayload(doc);
    },
    async save_progress(id, index) {
      const doc = mockDocs.get(id);
      if (doc) doc.progress = index;
      return { progress: index };
    },
    async nudge(id, index, delta) {
      const doc = mockDocs.get(id);
      if (!doc) throw new Error("Unknown document");
      const pair = doc.pairs[index];
      if (pair && pair.pt.length) {
        pair.score = 1.0;
        doc.forced.push([pair.en[0], Math.max(0, pair.pt[0] + delta)]);
        void doc.forced;
      }
      return mockPayload(doc);
    },
    async add_anchor(id, index) {
      const doc = mockDocs.get(id);
      if (doc && doc.pairs[index]) doc.pairs[index].score = 1.0;
      return mockPayload(doc);
    },
    async clear_anchors(id) {
      const doc = mockDocs.get(id);
      if (doc) doc.forced = [];
      return mockPayload(doc);
    },
  };

  BZ.api = {
    isMock: () => !bridge(),
    ping: () => call("ping"),
    translatorInfo: () => call("translator_info"),
    list: () => call("list_documents"),
    get: (id) => call("get_document", id),
    remove: (id) => call("delete_document", id),
    createParallel: (payload) => call("create_parallel", payload),
    createTranslated: (payload) => call("create_translated", payload),
    saveProgress: (id, index) => call("save_progress", id, index),
    nudge: (id, index, delta) => call("nudge", id, index, delta),
    anchor: (id, index) => call("add_anchor", id, index),
    clearAnchors: (id) => call("clear_anchors", id),
  };
})();
