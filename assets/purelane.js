/*
 * Purelane section behaviour.
 *
 * THE PROBLEM THIS FILE SOLVES
 * The prototype ran one querySelectorAll at page load and bound everything globally. In
 * Shopify's theme editor that is fatal: the editor re-renders a single section over AJAX
 * whenever a merchant edits it, so anything bound at load is pointing at DOM nodes that no
 * longer exist. Reveals stop firing, carousels freeze, and timers from the old copy keep
 * running in the background. The brief requires that adding, removing, reordering and
 * reconfiguring never breaks anything "including the animations".
 *
 * THE APPROACH
 * Every behaviour is a small controller that owns one section element and knows how to
 * destroy itself. Controllers are registered per section id, so a re-render tears the old
 * one down before building the new one. No global state, no leaked observers or intervals.
 *
 * Motion is opt-in: if the visitor prefers reduced motion, content renders in its final
 * state rather than being hidden waiting for an animation that will never run.
 */
(function () {
  'use strict';

  /*
   * IDEMPOTENCE — this file is included by every Purelane section.
   *
   * `purelane-assets.liquid` is rendered per section so the sections stay self-contained
   * and drop into any template without editing the layout. The browser fetches the file
   * once, but it EXECUTES this IIFE once per <script> tag — six times on the Purelane
   * homepage. Without this guard each copy keeps its own private `controllers` map and
   * registers its own lifecycle listeners, so six controllers end up bound to the same
   * section and no copy's `destroy` can tear down another copy's timers and observers.
   * That is the exact stacking the teardown design exists to prevent, reintroduced by the
   * include strategy rather than by the controllers.
   *
   * One copy wins and owns every section; the rest return immediately. Found by counting
   * observer registrations after a single `shopify:section:load`, not by reading the code.
   */
  if (window.__purelaneBehaviour) return;
  window.__purelaneBehaviour = true;

  var reduceMotion = window.matchMedia('(prefers-reduced-motion: reduce)');
  var controllers = {}; // section id -> array of teardown functions

  function prefersReduced() {
    return reduceMotion.matches;
  }

  /* ---------------------------------------------------------------------------
   * Reveal on scroll
   * Elements marked .rv fade in once. With reduced motion they are simply shown.
   * ------------------------------------------------------------------------- */
  function initReveal(root) {
    var items = root.querySelectorAll('.rv');
    if (!items.length) return null;

    if (prefersReduced() || !('IntersectionObserver' in window)) {
      Array.prototype.forEach.call(items, function (el) { el.classList.add('in'); });
      return null;
    }

    var observer = new IntersectionObserver(function (entries) {
      entries.forEach(function (entry) {
        if (!entry.isIntersecting) return;
        entry.target.classList.add('in');
        observer.unobserve(entry.target);
      });
    }, { rootMargin: '0px 0px -12% 0px', threshold: 0.12 });

    Array.prototype.forEach.call(items, function (el) { observer.observe(el); });
    return function teardown() { observer.disconnect(); };
  }

  /* ---------------------------------------------------------------------------
   * Carousel (hero slides, reviews rail)
   * Autoplay pauses on hover, on keyboard focus, when scrolled out of view, and while
   * the merchant has the section selected in the theme editor.
   * ------------------------------------------------------------------------- */
  function initCarousel(root, options) {
    var slides = root.querySelectorAll(options.slide);
    var dots = root.querySelectorAll(options.dot);
    if (slides.length < 2) return null;

    var index = 0;
    var timer = null;
    var interval = parseInt(root.getAttribute('data-autoplay'), 10) || 3800;
    var autoplayAllowed = root.getAttribute('data-autoplay') !== 'off' && !prefersReduced();

    function show(next) {
      index = (next + slides.length) % slides.length;
      Array.prototype.forEach.call(slides, function (slide, i) {
        slide.classList.toggle('on', i === index);
        // Hide inactive slides from assistive tech rather than just visually.
        slide.setAttribute('aria-hidden', i === index ? 'false' : 'true');
      });
      Array.prototype.forEach.call(dots, function (dot, i) {
        dot.classList.toggle('on', i === index);
        dot.setAttribute('aria-selected', i === index ? 'true' : 'false');
        dot.setAttribute('tabindex', i === index ? '0' : '-1');
      });
    }

    function play() {
      if (timer || !autoplayAllowed) return;
      timer = setInterval(function () { show(index + 1); }, interval);
    }
    function stop() {
      if (!timer) return;
      clearInterval(timer);
      timer = null;
    }

    var onDotClick = [];
    Array.prototype.forEach.call(dots, function (dot, i) {
      var handler = function () { stop(); show(i); play(); };
      dot.addEventListener('click', handler);
      onDotClick.push([dot, handler]);
    });

    // Arrow keys move between slides when the control strip has focus.
    function onKey(event) {
      if (event.key !== 'ArrowRight' && event.key !== 'ArrowLeft') return;
      event.preventDefault();
      stop();
      show(index + (event.key === 'ArrowRight' ? 1 : -1));
      if (dots[index]) dots[index].focus();
    }

    root.addEventListener('mouseenter', stop);
    root.addEventListener('mouseleave', play);
    root.addEventListener('focusin', stop);
    root.addEventListener('focusout', play);
    root.addEventListener('keydown', onKey);

    // Don't burn frames animating a carousel nobody is looking at.
    var visibility = null;
    if ('IntersectionObserver' in window) {
      visibility = new IntersectionObserver(function (entries) {
        entries.forEach(function (entry) { entry.isIntersecting ? play() : stop(); });
      }, { threshold: 0.2 });
      visibility.observe(root);
    } else {
      play();
    }

    show(0);

    return function teardown() {
      stop();
      if (visibility) visibility.disconnect();
      root.removeEventListener('mouseenter', stop);
      root.removeEventListener('mouseleave', play);
      root.removeEventListener('focusin', stop);
      root.removeEventListener('focusout', play);
      root.removeEventListener('keydown', onKey);
      onDotClick.forEach(function (pair) { pair[0].removeEventListener('click', pair[1]); });
    };
  }

  /* ---------------------------------------------------------------------------
   * Hero parallax
   * Desktop only, motion-permitting only, and batched into a single rAF so scroll and
   * pointer movement never trigger more than one layout pass per frame.
   * ------------------------------------------------------------------------- */
  function initParallax(root) {
    var target = root.querySelector('[data-parallax]');
    if (!target || prefersReduced()) return null;
    if (!window.matchMedia('(min-width: 1024px)').matches) return null;

    var frame = null;
    var pointerX = 0;
    var pointerY = 0;

    function render() {
      frame = null;
      var scrolled = window.scrollY || window.pageYOffset;
      var progress = Math.min(scrolled / 700, 1);
      target.style.transform =
        'translate3d(' + (pointerX * -16).toFixed(2) + 'px,' +
        (-progress * 54 + pointerY * -10).toFixed(2) + 'px,0) ' +
        'scale(' + (1 - progress * 0.06).toFixed(3) + ')';
      target.style.opacity = (1 - progress * 0.55).toFixed(3);
    }
    function schedule() {
      if (!frame) frame = requestAnimationFrame(render);
    }
    function onPointer(event) {
      pointerX = (event.clientX / window.innerWidth - 0.5) * 2;
      pointerY = (event.clientY / window.innerHeight - 0.5) * 2;
      schedule();
    }

    window.addEventListener('scroll', schedule, { passive: true });
    window.addEventListener('resize', schedule);
    window.addEventListener('mousemove', onPointer, { passive: true });
    schedule();

    return function teardown() {
      if (frame) cancelAnimationFrame(frame);
      window.removeEventListener('scroll', schedule);
      window.removeEventListener('resize', schedule);
      window.removeEventListener('mousemove', onPointer);
      target.style.transform = '';
      target.style.opacity = '';
    };
  }

  /* ---------------------------------------------------------------------------
   * Section lifecycle
   * ------------------------------------------------------------------------- */
  function destroy(sectionId) {
    var teardowns = controllers[sectionId];
    if (!teardowns) return;
    teardowns.forEach(function (fn) { if (typeof fn === 'function') fn(); });
    delete controllers[sectionId];
  }

  function init(root) {
    if (!root) return;
    var id = root.getAttribute('data-section-id');
    if (!id) return;

    destroy(id); // a re-render must never stack a second set of observers

    var teardowns = [initReveal(root)];

    if (root.hasAttribute('data-carousel')) {
      teardowns.push(initCarousel(root, {
        slide: '[data-slide]',
        dot: '[data-slide-dot]'
      }));
    }
    if (root.hasAttribute('data-parallax-host')) {
      teardowns.push(initParallax(root));
    }

    controllers[id] = teardowns.filter(Boolean);
  }

  function initAll(scope) {
    var roots = (scope || document).querySelectorAll('[data-purelane-section]');
    Array.prototype.forEach.call(roots, init);
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', function () { initAll(); });
  } else {
    initAll();
  }

  // Shopify theme editor events. Without these, every animation dies the first time a
  // merchant edits a section, and the old section's timers keep running forever.
  document.addEventListener('shopify:section:load', function (event) {
    initAll(event.target);
  });
  document.addEventListener('shopify:section:unload', function (event) {
    destroy(event.detail.sectionId);
  });
  document.addEventListener('shopify:section:select', function (event) {
    // Freeze autoplay while the merchant is working on the section, so the thing they
    // are editing holds still.
    var root = event.target.querySelector('[data-purelane-section]');
    if (root) root.dispatchEvent(new Event('focusin'));
  });
  document.addEventListener('shopify:section:deselect', function (event) {
    var root = event.target.querySelector('[data-purelane-section]');
    if (root) root.dispatchEvent(new Event('focusout'));
  });

  // If the visitor changes their motion preference mid-session, re-init so we honour it
  // without requiring a reload.
  if (typeof reduceMotion.addEventListener === 'function') {
    reduceMotion.addEventListener('change', function () {
      Object.keys(controllers).forEach(destroy);
      initAll();
    });
  }
})();
