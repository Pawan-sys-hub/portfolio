/**
 * main.js – Portfolio Website Frontend Logic
 *
 * Sections:
 *   1. Theme (Dark / Light)
 *   2. Navigation (mobile menu + scroll behaviour + active link)
 *   3. Typed text animation
 *   4. Projects – fetch + render + filter + drawer
 *   5. Contact form – async submit with alert banner
 *   6. Email clipboard copy
 *   7. ScrollReveal animations
 *   8. Footer year
 */

"use strict";

/* ============================================================
   1. THEME TOGGLE
   ============================================================ */
(function initTheme() {
  const root = document.documentElement;
  const themeBtn = document.getElementById("theme-toggle");
  const themeIcon = document.getElementById("theme-icon");

  /** Apply a theme and persist the preference. */
  function applyTheme(theme) {
    root.setAttribute("data-theme", theme);
    localStorage.setItem("portfolio-theme", theme);
    // Swap icon
    themeIcon.className = theme === "dark" ? "ri-moon-line" : "ri-sun-line";
  }

  // On first load: honour saved preference, otherwise keep HTML default (dark)
  const saved = localStorage.getItem("portfolio-theme");
  if (saved) applyTheme(saved);

  themeBtn.addEventListener("click", () => {
    const current = root.getAttribute("data-theme") || "dark";
    applyTheme(current === "dark" ? "light" : "dark");
  });
})();

/* ============================================================
   2. NAVIGATION
   ============================================================ */
(function initNav() {
  const header = document.getElementById("header");
  const navMenu = document.getElementById("nav-menu");
  const navToggle = document.getElementById("nav-toggle");
  const navClose = document.getElementById("nav-close");
  const navLinks = document.querySelectorAll(".nav__link");
  const sections = document.querySelectorAll("section[id]");

  // ── Mobile menu open / close ──────────────────────────────────────────────
  navToggle?.addEventListener("click", () => navMenu.classList.add("show"));
  navClose?.addEventListener("click", () => navMenu.classList.remove("show"));

  // Close mobile menu when a link is clicked
  navLinks.forEach(link => {
    link.addEventListener("click", () => navMenu.classList.remove("show"));
  });

  // ── Scroll: header shadow + active nav link ───────────────────────────────
  function onScroll() {
    // Add scrolled class for glassmorphism background
    header.classList.toggle("scrolled", window.scrollY > 40);

    // Highlight the nav link whose section is in view
    const scrollY = window.scrollY;
    sections.forEach(section => {
      const top = section.offsetTop - 100;
      const bottom = top + section.offsetHeight;
      const id = section.getAttribute("id");
      const link = document.querySelector(`.nav__link[href="#${id}"]`);
      if (!link) return;

      if (scrollY >= top && scrollY < bottom) {
        navLinks.forEach(l => l.classList.remove("active-link"));
        link.classList.add("active-link");
      }
    });
  }

  window.addEventListener("scroll", onScroll, { passive: true });
})();

/* ============================================================
   3. TYPED TEXT ANIMATION (Hero)
   ============================================================ */
(function initTyped() {
  const el = document.getElementById("typed-text");
  if (!el) return;

  const words = [
    "AI Engineer",
    "Frontend Developer",
    "UI / UX / Designer",
    "Figma",
    "Problem Solver",
  ];
  let wordIdx = 0;
  let charIdx = 0;
  let deleting = false;
  const PAUSE_AFTER_WORD = 1800;   // ms to pause when word is fully typed
  const PAUSE_AFTER_DELETE = 400;    // ms to pause after fully deleted
  const TYPE_SPEED = 70;     // ms per character (typing)
  const DELETE_SPEED = 40;     // ms per character (deleting)

  function tick() {
    const word = words[wordIdx];
    const current = word.slice(0, charIdx);
    el.textContent = current;

    if (!deleting && charIdx === word.length) {
      // Fully typed – pause then start deleting
      setTimeout(() => { deleting = true; tick(); }, PAUSE_AFTER_WORD);
      return;
    }

    if (deleting && charIdx === 0) {
      // Fully deleted – move to next word and pause
      deleting = false;
      wordIdx = (wordIdx + 1) % words.length;
      setTimeout(tick, PAUSE_AFTER_DELETE);
      return;
    }

    charIdx += deleting ? -1 : 1;
    setTimeout(tick, deleting ? DELETE_SPEED : TYPE_SPEED);
  }

  tick();
})();

/* ============================================================
   4. PROJECTS – Fetch, Render, Filter & Drawer
   ============================================================ */
(function initProjects() {
  const grid = document.getElementById("projects-grid");
  const loader = document.getElementById("projects-loader");
  const errorMsg = document.getElementById("projects-error");
  const filterBtns = document.querySelectorAll(".filter-btn");

  // Drawer elements
  const overlay = document.getElementById("drawer-overlay");
  const drawer = document.getElementById("project-drawer");
  const drawerClose = document.getElementById("drawer-close");
  const drawerImg = document.getElementById("drawer-img");
  const drawerCat = document.getElementById("drawer-category");
  const drawerTitle = document.getElementById("drawer-title");
  const drawerDesc = document.getElementById("drawer-description");
  const drawerTech = document.getElementById("drawer-tech");
  const drawerLive = document.getElementById("drawer-live");
  const drawerGit = document.getElementById("drawer-git");

  /** All fetched projects – used for client-side filtering. */
  let allProjects = [];

  // ── Build a project card HTML string ─────────────────────────────────────
  function buildCard(project) {
    const techBadges = project.technologies
      .slice(0, 4)                          // show max 4 badges on card
      .map(t => `<span class="tech-badge">${t}</span>`)
      .join("");

    return `
      <article
        class="project-card"
        role="listitem"
        data-id="${project.id}"
        data-category="${project.category}"
        tabindex="0"
        aria-label="View details for ${project.title}"
      >
        <div class="project-card__img-wrap">
          <img
            src="${project.image_url || 'https://via.placeholder.com/800x400?text=No+Image'}"
            alt="${project.title} screenshot"
            class="project-card__img"
            loading="lazy"
          />
          <div class="project-card__overlay">
            <span class="project-card__overlay-label">
              <i class="ri-eye-line"></i> View Details
            </span>
          </div>
        </div>
        <div class="project-card__body">
          <span class="project-card__category">${project.category}</span>
          <h3 class="project-card__title">${project.title}</h3>
          <p class="project-card__desc">${project.description}</p>
          <div class="project-card__tech">${techBadges}</div>
        </div>
      </article>
    `;
  }

  // ── Render an array of projects into the grid ────────────────────────────
  function renderProjects(projects) {
    if (projects.length === 0) {
      grid.innerHTML = `
        <p style="grid-column:1/-1;text-align:center;color:var(--clr-text-muted);padding:3rem 0;">
          No projects found for this category.
        </p>`;
      return;
    }
    grid.innerHTML = projects.map(buildCard).join("");

    // Attach click / keydown events to each card
    grid.querySelectorAll(".project-card").forEach(card => {
      const openDrawer = () => {
        const id = Number(card.dataset.id);
        const project = allProjects.find(p => p.id === id);
        if (project) showDrawer(project);
      };
      card.addEventListener("click", openDrawer);
      card.addEventListener("keydown", e => { if (e.key === "Enter" || e.key === " ") openDrawer(); });
    });
  }

  // ── Filter projects by category ──────────────────────────────────────────
  function filterProjects(category) {
    const filtered =
      category === "all"
        ? allProjects
        : allProjects.filter(p => p.category === category);
    renderProjects(filtered);
  }

  // ── Wire filter buttons ──────────────────────────────────────────────────
  filterBtns.forEach(btn => {
    btn.addEventListener("click", () => {
      filterBtns.forEach(b => b.classList.remove("active"));
      btn.classList.add("active");
      filterProjects(btn.dataset.filter);
    });
  });

  // ── Show / hide drawer ───────────────────────────────────────────────────
  function showDrawer(project) {
    drawerImg.src = project.image_url || "";
    drawerImg.alt = project.title + " screenshot";
    drawerCat.textContent = project.category;
    drawerTitle.textContent = project.title;
    drawerDesc.textContent = project.description;

    // Tech badges in drawer (show all)
    drawerTech.innerHTML = project.technologies
      .map(t => `<span class="tech-badge">${t}</span>`)
      .join("");

    drawerLive.href = project.live_link || "#";
    drawerGit.href = project.git_link || "#";

    drawer.classList.add("open");
    overlay.classList.add("active");
    drawer.removeAttribute("aria-hidden");
    overlay.removeAttribute("aria-hidden");
    drawerClose.focus();

    // Prevent body scroll while drawer is open
    document.body.style.overflow = "hidden";
  }

  function hideDrawer() {
    drawer.classList.remove("open");
    overlay.classList.remove("active");
    drawer.setAttribute("aria-hidden", "true");
    overlay.setAttribute("aria-hidden", "true");
    document.body.style.overflow = "";
  }

  drawerClose?.addEventListener("click", hideDrawer);
  overlay?.addEventListener("click", hideDrawer);
  document.addEventListener("keydown", e => { if (e.key === "Escape") hideDrawer(); });

  // ── Fetch projects from API ───────────────────────────────────────────────
  async function fetchProjects() {
    loader.classList.remove("hidden");
    grid.innerHTML = "";
    errorMsg.classList.add("hidden");

    try {
      const response = await fetch("/api/projects");

      if (!response.ok) {
        throw new Error(`Server responded with ${response.status}`);
      }

      const data = await response.json();

      if (!data.success || !Array.isArray(data.data)) {
        throw new Error("Unexpected API response format.");
      }

      allProjects = data.data;
      renderProjects(allProjects);

    } catch (err) {
      console.error("[Projects] Failed to fetch:", err);
      errorMsg.classList.remove("hidden");
    } finally {
      loader.classList.add("hidden");
    }
  }

  // Load projects when page is ready
  fetchProjects();
})();

/* ============================================================
   5. CONTACT FORM – Async Submit
   ============================================================ */
(function initContactForm() {
  const form = document.getElementById("contact-form");
  const alertBox = document.getElementById("form-alert");
  const submitBtn = document.getElementById("submit-btn");
  const submitLabel = document.getElementById("submit-label");

  if (!form) return;

  /** Display a banner alert inside the form. */
  function showAlert(message, type /* "success" | "error" */) {
    alertBox.className = `form-alert ${type}`;
    alertBox.innerHTML = `
      <i class="ri-${type === "success" ? "checkbox-circle" : "error-warning"}-fill"></i>
      ${message}
    `;
    alertBox.classList.remove("hidden");

    // Auto-hide success banners after 6 seconds
    if (type === "success") {
      setTimeout(() => alertBox.classList.add("hidden"), 6000);
    }
  }

  /** Set the button into a loading / idle state. */
  function setLoading(loading) {
    submitBtn.disabled = loading;
    submitLabel.textContent = loading ? "Sending…" : "Send Message";
  }

  form.addEventListener("submit", async (e) => {
    e.preventDefault();

    // Hide any previous alert
    alertBox.classList.add("hidden");

    // Collect form data
    const formData = new FormData(form);
    const payload = {
      name: formData.get("name")?.trim() ?? "",
      email: formData.get("email")?.trim() ?? "",
      subject: formData.get("subject")?.trim() ?? "",
      message: formData.get("message")?.trim() ?? "",
    };

    // Basic client-side guard (server validates too)
    if (!payload.name || !payload.email || !payload.subject || !payload.message) {
      showAlert("Please fill in all required fields.", "error");
      return;
    }

    setLoading(true);

    try {
      const response = await fetch("/api/contact", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });

      const data = await response.json();

      if (response.ok && data.success) {
        showAlert(data.message || "Message sent successfully!", "success");
        form.reset();  // Clear form fields on success
      } else {
        showAlert(
          data.message || "Something went wrong. Please try again.",
          "error"
        );
      }

    } catch (err) {
      console.error("[Contact] Network error:", err);
      showAlert("Network error. Please check your connection and retry.", "error");
    } finally {
      setLoading(false);
    }
  });
})();

/* ============================================================
   6. EMAIL CLIPBOARD COPY
   ============================================================ */
(function initClipboardCopy() {
  const btn = document.getElementById("copy-email-btn");
  const tooltip = document.getElementById("copy-tooltip");
  const icon = document.getElementById("copy-icon");

  if (!btn || !tooltip) return;

  btn.addEventListener("click", async () => {
    const email = btn.dataset.email || "";

    try {
      await navigator.clipboard.writeText(email);

      // Visual feedback
      icon.className = "ri-check-line";
      tooltip.classList.add("show");

      // Reset after 2 seconds
      setTimeout(() => {
        icon.className = "ri-file-copy-line";
        tooltip.classList.remove("show");
      }, 2000);

    } catch (err) {
      console.warn("[Clipboard] Copy failed:", err);
      // Fallback for older browsers
      const ta = document.createElement("textarea");
      ta.value = email;
      ta.style.position = "fixed";
      ta.style.opacity = "0";
      document.body.appendChild(ta);
      ta.focus();
      ta.select();
      document.execCommand("copy");
      document.body.removeChild(ta);

      icon.className = "ri-check-line";
      tooltip.classList.add("show");
      setTimeout(() => {
        icon.className = "ri-file-copy-line";
        tooltip.classList.remove("show");
      }, 2000);
    }
  });
})();

/* ============================================================
   7. SCROLL REVEAL ANIMATIONS
   ============================================================ */
(function initScrollReveal() {
  if (typeof ScrollReveal === "undefined") return;

  const sr = ScrollReveal({
    distance: "40px",
    duration: 800,
    easing: "cubic-bezier(0.16, 1, 0.3, 1)",
    reset: false,
  });

  // Hero
  sr.reveal(".hero__content", { origin: "left", delay: 100 });
  sr.reveal(".hero__image-wrapper", { origin: "right", delay: 200 });
  sr.reveal(".hero__chip", { origin: "bottom", delay: 350, interval: 150 });

  // About
  sr.reveal(".section__label", { origin: "bottom", delay: 100 });
  sr.reveal(".section__title", { origin: "bottom", delay: 180 });
  sr.reveal(".about__card", { origin: "left", delay: 250 });
  sr.reveal(".about__tabs-wrapper", { origin: "right", delay: 300 });

  // Projects
  sr.reveal(".filter-btns", { origin: "bottom", delay: 100 });
  // Project cards are revealed individually after DOM insertion
  // (We can't reveal elements that don't exist yet at ScrollReveal init time)

  // Contact
  sr.reveal(".contact__info", { origin: "left", delay: 200 });
  sr.reveal(".contact__form", { origin: "right", delay: 250 });

  // Footer
  sr.reveal(".footer__inner", { origin: "bottom", delay: 100 });
})();

/* ============================================================
   8. ABOUT TABS (Skills / Education / Experience)
   ============================================================ */
(function initAboutTabs() {
  const tabBtns = document.querySelectorAll(".tab-btn");
  const tabPanels = document.querySelectorAll(".tab-panel");

  if (!tabBtns.length) return;

  tabBtns.forEach(btn => {
    btn.addEventListener("click", () => {
      const target = btn.dataset.tab;

      // Update button states
      tabBtns.forEach(b => {
        b.classList.remove("active");
        b.setAttribute("aria-selected", "false");
      });
      btn.classList.add("active");
      btn.setAttribute("aria-selected", "true");

      // Show matching panel, hide others
      tabPanels.forEach(panel => {
        if (panel.id === `tab-${target}`) {
          panel.classList.add("active");
          panel.removeAttribute("hidden");
        } else {
          panel.classList.remove("active");
          panel.setAttribute("hidden", "");
        }
      });
    });
  });
})();

/* ============================================================
   9. FOOTER YEAR
   ============================================================ */
(function setFooterYear() {
  const yearEl = document.getElementById("footer-year");
  if (yearEl) yearEl.textContent = new Date().getFullYear();
})();
