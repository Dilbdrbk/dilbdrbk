// Small enhancements; the site works without JavaScript.
(function () {
  // Mobile menu.
  var btn = document.querySelector('.menu-btn');
  var nav = document.querySelector('.nav');
  if (btn && nav) {
    btn.addEventListener('click', function () {
      var open = btn.getAttribute('aria-expanded') === 'true';
      btn.setAttribute('aria-expanded', String(!open));
      btn.textContent = open ? 'Menu' : 'Close';
      nav.classList.toggle('is-open', !open);
    });
    document.addEventListener('keydown', function (e) {
      if (e.key === 'Escape' && nav.classList.contains('is-open')) {
        btn.click();
        btn.focus();
      }
    });
  }

  // Local time in Kathmandu.
  var clocks = document.querySelectorAll('[data-clock]');
  if (clocks.length && window.Intl) {
    var fmt = new Intl.DateTimeFormat('en-GB', { timeZone: 'Asia/Kathmandu', hour: '2-digit', minute: '2-digit' });
    var tick = function () {
      var now = fmt.format(new Date());
      clocks.forEach(function (el) { el.textContent = now; });
    };
    tick();
    setInterval(tick, 30000);
  }

  var year = document.querySelector('[data-year]');
  if (year) year.textContent = new Date().getFullYear();

  // Home: search pipeline as tabs (arrow keys, Home and End move between them).
  // Earlier stages show as done and the track fills to the open stage. With
  // data-autoplay it advances on its own once in view, until the visitor hovers
  // or picks a stage.
  var stillMotion = matchMedia('(prefers-reduced-motion: reduce)').matches;
  document.querySelectorAll('[data-stages]').forEach(function (box) {
    var tabs = Array.prototype.slice.call(box.querySelectorAll('[role="tab"]'));
    var timer = null;
    var current = 0;
    var select = function (tab, focus) {
      current = tabs.indexOf(tab);
      tabs.forEach(function (t, k) {
        var on = k === current;
        t.setAttribute('aria-selected', String(on));
        t.tabIndex = on ? 0 : -1;
        t.classList.toggle('is-done', k < current);
        document.getElementById(t.getAttribute('aria-controls')).classList.toggle('is-active', on);
      });
      box.style.setProperty('--progress', tabs.length > 1 ? current / (tabs.length - 1) : 0);
      if (focus) tab.focus();
    };
    var stop = function () { clearInterval(timer); timer = null; box.removeAttribute('data-autoplay'); };
    tabs.forEach(function (tab, i) {
      tab.addEventListener('click', function () { stop(); select(tab); });
      tab.addEventListener('keydown', function (e) {
        var next = { ArrowRight: tabs[(i + 1) % tabs.length], ArrowLeft: tabs[(i - 1 + tabs.length) % tabs.length],
                     Home: tabs[0], End: tabs[tabs.length - 1] }[e.key];
        if (next) {
          e.preventDefault();
          stop();
          select(next, true);
        }
      });
    });
    select(tabs[0]);

    if (stillMotion || !box.hasAttribute('data-autoplay') || !('IntersectionObserver' in window)) return;
    box.addEventListener('mouseenter', stop);
    box.addEventListener('focusin', stop);
    new IntersectionObserver(function (entries) {
      entries.forEach(function (entry) {
        if (!box.hasAttribute('data-autoplay')) return;
        if (entry.isIntersecting && !timer) {
          timer = setInterval(function () { select(tabs[(current + 1) % tabs.length]); }, 5000);
        } else if (!entry.isIntersecting && timer) {
          clearInterval(timer);
          timer = null;
        }
      });
    }, { threshold: 0.35 }).observe(box);
  });

  // Home hero: entity orbit. Nodes light up on hover or focus and cycle on
  // their own while idle; the orbit tilts slightly with the pointer.
  var calm = matchMedia('(prefers-reduced-motion: reduce)').matches;
  document.querySelectorAll('[data-orbit]').forEach(function (orbit) {
    var nodes = Array.prototype.slice.call(orbit.querySelectorAll('.orbit-node'));
    var edges = orbit.querySelectorAll('.orbit-edge');
    var caption = document.querySelector('[data-orbit-caption]');
    var title = caption && caption.querySelector('.orbit-caption-title');
    var text = caption && caption.querySelector('.orbit-caption-text');
    var initial = caption ? [title.textContent, text.textContent] : null;
    var current = -1;
    var timer = null;

    var show = function (i) {
      current = i;
      nodes.forEach(function (n, k) { n.classList.toggle('is-active', k === i); });
      Array.prototype.forEach.call(edges, function (e, k) { e.classList.toggle('is-active', k === i); });
      if (!caption) return;
      title.textContent = i > -1 ? nodes[i].textContent : initial[0];
      text.textContent = i > -1 ? nodes[i].getAttribute('data-desc') : initial[1];
    };
    var cycle = function () {
      if (calm || timer) return;
      timer = setInterval(function () { show((current + 1) % nodes.length); }, 2800);
    };
    var stop = function () { clearInterval(timer); timer = null; };

    nodes.forEach(function (n, i) {
      n.addEventListener('mouseenter', function () { stop(); show(i); });
      n.addEventListener('focus', function () { stop(); show(i); });
      n.addEventListener('blur', function () { show(-1); cycle(); });
    });
    orbit.addEventListener('mouseleave', function () { show(-1); cycle(); });
    cycle();

    if (!calm && matchMedia('(pointer: fine)').matches) {
      var wrap = orbit.parentElement;
      wrap.addEventListener('pointermove', function (e) {
        var r = wrap.getBoundingClientRect();
        orbit.style.setProperty('--ry', (((e.clientX - r.left) / r.width - 0.5) * 10).toFixed(2) + 'deg');
        orbit.style.setProperty('--rx', ((0.5 - (e.clientY - r.top) / r.height) * 10).toFixed(2) + 'deg');
      });
      wrap.addEventListener('pointerleave', function () {
        orbit.style.setProperty('--rx', '0deg');
        orbit.style.setProperty('--ry', '0deg');
      });
    }
  });

  // "Hire me" pop-up form. Trigger links keep their normal href as the no-JS
  // fallback. With no endpoint configured, submit opens the visitor's email app.
  var dialog = document.getElementById('lead-dialog');
  if (dialog && typeof dialog.showModal === 'function') {
    var form = dialog.querySelector('form');
    var status = dialog.querySelector('.lead-status');
    document.querySelectorAll('[data-open-form]').forEach(function (link) {
      link.addEventListener('click', function (e) {
        if (e.metaKey || e.ctrlKey || e.shiftKey || e.button !== 0) return;
        e.preventDefault();
        status.textContent = '';
        dialog.showModal();
        form.querySelector('[name="name"]').focus();
      });
    });
    dialog.querySelector('[data-close-form]').addEventListener('click', function () { dialog.close(); });
    dialog.addEventListener('click', function (e) { if (e.target === dialog) dialog.close(); });
    form.addEventListener('submit', function (e) {
      e.preventDefault();
      var data = new FormData(form);
      if (data.get('_gotcha')) return;
      var to = form.getAttribute('data-email');
      var endpoint = form.getAttribute('data-endpoint');
      if (endpoint) {
        status.textContent = 'Sending…';
        fetch(endpoint, { method: 'POST', headers: { Accept: 'application/json' }, body: data })
          .then(function (r) {
            if (!r.ok) throw new Error(r.status);
            form.reset();
            status.textContent = 'Thanks, your request is on its way. I’ll reply personally.';
          })
          .catch(function () { status.textContent = 'Sending failed. Please email me at ' + to + '.'; });
        return;
      }
      var body = ['Name: ' + data.get('name'), 'Email: ' + data.get('email'), 'Website: ' + (data.get('website') || '-'), '', data.get('message')].join('\n');
      location.href = 'mailto:' + to + '?subject=' + encodeURIComponent('Website review request from ' + data.get('name')) +
        '&body=' + encodeURIComponent(body);
      status.textContent = 'Your email app should open with your request ready to send.';
    });
  }

  // Stats bar: numbers count up once when they scroll into view. The final
  // value is already in the HTML, so nothing changes without JS.
  var counters = document.querySelectorAll('[data-count]');
  if (counters.length && !stillMotion && 'IntersectionObserver' in window) {
    var countIO = new IntersectionObserver(function (entries) {
      entries.forEach(function (entry) {
        if (!entry.isIntersecting) return;
        countIO.unobserve(entry.target);
        var el = entry.target;
        var to = +el.getAttribute('data-count');
        var from = +(el.getAttribute('data-from') || 0);
        var suffix = el.getAttribute('data-suffix') || '';
        var start = null;
        var step = function (t) {
          if (start === null) start = t;
          var k = Math.min((t - start) / 1200, 1);
          el.textContent = Math.round(from + (to - from) * (1 - Math.pow(1 - k, 3))) + suffix;
          if (k < 1) requestAnimationFrame(step);
        };
        requestAnimationFrame(step);
      });
    }, { threshold: 0.6 });
    counters.forEach(function (el) { countIO.observe(el); });
  }

  // Fade sections in as they scroll into view.
  var targets = document.querySelectorAll('main > .frame:not(:first-child) .body');
  if ('IntersectionObserver' in window && !matchMedia('(prefers-reduced-motion: reduce)').matches) {
    var io = new IntersectionObserver(function (entries) {
      entries.forEach(function (entry) {
        if (entry.isIntersecting) {
          entry.target.classList.add('is-in');
          io.unobserve(entry.target);
        }
      });
    }, { rootMargin: '0px 0px -8% 0px' });
    targets.forEach(function (el) {
      el.setAttribute('data-reveal', '');
      io.observe(el);
    });
  }
})();
