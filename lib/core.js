// Shared interaction primitives for all three portfolio directions.
// Magnetic, marquee, reveal-on-scroll, page transition, i18n.
// Exported as globals on window so each prototype can pick what it needs.
// Self-contained — no React required. Pure DOM.

(function () {
  // -------------------- MAGNETIC HOVER --------------------
  // For elements with data-magnetic="0.4" — strength 0..1.
  function initMagnetic() {
    if (matchMedia("(hover: none)").matches) return;
    document.querySelectorAll("[data-magnetic]").forEach((el) => {
      const strength = parseFloat(el.dataset.magnetic) || 0.3;
      let tx = 0, ty = 0, cx = 0, cy = 0, raf;
      // Rect is captured on mouseenter and reused across the mousemove
      // burst; refresh on scroll/resize. This avoids one forced layout
      // per pointer event on hover-magnetic elements.
      let rect = null;
      function refreshRect() { rect = el.getBoundingClientRect(); }
      function loop() {
        cx += (tx - cx) * 0.18;
        cy += (ty - cy) * 0.18;
        el.style.transform = `translate3d(${cx}px, ${cy}px, 0)`;
        if (Math.abs(tx - cx) < 0.1 && Math.abs(ty - cy) < 0.1) {
          cancelAnimationFrame(raf); raf = null;
        } else raf = requestAnimationFrame(loop);
      }
      el.addEventListener("mouseenter", refreshRect);
      el.addEventListener("mousemove", (e) => {
        if (!rect) refreshRect();
        const x = e.clientX - rect.left - rect.width / 2;
        const y = e.clientY - rect.top - rect.height / 2;
        tx = x * strength; ty = y * strength;
        if (!raf) raf = requestAnimationFrame(loop);
      });
      el.addEventListener("mouseleave", () => {
        tx = 0; ty = 0; rect = null;
        if (!raf) raf = requestAnimationFrame(loop);
      });
      window.addEventListener("scroll", () => { rect = null; }, { passive: true });
      window.addEventListener("resize", () => { rect = null; }, { passive: true });
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
    // Batched init: all style writes happen before the first layout read
    // (offsetWidth), and that read is deferred to an idle / rAF tick so it
    // doesn't fight with the page's initial paint. Eliminates the
    // ~1.9s combined forced reflow that Lighthouse flagged here.
    const items = [];
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
      // Batch all style writes via cssText — a single style invalidation
      // instead of six separate property assignments.
      el.style.cssText += ";overflow:hidden;white-space:nowrap;";
      const inlineStyles = "display:inline-block;will-change:transform;";
      inner.style.cssText = inlineStyles;
      clone.style.cssText = inlineStyles;
      el.appendChild(inner);
      el.appendChild(clone);
      items.push({ el, inner, clone, speed, reverse });
    });
    if (!items.length) return;

    // Defer all measurements to the next rAF so they happen AFTER the
    // browser has committed the layout for the writes above.
    const start = () => {
      items.forEach((item) => {
        item.w = item.inner.offsetWidth;
        item.x = 0;
        const measure = () => {
          // Guard: skip if element was removed from the DOM.
          if (!item.inner.isConnected) return;
          // Re-measure inside another rAF so the read doesn't race with
          // the browser's own style/layout work on the same frame.
          requestAnimationFrame(() => {
            if (!item.inner.isConnected) return;
            item.w = item.inner.offsetWidth;
          });
        };
        if ("ResizeObserver" in window) {
          const ro = new ResizeObserver(measure);
          ro.observe(item.inner);
          item.ro = ro;
        } else {
          window.addEventListener("resize", measure, { passive: true });
        }
      });
      function tick() {
        items.forEach((item) => {
          item.x -= item.reverse ? -item.speed : item.speed;
          if (item.w > 0 && Math.abs(item.x) >= item.w) item.x = 0;
          if (item.reverse && item.x >= 0) item.x = -item.w;
          const t = `translate3d(${item.x}px,0,0)`;
          item.inner.style.transform = t;
          item.clone.style.transform = t;
        });
        requestAnimationFrame(tick);
      }
      tick();
    };
    // requestIdleCallback when available — pushes the initial layout read
    // out of the critical render path entirely.
    if ("requestIdleCallback" in window) {
      requestIdleCallback(() => requestAnimationFrame(start), { timeout: 500 });
    } else {
      requestAnimationFrame(() => requestAnimationFrame(start));
    }
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
    initMagnetic,
    initReveal,
    initMarquee,
    pageTransition,
    initI18n,
  };
})();
