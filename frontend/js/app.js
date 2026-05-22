/**
 * Prepzo — shared UI utilities (vanilla JS)
 * Page loader, scroll reveals, mobile nav
 */
const AppUI = {
  init() {
    this.hideLoader();
    this.initReveal();
    this.initMobileNav();
  },

  hideLoader() {
    const loader = document.getElementById('page-loader');
    if (!loader) return;
    window.addEventListener('load', () => {
      setTimeout(() => loader.classList.add('done'), 280);
    });
    setTimeout(() => loader.classList.add('done'), 2500);
  },

  initReveal() {
    const els = document.querySelectorAll('.reveal');
    if (!els.length) return;
    const obs = new IntersectionObserver(
      (entries) => {
        entries.forEach((e) => {
          if (e.isIntersecting) {
            e.target.classList.add('visible');
            obs.unobserve(e.target);
          }
        });
      },
      { threshold: 0.12, rootMargin: '0px 0px -40px 0px' }
    );
    els.forEach((el) => obs.observe(el));
  },

  initMobileNav() {
    const btn = document.getElementById('mobile-menu-btn');
    const nav = document.getElementById('mobile-nav');
    if (!btn || !nav) return;
    btn.addEventListener('click', () => nav.classList.toggle('open'));
    nav.querySelectorAll('a').forEach((a) => {
      a.addEventListener('click', () => nav.classList.remove('open'));
    });
  },

  toggleSidebar(open) {
    document.getElementById('app-sidebar')?.classList.toggle('open', open);
    document.getElementById('sidebar-overlay')?.classList.toggle('open', open);
  },
};

document.addEventListener('DOMContentLoaded', () => AppUI.init());
