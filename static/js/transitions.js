/* ═══════════════════════════════════════
   NqiZbali — Global Smooth Transitions
   Instagram-level page animations
═══════════════════════════════════════ */

(function() {

  // ── Create transition overlay ──
  const overlay = document.createElement('div');
  overlay.className = 'page-transition';
  document.body.appendChild(overlay);

  // ── Animate page entrance ──
  function animateEntrance() {
    // Fade in overlay then remove
    overlay.classList.add('in');
    requestAnimationFrame(() => {
      requestAnimationFrame(() => {
        overlay.classList.remove('in');
      });
    });

    // Stagger all cards
    const cards = document.querySelectorAll(
      '.card, .bcard, .stat-pill, .stat-card, .stat-box, ' +
      '.role-card, .feature-card, .syndic-card, .history-card, ' +
      '.status-card, .map-card, .qr-card, .profile-card, ' +
      '.section-card, .collector-hero, .story-header, ' +
      '.profile-hero, .nearby-card, .greeting, .pending-banner, ' +
      '.table-wrap, .rev-card, .hist-card, .stats-row, ' +
      '.hero, .roles-section, .features-section'
    );

    cards.forEach((el, i) => {
      el.style.opacity = '0';
      el.style.transform = 'translateY(18px)';
      el.style.transition = 'none';
      setTimeout(() => {
        el.style.transition = `opacity .4s ease, transform .4s cubic-bezier(.34,1.56,.64,1)`;
        el.style.transitionDelay = `${i * 0.06}s`;
        el.style.opacity = '1';
        el.style.transform = 'translateY(0)';
      }, 30 + i * 30);
    });

    // Animate stat numbers
    document.querySelectorAll('.stat-val, .stat-num, .perf-pts, .bstat-val, .hero-stat-val').forEach((el, i) => {
      const original = el.textContent;
      el.style.opacity = '0';
      setTimeout(() => {
        el.style.transition = 'opacity .3s ease, transform .3s cubic-bezier(.34,1.56,.64,1)';
        el.style.transform = 'translateY(8px)';
        setTimeout(() => {
          el.style.opacity = '1';
          el.style.transform = 'translateY(0)';
          // Animate number if it's a number
          const num = parseFloat(original.replace(/[^0-9.]/g, ''));
          if (!isNaN(num) && num > 0 && num < 10000 && original === String(Math.round(num))) {
            animateNumber(el, num);
          }
        }, 50);
      }, 200 + i * 80);
    });
  }

  // ── Number counter animation ──
  function animateNumber(el, target) {
    const duration = 600;
    const start = performance.now();
    const startVal = 0;
    function step(now) {
      const elapsed = now - start;
      const progress = Math.min(elapsed / duration, 1);
      const ease = 1 - Math.pow(1 - progress, 3);
      el.textContent = Math.round(startVal + (target - startVal) * ease);
      if (progress < 1) requestAnimationFrame(step);
    }
    requestAnimationFrame(step);
  }

  // ── Page link transitions ──
  function handleLinkClick(e) {
    const link = e.currentTarget;
    const href = link.getAttribute('href');

    // Skip external, hash, javascript links
    if (!href || href.startsWith('#') || href.startsWith('javascript') ||
        href.startsWith('http') || link.target === '_blank') return;

    e.preventDefault();

    // Add ripple
    addRipple(link, e);

    // Slide out
    overlay.style.transition = 'opacity .2s ease';
    overlay.classList.add('in');

    setTimeout(() => {
      window.location.href = href;
    }, 200);
  }

  // ── Ripple effect ──
  function addRipple(el, e) {
    const rect = el.getBoundingClientRect();
    const ripple = document.createElement('span');
    const size = Math.max(rect.width, rect.height) * 2;
    const x = (e.clientX - rect.left) - size/2;
    const y = (e.clientY - rect.top)  - size/2;

    ripple.style.cssText = `
      position:absolute;
      width:${size}px;height:${size}px;
      left:${x}px;top:${y}px;
      background:rgba(255,255,255,.25);
      border-radius:50%;
      pointer-events:none;
      transform:scale(0);
      animation:rippleAnim .5s ease forwards;
      z-index:10;
    `;

    const style = document.createElement('style');
    style.textContent = `@keyframes rippleAnim{to{transform:scale(1);opacity:0}}`;
    document.head.appendChild(style);

    el.style.position = el.style.position || 'relative';
    el.style.overflow = 'hidden';
    el.appendChild(ripple);
    setTimeout(() => ripple.remove(), 600);
  }

  // ── Button press animation ──
  function addButtonAnimations() {
    const btns = document.querySelectorAll(
      'button, .btn, .role-card, .pay-btn, .btn-pay, .action-btn, ' +
      '.big-btn, .btn-collect, .btn-viol, .btn-cam-open, ' +
      '.btn-approve, .btn-ok, .btn-add, .nav-item, .nav-logout'
    );

    btns.forEach(btn => {
      btn.addEventListener('mousedown', () => {
        btn.style.transition = 'transform .12s cubic-bezier(.34,1.56,.64,1)';
        btn.style.transform = 'scale(.95)';
      });
      btn.addEventListener('mouseup', () => {
        btn.style.transform = 'scale(1)';
      });
      btn.addEventListener('touchstart', () => {
        btn.style.transition = 'transform .12s cubic-bezier(.34,1.56,.64,1)';
        btn.style.transform = 'scale(.95)';
      }, {passive:true});
      btn.addEventListener('touchend', () => {
        setTimeout(() => { btn.style.transform = 'scale(1)'; }, 100);
      });
    });
  }

  // ── Nav tab animation (for bottom nav) ──
  function animateTabSwitch(tabEl) {
    if (!tabEl) return;
    tabEl.style.transform = 'scale(.85)';
    tabEl.style.transition = 'transform .15s cubic-bezier(.34,1.56,.64,1)';
    setTimeout(() => {
      tabEl.style.transform = 'scale(1)';
    }, 150);
  }

  // ── Intercept switchTab if exists ──
  const originalSwitchTab = window.switchTab;
  if (typeof originalSwitchTab === 'function') {
    window.switchTab = function(tab) {
      // Animate out current page
      const currentPage = document.querySelector('.page.active');
      if (currentPage) {
        currentPage.style.transition = 'opacity .15s ease, transform .15s ease';
        currentPage.style.opacity = '0';
        currentPage.style.transform = 'translateY(6px)';
      }

      setTimeout(() => {
        originalSwitchTab(tab);
        // Animate in new page
        const newPage = document.getElementById('page-'+tab);
        if (newPage) {
          newPage.style.opacity = '0';
          newPage.style.transform = 'translateY(10px)';
          newPage.style.transition = 'none';
          requestAnimationFrame(() => {
            newPage.style.transition = 'opacity .25s ease, transform .25s cubic-bezier(.34,1.56,.64,1)';
            newPage.style.opacity = '1';
            newPage.style.transform = 'translateY(0)';
          });
        }

        // Animate nav icon
        const navItem = document.getElementById('nav-'+tab);
        if (navItem) animateTabSwitch(navItem);

        // Re-animate cards in new page
        if (newPage) {
          const newCards = newPage.querySelectorAll(
            '.status-card, .map-card, .history-card, .qr-card, .profile-card, .map-section'
          );
          newCards.forEach((card, i) => {
            card.style.opacity = '0';
            card.style.transform = 'translateY(12px)';
            card.style.transition = 'none';
            setTimeout(() => {
              card.style.transition = `opacity .35s ease, transform .35s cubic-bezier(.34,1.56,.64,1)`;
              card.style.transitionDelay = `${i * 0.07}s`;
              card.style.opacity = '1';
              card.style.transform = 'translateY(0)';
            }, 20 + i * 40);
          });
        }
      }, 120);
    };
  }

  // ── Toast animation enhancement ──
  const originalShowToast = window.showToast;
  if (typeof originalShowToast === 'function') {
    window.showToast = function(msg) {
      originalShowToast(msg);
      const toast = document.getElementById('toast');
      if (toast) {
        toast.style.animation = 'none';
        void toast.offsetWidth;
      }
    };
  }

  // ── Scroll animations ──
  function initScrollAnimations() {
    const observer = new IntersectionObserver((entries) => {
      entries.forEach(entry => {
        if (entry.isIntersecting) {
          entry.target.style.opacity = '1';
          entry.target.style.transform = 'translateY(0)';
          observer.unobserve(entry.target);
        }
      });
    }, { threshold: 0.1, rootMargin: '0px 0px -30px 0px' });

    document.querySelectorAll('.scroll-reveal').forEach(el => {
      el.style.opacity = '0';
      el.style.transform = 'translateY(20px)';
      el.style.transition = 'opacity .4s ease, transform .4s cubic-bezier(.34,1.56,.64,1)';
      observer.observe(el);
    });
  }

  // ── Init everything ──
  function init() {
    // Intercept all internal links
    document.querySelectorAll('a[href]').forEach(link => {
      const href = link.getAttribute('href');
      if (href && !href.startsWith('#') && !href.startsWith('http') &&
          !href.startsWith('javascript') && link.target !== '_blank') {
        link.addEventListener('click', handleLinkClick);
      }
    });

    // Button animations
    addButtonAnimations();

    // Scroll reveal
    initScrollAnimations();

    // Entrance animation
    animateEntrance();
  }

  // Run after DOM ready
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else {
    setTimeout(init, 50);
  }

})();
