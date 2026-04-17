// Lionpoint Partners — interactions

(() => {
  const body = document.body;
  const qs = (s, r = document) => r.querySelector(s);
  const qsa = (s, r = document) => Array.from(r.querySelectorAll(s));

  /* ---------- Year stamp ---------- */
  const yr = qs("#yr");
  if (yr) yr.textContent = String(new Date().getFullYear());

  /* ---------- Clock in hero meta ---------- */
  const clock = qs("#clock");
  if (clock) {
    const tick = () => {
      const now = new Date();
      const t = now.toLocaleTimeString("en-US", {
        hour: "2-digit",
        minute: "2-digit",
        hour12: false,
        timeZone: "America/New_York",
      });
      clock.textContent = `NY ${t}`;
    };
    tick();
    setInterval(tick, 15000);
  }

  /* ---------- Custom cursor ---------- */
  const cursor = qs(".cursor");
  if (cursor && window.matchMedia("(hover: hover)").matches) {
    let tx = 0, ty = 0, cx = 0, cy = 0;
    window.addEventListener("mousemove", (e) => {
      tx = e.clientX;
      ty = e.clientY;
    });
    const loop = () => {
      cx += (tx - cx) * 0.22;
      cy += (ty - cy) * 0.22;
      cursor.style.transform = `translate(${cx}px, ${cy}px) translate(-50%, -50%)`;
      requestAnimationFrame(loop);
    };
    loop();

    const hoverables = "a, button, .case, .service, .split-card, .cta-box, .insight, .member";
    qsa(hoverables).forEach((el) => {
      el.addEventListener("mouseenter", () => cursor.classList.add("is-hover"));
      el.addEventListener("mouseleave", () => cursor.classList.remove("is-hover"));
    });
  }

  /* ---------- Reveal on scroll ---------- */
  const revealTargets = [
    ".section-head",
    ".service",
    ".split-card",
    ".stat",
    ".case",
    ".insight",
    ".member",
    ".cta-box",
    ".quote blockquote",
  ];
  qsa(revealTargets.join(",")).forEach((el) => el.classList.add("reveal"));

  const heroTitle = qs(".hero-title");
  if (heroTitle) heroTitle.classList.add("reveal-line");

  const io = new IntersectionObserver(
    (entries) => {
      entries.forEach((e) => {
        if (e.isIntersecting) {
          e.target.classList.add("in");
          io.unobserve(e.target);
        }
      });
    },
    { threshold: 0.12, rootMargin: "0px 0px -40px 0px" }
  );

  qsa(".reveal, .reveal-line").forEach((el) => io.observe(el));

  // Hero reveals immediately after load
  window.addEventListener("load", () => {
    setTimeout(() => heroTitle && heroTitle.classList.add("in"), 80);
  });

  /* ---------- Stat counters ---------- */
  const statEls = qsa(".stat-num");
  const statIO = new IntersectionObserver(
    (entries) => {
      entries.forEach((e) => {
        if (!e.isIntersecting) return;
        const el = e.target;
        const target = Number(el.dataset.count || 0);
        const dur = 1400;
        const start = performance.now();
        const ease = (t) => 1 - Math.pow(1 - t, 3);
        const frame = (now) => {
          const t = Math.min(1, (now - start) / dur);
          el.textContent = Math.round(target * ease(t)).toString();
          if (t < 1) requestAnimationFrame(frame);
        };
        requestAnimationFrame(frame);
        statIO.unobserve(el);
      });
    },
    { threshold: 0.4 }
  );
  statEls.forEach((el) => statIO.observe(el));

  /* ---------- Subtle parallax on hero spine ---------- */
  const spine = qs(".hero-spine");
  if (spine) {
    window.addEventListener(
      "scroll",
      () => {
        const y = window.scrollY;
        spine.style.opacity = Math.max(0, 1 - y / 600).toString();
      },
      { passive: true }
    );
  }

  /* ---------- Magnetic buttons ---------- */
  qsa(".btn-primary, .btn-light").forEach((btn) => {
    btn.addEventListener("mousemove", (e) => {
      const r = btn.getBoundingClientRect();
      const x = e.clientX - (r.left + r.width / 2);
      const y = e.clientY - (r.top + r.height / 2);
      btn.style.transform = `translate(${x * 0.15}px, ${y * 0.2}px)`;
    });
    btn.addEventListener("mouseleave", () => {
      btn.style.transform = "";
    });
  });
})();
