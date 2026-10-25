// QX: the tiny runner every figure on the site uses. Kit functions (translateAlong, lineOnTop...) are globals above.
const QX = (() => {
  const still = matchMedia("(prefers-reduced-motion: reduce)");
  const merge = (a, b) => {
    const out = { ...a };
    for (const key of ["lamps", "move", "dial", "text", "show", "cls"]) if (b[key]) out[key] = { ...(a[key] || {}), ...b[key] };
    out.say = b.say ?? "";
    out.lit = b.lit || [];
    out.ms = b.ms ?? 2600;
    out.fn = b.fn;
    return out;
  };
  const statesOf = (scenes, init = {}) => {
    const out = [];
    let s = merge({ lamps: {}, move: {}, dial: {}, text: {}, show: {}, cls: {} }, init);
    for (const sc of scenes) { s = merge(s, sc); out.push(s); }
    return out;
  };

  function figure(cfg) {
    const root = document.getElementById(cfg.id);
    if (!root) return;
    const svg = root.querySelector("svg");
    const P = cfg.P;
    const sayEl = root.querySelector("[data-say]");
    const stepEl = root.querySelector("[data-step]");
    const playBtn = root.querySelector('[data-act="play"]');
    const movers = {};
    root.querySelectorAll("[data-move]").forEach((el) => {
      const at = (el.dataset.at || "0,0,0").split(",").map(Number);
      movers[el.dataset.move] = { el, cur: at.slice(), to: at.slice() };
    });
    const dials = {};
    for (const [id, spec] of Object.entries(cfg.dials || {})) {
      const el = svg.querySelector(`[data-dial="${id}"]`);
      if (el) dials[id] = { el, spec, cur: spec.value, to: spec.value };
    }
    const hots = [...root.querySelectorAll("[data-hot]")];
    const labels = cfg.labels || {};
    let modeName = cfg.mode || Object.keys(cfg.modes)[0];
    let states = statesOf(cfg.modes[modeName], cfg.init);
    let index = 0, clock = 0, playing = !still.matches, visible = true, frame = 0, last = 0, peek = null;

    const lightUp = (ids) => {
      hots.forEach((el) => el.classList.toggle("lit", ids.includes(el.dataset.hot)));
      document.querySelectorAll(`[data-fig="${cfg.id}"][data-for]`).forEach((el) => el.classList.toggle("lit", ids.includes(el.dataset.for)));
    };
    function apply(jump) {
      const s = states[index];
      root.querySelectorAll("[data-lamp]").forEach((el) => { el.dataset.state = s.lamps[el.dataset.lamp] || "off"; });
      root.querySelectorAll("[data-show]").forEach((el) => { el.toggleAttribute("data-off", s.show[el.dataset.show] === false); });
      root.querySelectorAll("[data-cls]").forEach((el) => { el.dataset.state = s.cls[el.dataset.cls] || ""; });
      root.querySelectorAll("[data-text]").forEach((el) => { const t = s.text[el.dataset.text]; if (t !== undefined && el.textContent !== t) el.textContent = t; });
      for (const [id, m] of Object.entries(movers)) { const to = s.move[id]; if (to) m.to = to.slice(); if (jump) m.cur = m.to.slice(); }
      for (const [id, d] of Object.entries(dials)) { const to = s.dial[id]; if (to !== undefined) d.to = to; if (jump) d.cur = d.to; }
      if (!peek) { lightUp(s.lit); if (sayEl) sayEl.textContent = s.say; }
      if (stepEl) stepEl.textContent = `${index + 1} / ${states.length}`;
      root.querySelectorAll("[data-dot]").forEach((el, i) => el.classList.toggle("on", i === index));
      if (cfg.after) cfg.after(s, api);
      draw();
    }
    function draw() {
      for (const m of Object.values(movers)) m.el.setAttribute("transform", translateAlong(P, m.cur));
      for (const d of Object.values(dials)) {
        const { cx, cy, r, z, from, span } = d.spec;
        const a = from + span * d.cur;
        d.el.setAttribute("d", lineOnTop([cx - Math.sin(a) * 2.2, cy + Math.cos(a) * 2.2], [cx + Math.sin(a) * (r - 3), cy - Math.cos(a) * (r - 3)], z + 0.2, P));
      }
    }
    function tick(now) {
      const dt = last ? Math.min((now - last) / 1000, 1 / 20) : 1 / 60;
      last = now;
      const calm = still.matches;
      let moving = false;
      for (const m of Object.values(movers)) for (let i = 0; i < 3; i++) {
        const gap = m.to[i] - m.cur[i];
        if (Math.abs(gap) > 0.02) { m.cur[i] = calm ? m.to[i] : m.cur[i] + gap * (1 - Math.exp(-dt / (cfg.ease || 0.35))); moving = true; } else m.cur[i] = m.to[i];
      }
      for (const d of Object.values(dials)) {
        const gap = d.to - d.cur;
        if (Math.abs(gap) > 0.001) { d.cur = calm ? d.to : d.cur + gap * (1 - Math.exp(-dt / 0.5)); moving = true; } else d.cur = d.to;
      }
      const s = states[index];
      if (s.fn) s.fn(Math.min(1, clock / s.ms), api);
      draw();
      if (playing) { clock += dt * 1000; if (clock >= s.ms) go(index + 1); }
      frame = visible && (playing || moving || s.fn) ? requestAnimationFrame(tick) : 0;
    }
    const run = () => { if (!frame && visible) { last = 0; frame = requestAnimationFrame(tick); } };
    function go(i, jump = false) { index = (i + states.length) % states.length; clock = 0; apply(jump); run(); }
    function setPlaying(on) { playing = on; if (playBtn) { playBtn.setAttribute("aria-pressed", String(on)); playBtn.textContent = on ? "Pause" : "Play"; } run(); }
    const api = { svg, root, P, movers, dials, run: () => run(), current: () => states[index], setText: (id, t) => root.querySelectorAll(`[data-text="${id}"]`).forEach((el) => (el.textContent = t)), say: (t) => sayEl && (sayEl.textContent = t), draw };

    function peekAt(id) {
      peek = id;
      lightUp(id ? [id] : states[index].lit);
      if (sayEl) sayEl.textContent = id ? labels[id] || "" : states[index].say;
    }
    hots.forEach((el) => {
      const id = el.dataset.hot;
      el.addEventListener("pointerenter", (e) => { if (e.pointerType === "mouse") peekAt(id); });
      el.addEventListener("pointerleave", (e) => { if (e.pointerType === "mouse") peekAt(null); });
      el.addEventListener("click", () => {
        if (el.dataset.href) { location.href = el.dataset.href; return; }
        setPlaying(false); peekAt(id);
      });
    });
    document.querySelectorAll(`[data-fig="${cfg.id}"][data-for]`).forEach((el) => {
      const id = el.dataset.for;
      el.addEventListener("pointerenter", (e) => { if (e.pointerType === "mouse") peekAt(id); });
      el.addEventListener("pointerleave", (e) => { if (e.pointerType === "mouse") peekAt(null); });
      el.addEventListener("click", () => { setPlaying(false); peekAt(id); root.scrollIntoView({ block: "nearest", behavior: still.matches ? "auto" : "smooth" }); });
    });
    root.querySelectorAll("[data-act]").forEach((btn) => btn.addEventListener("click", () => {
      const act = btn.dataset.act;
      peek = null;
      if (act === "play") setPlaying(!playing);
      if (act === "next") { setPlaying(false); go(index + 1); }
      if (act === "prev") { setPlaying(false); go(index - 1); }
    }));
    root.querySelectorAll("[data-mode]").forEach((btn) => btn.addEventListener("click", () => {
      modeName = btn.dataset.mode;
      root.querySelectorAll("[data-mode]").forEach((b) => b.setAttribute("aria-pressed", String(b === btn)));
      states = statesOf(cfg.modes[modeName], cfg.init);
      buildDots(); peek = null; go(0, true);
    }));
    function buildDots() {
      const holder = root.querySelector("[data-dots]");
      if (!holder) return;
      holder.innerHTML = states.map((_, i) => `<button type="button" data-dot aria-label="Step ${i + 1}"></button>`).join("");
      holder.querySelectorAll("[data-dot]").forEach((b, i) => b.addEventListener("click", () => { peek = null; setPlaying(false); go(i); }));
    }
    buildDots();
    new IntersectionObserver((entries) => { visible = entries[entries.length - 1].isIntersecting; if (visible) run(); }, { rootMargin: "80px 0px" }).observe(root);
    if (cfg.setup) cfg.setup(api, { go: (i) => go(i), pause: () => setPlaying(false), states: () => states });
    setPlaying(playing);
    go(0, true);
    return api;
  }
  return { figure };
})();
