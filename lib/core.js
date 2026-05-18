// Shared interaction primitives for all three portfolio directions.
// Smooth scroll (lerp), custom cursor, magnetic, marquee, reveal-on-scroll.
// Exported as globals on window so each prototype can pick what it needs.
// Self-contained — no React required. Pure DOM.

(function () {
  // -------------------- SMOOTH SCROLL (Lenis-lite) --------------------
  // Lerped wheel scroll on document. Falls back to native on touch.
  function initSmoothScroll(opts = {}) {
    const easeFactor = opts.ease ?? 0.085;
    const isTouch = matchMedia("(hover: none)").matches;
    if (isTouch) return { destroy() {} };

    let target = window.scrollY;
    let current = window.scrollY;
    let rafId = null;
    let isRunning = false;

    document.documentElement.classList.add("ps-smooth");

    function onWheel(e) {
      e.preventDefault();
      target += e.deltaY;
      const max = document.documentElement.scrollHeight - window.innerHeight;
      target = Math.max(0, Math.min(max, target));
      if (!isRunning) raf();
    }

    function onKey(e) {
      const max = document.documentElement.scrollHeight - window.innerHeight;
      const step = window.innerHeight * 0.9;
      if (e.key === "ArrowDown" || e.key === "PageDown") {
        target = Math.min(max, target + step); e.preventDefault();
      } else if (e.key === "ArrowUp" || e.key === "PageUp") {
        target = Math.max(0, target - step); e.preventDefault();
      } else if (e.key === "Home") { target = 0; e.preventDefault(); }
      else if (e.key === "End") { target = max; e.preventDefault(); }
      if (!isRunning) raf();
    }

    function raf() {
      isRunning = true;
      current += (target - current) * easeFactor;
      if (Math.abs(target - current) < 0.4) {
        current = target;
        isRunning = false;
      }
      window.scrollTo(0, current);
      window.dispatchEvent(new CustomEvent("ps:scroll", { detail: { y: current, target } }));
      if (isRunning) rafId = requestAnimationFrame(raf);
    }

    window.addEventListener("wheel", onWheel, { passive: false });
    window.addEventListener("keydown", onKey);
    window.addEventListener("resize", () => {
      const max = document.documentElement.scrollHeight - window.innerHeight;
      target = Math.min(target, max);
    });

    // Allow programmatic scroll-to via anchor clicks
    document.addEventListener("click", (e) => {
      const a = e.target.closest("a[href^='#']");
      if (!a) return;
      const id = a.getAttribute("href").slice(1);
      const el = document.getElementById(id);
      if (!el) return;
      e.preventDefault();
      const rect = el.getBoundingClientRect();
      target = Math.max(0, Math.min(
        document.documentElement.scrollHeight - window.innerHeight,
        target + rect.top - 20
      ));
      if (!isRunning) raf();
    });

    return {
      destroy() {
        window.removeEventListener("wheel", onWheel);
        window.removeEventListener("keydown", onKey);
        cancelAnimationFrame(rafId);
      },
    };
  }

  // -------------------- CUSTOM CURSOR --------------------
  // Two layered dots: an inner one that snaps to pointer, an outer ring that
  // trails with a soft lerp. Both can be expanded/labelled via data attrs on
  // hovered elements.
  //   data-cursor="view" → outer ring fills + shows label
  //   data-cursor="drag"
  //   data-cursor-text="anything"
  function initCursor(opts = {}) {
    if (matchMedia("(hover: none)").matches) return { destroy() {} };

    const root = document.createElement("div");
    root.className = "ps-cursor";
    root.innerHTML = `
      <div class="ps-cursor-ring" aria-hidden="true">
        <span class="ps-cursor-label"></span>
      </div>
      <div class="ps-cursor-dot" aria-hidden="true"></div>
    `;
    document.body.appendChild(root);

    const ring = root.querySelector(".ps-cursor-ring");
    const dot = root.querySelector(".ps-cursor-dot");
    const label = root.querySelector(".ps-cursor-label");

    let mx = window.innerWidth / 2, my = window.innerHeight / 2;
    let rx = mx, ry = my;
    let hover = null;

    function move(e) {
      mx = e.clientX; my = e.clientY;
      dot.style.transform = `translate3d(${mx}px, ${my}px, 0)`;
    }
    function over(e) {
      const t = e.target.closest("[data-cursor]");
      if (t && t !== hover) {
        hover = t;
        const kind = t.dataset.cursor;
        const text = t.dataset.cursorText || "";
        root.dataset.state = kind;
        label.textContent = text;
      } else if (!t && hover) {
        hover = null;
        root.dataset.state = "";
        label.textContent = "";
      }
    }
    function loop() {
      rx += (mx - rx) * 0.18;
      ry += (my - ry) * 0.18;
      ring.style.transform = `translate3d(${rx}px, ${ry}px, 0)`;
      requestAnimationFrame(loop);
    }
    loop();

    window.addEventListener("mousemove", move);
    window.addEventListener("mouseover", over);
    document.addEventListener("mouseleave", () => { root.style.opacity = "0"; });
    document.addEventListener("mouseenter", () => { root.style.opacity = "1"; });
    window.addEventListener("mousedown", () => root.classList.add("is-down"));
    window.addEventListener("mouseup", () => root.classList.remove("is-down"));

    return { destroy() { root.remove(); } };
  }

  // -------------------- MAGNETIC HOVER --------------------
  // For elements with data-magnetic="0.4" — strength 0..1.
  function initMagnetic() {
    if (matchMedia("(hover: none)").matches) return;
    document.querySelectorAll("[data-magnetic]").forEach((el) => {
      const strength = parseFloat(el.dataset.magnetic) || 0.3;
      let tx = 0, ty = 0, cx = 0, cy = 0, raf;
      function loop() {
        cx += (tx - cx) * 0.18;
        cy += (ty - cy) * 0.18;
        el.style.transform = `translate3d(${cx}px, ${cy}px, 0)`;
        if (Math.abs(tx - cx) < 0.1 && Math.abs(ty - cy) < 0.1) {
          cancelAnimationFrame(raf); raf = null;
        } else raf = requestAnimationFrame(loop);
      }
      el.addEventListener("mousemove", (e) => {
        const r = el.getBoundingClientRect();
        const x = e.clientX - r.left - r.width / 2;
        const y = e.clientY - r.top - r.height / 2;
        tx = x * strength; ty = y * strength;
        if (!raf) raf = requestAnimationFrame(loop);
      });
      el.addEventListener("mouseleave", () => {
        tx = 0; ty = 0;
        if (!raf) raf = requestAnimationFrame(loop);
      });
    });
  }

  // -------------------- REVEAL ON SCROLL --------------------
  // Adds .is-in to any [data-reveal] when it enters the viewport.
  // Supports data-reveal-delay (ms).
  function initReveal(rootEl = document) {
    const io = new IntersectionObserver(
      (entries) => {
        entries.forEach((entry) => {
          if (entry.isIntersecting) {
            const d = entry.target.dataset.revealDelay || 0;
            setTimeout(() => entry.target.classList.add("is-in"), +d);
            io.unobserve(entry.target);
          }
        });
      },
      { threshold: 0.12, rootMargin: "0px 0px -8% 0px" }
    );
    rootEl.querySelectorAll("[data-reveal]").forEach((el) => io.observe(el));
    return io;
  }

  // -------------------- MARQUEE --------------------
  // <div data-marquee data-speed="0.4">content</div>
  // Duplicates content to seamless-loop and translates via rAF.
  function initMarquee() {
    document.querySelectorAll("[data-marquee]").forEach((el) => {
      if (el.dataset.psMarqueeInited) return;
      el.dataset.psMarqueeInited = "1";
      const speed = parseFloat(el.dataset.speed) || 0.4;
      const reverse = el.dataset.reverse === "1";
      const inner = document.createElement("div");
      inner.className = "ps-marquee-inner";
      while (el.firstChild) inner.appendChild(el.firstChild);
      const clone = inner.cloneNode(true);
      clone.setAttribute("aria-hidden", "true");
      el.appendChild(inner);
      el.appendChild(clone);
      el.style.overflow = "hidden";
      el.style.whiteSpace = "nowrap";
      inner.style.display = "inline-block";
      clone.style.display = "inline-block";
      let x = 0;
      function tick() {
        x -= reverse ? -speed : speed;
        const w = inner.offsetWidth;
        if (w > 0 && Math.abs(x) >= w) x = 0;
        if (reverse && x >= 0) x = -w;
        inner.style.transform = clone.style.transform = `translate3d(${x}px,0,0)`;
        requestAnimationFrame(tick);
      }
      tick();
    });
  }

  // -------------------- PAGE TRANSITION --------------------
  // Curtain wipe used for fake nav (clicking a project).
  function pageTransition({ color = "#0a0a0a", text = "" } = {}) {
    return new Promise((resolve) => {
      const layer = document.createElement("div");
      layer.className = "ps-curtain";
      layer.style.background = color;
      layer.innerHTML = `<span class="ps-curtain-text">${text}</span>`;
      document.body.appendChild(layer);
      requestAnimationFrame(() => layer.classList.add("in"));
      setTimeout(() => {
        resolve();
        setTimeout(() => {
          layer.classList.add("out");
          setTimeout(() => layer.remove(), 700);
        }, 200);
      }, 700);
    });
  }

  // -------------------- LANG TOGGLE --------------------
  // Updates [data-i18n="path.to.key"] from PORTFOLIO_CONTENT[lang].
  // For headline arrays etc., expects matching shape.
  function initI18n(lang = "en") {
    // The page's <html lang> is set by the server-side render. If it
    // disagrees with the caller's argument, the static markup wins —
    // this prevents JS hydration from flipping a /he/ page back to EN
    // on first paint. A subsequent client-side toggle could re-call
    // initI18n with a different lang, but that's a future feature; for
    // now every language has its own URL, so the static lang is canon.
    const staticLang = document.documentElement.lang;
    if (staticLang && staticLang !== lang) lang = staticLang;

    const get = (obj, path) => path.split(".").reduce((o, k) => (o ? o[k] : null), obj);
    function apply(lang) {
      const data = window.PORTFOLIO_CONTENT[lang];
      document.documentElement.lang = lang;
      document.documentElement.dir = lang === "he" ? "rtl" : "ltr";
      document.body.dataset.lang = lang;
      document.querySelectorAll("[data-i18n]").forEach((el) => {
        const v = get(data, el.dataset.i18n);
        if (typeof v === "string") el.textContent = v;
      });
      window.dispatchEvent(new CustomEvent("ps:lang", { detail: lang }));
    }
    apply(lang);
    return { apply };
  }

  // Expose
  window.PS = {
    initSmoothScroll,
    initCursor,
    initMagnetic,
    initReveal,
    initMarquee,
    pageTransition,
    initI18n,
  };
})();
