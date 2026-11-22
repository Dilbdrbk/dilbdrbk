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

  // Header dropdowns: a click opens one group and closes the others; hover and focus open them on desktop.
  var subs = document.querySelectorAll('.has-sub');
  var closeSubs = function (except) {
    subs.forEach(function (li) {
      if (li === except) return;
      li.classList.remove('is-open');
      li.querySelector('.sub-btn').setAttribute('aria-expanded', 'false');
    });
  };
  subs.forEach(function (li) {
    var b = li.querySelector('.sub-btn');
    b.addEventListener('click', function () {
      var open = li.classList.toggle('is-open');
      b.setAttribute('aria-expanded', String(open));
      closeSubs(li);
    });
  });
  document.addEventListener('click', function (e) {
    if (!e.target.closest('.has-sub')) closeSubs(null);
  });
  document.addEventListener('keydown', function (e) {
    var open = document.querySelector('.has-sub.is-open');
    if (e.key === 'Escape' && open) {
      closeSubs(null);
      open.querySelector('.sub-btn').focus();
    }
  });

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
    var title = dialog.querySelector('.lead-title');
    var sub = dialog.querySelector('.lead-sub');
    var defaults = { title: title.textContent, sub: sub.textContent, subject: form.elements.subject.value };
    document.querySelectorAll('[data-open-form]').forEach(function (link) {
      link.addEventListener('click', function (e) {
        if (e.metaKey || e.ctrlKey || e.shiftKey || e.button !== 0) return;
        e.preventDefault();
        status.textContent = '';
        title.textContent = link.getAttribute('data-form-title') || defaults.title;
        sub.textContent = link.getAttribute('data-form-sub') || defaults.sub;
        form.elements.subject.value = link.getAttribute('data-form-subject') || defaults.subject;
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
      location.href = 'mailto:' + to + '?subject=' + encodeURIComponent((data.get('subject') || 'Website review request') + ' from ' + data.get('name')) +
        '&body=' + encodeURIComponent(body);
      status.textContent = 'Your email app should open with your request ready to send.';
    });
  }

  // Home hero: search results simulator. A tab picks the search type; its query
  // types into the bar and only the result blocks for that type are shown.
  document.querySelectorAll('[data-serp]').forEach(function (serp) {
    var tabs = Array.prototype.slice.call(serp.querySelectorAll('[role="tab"]'));
    var query = serp.querySelector('[data-serp-query]');
    var blocks = serp.querySelectorAll('[data-for]');
    var swaps = serp.querySelectorAll('[data-local]');
    var typing = null;
    var timer = null;
    var current = 0;
    var show = function (i, focus) {
      current = i;
      var tab = tabs[i];
      var key = tab.getAttribute('data-scenario');
      tabs.forEach(function (t, k) {
        t.setAttribute('aria-selected', String(k === i));
        t.tabIndex = k === i ? 0 : -1;
      });
      Array.prototype.forEach.call(blocks, function (b) {
        b.hidden = b.getAttribute('data-for').split(' ').indexOf(key) === -1;
      });
      Array.prototype.forEach.call(swaps, function (s) { s.textContent = s.getAttribute('data-' + key); });
      serp.classList.remove('is-run');
      void serp.offsetWidth;
      serp.classList.add('is-run');
      var text = tab.getAttribute('data-query');
      clearInterval(typing);
      if (stillMotion) {
        query.textContent = text;
      } else {
        var n = 0;
        query.textContent = '';
        typing = setInterval(function () {
          n += 1;
          query.textContent = text.slice(0, n);
          if (n >= text.length) clearInterval(typing);
        }, 45);
      }
      if (focus) tab.focus();
    };
    var stop = function () { clearInterval(timer); timer = null; serp.removeAttribute('data-autoplay'); };
    tabs.forEach(function (tab, i) {
      tab.addEventListener('click', function () { stop(); show(i); });
      tab.addEventListener('keydown', function (e) {
        var next = { ArrowRight: (i + 1) % tabs.length, ArrowLeft: (i - 1 + tabs.length) % tabs.length, Home: 0, End: tabs.length - 1 }[e.key];
        if (next !== undefined) { e.preventDefault(); stop(); show(next, true); }
      });
    });
    show(0);

    if (stillMotion || !('IntersectionObserver' in window)) return;
    serp.setAttribute('data-autoplay', '');
    serp.addEventListener('mouseenter', stop);
    serp.addEventListener('focusin', stop);
    new IntersectionObserver(function (entries) {
      entries.forEach(function (entry) {
        if (!serp.hasAttribute('data-autoplay')) return;
        if (entry.isIntersecting && !timer) {
          timer = setInterval(function () { show((current + 1) % tabs.length); }, 6500);
        } else if (!entry.isIntersecting && timer) {
          clearInterval(timer);
          timer = null;
        }
      });
    }, { threshold: 0.35 }).observe(serp);
  });

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

  // Home: Resources tabs (Blog, FAQ). Without JS the tab buttons stay hidden and
  // both panels show. A link to a panel's id, such as /#faq, opens that tab.
  document.querySelectorAll('[data-tabs]').forEach(function (box) {
    var tabs = Array.prototype.slice.call(box.querySelectorAll('[role="tab"]'));
    var panels = tabs.map(function (t) { return document.getElementById(t.getAttribute('aria-controls')); });
    var select = function (i, focus) {
      tabs.forEach(function (t, k) {
        var on = k === i;
        t.setAttribute('aria-selected', String(on));
        t.tabIndex = on ? 0 : -1;
        panels[k].hidden = !on;
      });
      if (focus) tabs[i].focus();
    };
    tabs.forEach(function (tab, i) {
      tab.addEventListener('click', function () { select(i); });
      tab.addEventListener('keydown', function (e) {
        var next = { ArrowRight: (i + 1) % tabs.length, ArrowLeft: (i - 1 + tabs.length) % tabs.length, Home: 0, End: tabs.length - 1 }[e.key];
        if (next !== undefined) { e.preventDefault(); select(next, true); }
      });
    });
    var fromHash = function () {
      for (var k = 0; k < panels.length; k++) {
        if (location.hash === '#' + panels[k].id) {
          select(k);
          panels[k].scrollIntoView();
          return true;
        }
      }
      return false;
    };
    if (!fromHash()) select(0);
    window.addEventListener('hashchange', fromHash);
  });

  // Blog post: the "On this page" sidebar marks the section in view and keeps
  // that link visible inside the panel. Without JS the links still jump.
  var toc = document.querySelector('[data-post-toc]');
  if (toc) {
    var tocLinks = Array.prototype.slice.call(toc.querySelectorAll('a[href^="#"]'));
    var tocHeads = tocLinks.map(function (a) { return document.getElementById(decodeURIComponent(a.hash.slice(1))); });
    var tocList = toc.querySelector('.post-side-list');
    var tocActive = -1;
    var tocTick = false;
    var tocUpdate = function () {
      tocTick = false;
      var idx = -1;
      for (var i = 0; i < tocHeads.length; i++) {
        if (!tocHeads[i]) continue;
        if (tocHeads[i].getBoundingClientRect().top <= 120) idx = i; else break;
      }
      if (idx === tocActive) return;
      if (tocActive >= 0) tocLinks[tocActive].removeAttribute('aria-current');
      tocActive = idx;
      if (idx < 0) return;
      var a = tocLinks[idx];
      a.setAttribute('aria-current', 'location');
      var top = a.offsetTop;
      var bottom = top + a.offsetHeight;
      if (top < tocList.scrollTop + 8) tocList.scrollTop = top - 8;
      else if (bottom > tocList.scrollTop + tocList.clientHeight - 8) tocList.scrollTop = bottom - tocList.clientHeight + 8;
    };
    // A short timer keeps this to a few updates a second while the page scrolls.
    window.addEventListener('scroll', function () {
      if (!tocTick) { tocTick = true; setTimeout(tocUpdate, 60); }
    }, { passive: true });
    tocUpdate();
  }

  // Blog post: Copy link in the share row (hidden without JS).
  Array.prototype.forEach.call(document.querySelectorAll('[data-copy]'), function (btn) {
    var label = btn.querySelector('span');
    btn.addEventListener('click', function () {
      var show = function (text) {
        label.textContent = text;
        setTimeout(function () { label.textContent = 'Copy link'; }, 2000);
      };
      if (navigator.clipboard && navigator.clipboard.writeText) {
        navigator.clipboard.writeText(btn.getAttribute('data-copy')).then(
          function () { show('Link copied'); },
          function () { show('Copy failed'); }
        );
      } else {
        show('Copy failed');
      }
    });
  });

  // Blog tools. Each one starts from a static example in the HTML, so the page
  // still reads correctly without JavaScript.
  var escapeXml = function (s) {
    return String(s).replace(/[&<>"]/g, function (c) { return { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' }[c]; });
  };
  var field = function (form, name) {
    var el = form.elements.namedItem(name);
    return el ? el.value.trim() : '';
  };

  // Entity triple builder: each fact becomes a list row, a sentence and a branch of the graph.
  document.querySelectorAll('[data-tool="triple"]').forEach(function (tool) {
    var form = tool.querySelector('form');
    var svg = tool.querySelector('.triple-graph');
    var list = tool.querySelector('.triple-list');
    var sentence = tool.querySelector('.triple-sentence');
    var entity = 'Nepal';
    var facts = [['capital', 'Kathmandu'], ['highest point', 'Mount Everest'], ['currency', 'Nepalese rupee']];
    var clip = function (s, n) { return s.length > n ? s.slice(0, n - 1) + '…' : s; };
    var render = function () {
      var cx = 320, cy = 140, rx = 215, ry = 100, n = facts.length, out = '';
      var nodes = facts.map(function (f, k) {
        var a = (-90 + k * 360 / n) * Math.PI / 180;
        var x = cx + rx * Math.cos(a), y = cy + ry * Math.sin(a);
        // Edge label halfway between the circle's edge and the value, not on the circle.
        return { x: x, y: y, t: 0.5 + 23 / Math.hypot(x - cx, y - cy), attr: clip(f[0], 22), val: clip(f[1], 20) };
      });
      nodes.forEach(function (p) {
        out += '<line class="tg-edge" x1="' + cx + '" y1="' + cy + '" x2="' + p.x.toFixed(1) + '" y2="' + p.y.toFixed(1) + '"/>';
      });
      nodes.forEach(function (p) {
        var w = p.val.length * 7.2 + 26;
        out += '<g class="tg-node"><rect x="' + (p.x - w / 2).toFixed(1) + '" y="' + (p.y - 15).toFixed(1) + '" width="' + w.toFixed(1) +
          '" height="30" rx="15"/><text x="' + p.x.toFixed(1) + '" y="' + p.y.toFixed(1) + '">' + escapeXml(p.val) + '</text></g>' +
          '<text class="tg-label" x="' + (cx + (p.x - cx) * p.t).toFixed(1) + '" y="' + (cy + (p.y - cy) * p.t).toFixed(1) + '">' + escapeXml(p.attr) + '</text>';
      });
      out += '<g class="tg-center"><circle cx="' + cx + '" cy="' + cy + '" r="46"/><text x="' + cx + '" y="' + cy + '">' + escapeXml(clip(entity, 14)) + '</text></g>';
      svg.innerHTML = out;
      svg.setAttribute('aria-label', 'Graph of ' + entity + (facts.length ? ': ' + facts.map(function (f) { return f[0] + ' ' + f[1]; }).join('; ') : ''));
      list.innerHTML = facts.map(function (f) {
        return '<li><span class="t-e">' + escapeXml(entity) + '</span><span class="t-a">' + escapeXml(f[0]) + '</span><span class="t-v">' + escapeXml(f[1]) + '</span></li>';
      }).join('');
      var last = facts[facts.length - 1];
      sentence.textContent = last ? 'The ' + last[0] + ' of ' + entity + ' is ' + last[1] + '.' : 'Add a fact to start the graph.';
    };
    form.addEventListener('submit', function (e) {
      e.preventDefault();
      var name = field(form, 'entity'), attr = field(form, 'attribute'), val = field(form, 'val');
      if (!name || !attr || !val) return;
      if (name !== entity) { entity = name; facts = []; }
      facts.push([attr, val]);
      if (facts.length > 6) facts.shift();
      render();
      form.elements.namedItem('attribute').value = '';
      form.elements.namedItem('val').value = '';
      form.elements.namedItem('attribute').focus();
    });
    form.querySelector('[data-reset]').addEventListener('click', function () {
      facts = [];
      entity = field(form, 'entity') || entity;
      render();
    });
  });

  // Entity schema generator: the form becomes JSON-LD for the entity home.
  document.querySelectorAll('[data-tool="schema"]').forEach(function (tool) {
    var form = tool.querySelector('form');
    var out = tool.querySelector('[data-schema-out]');
    var copy = tool.querySelector('[data-copy]');
    var build = function () {
      var type = field(form, 'type');
      var url = field(form, 'url');
      var data = { '@context': 'https://schema.org', '@type': type };
      if (url) data['@id'] = url.replace(/#.*$/, '') + '#' + type.toLowerCase();
      if (field(form, 'name')) data.name = field(form, 'name');
      if (url) data.url = url;
      if (type === 'Person') {
        if (field(form, 'jobTitle')) data.jobTitle = field(form, 'jobTitle');
        if (field(form, 'image')) data.image = field(form, 'image');
      } else if (field(form, 'logo')) {
        data.logo = field(form, 'logo');
      }
      if (type === 'LocalBusiness') {
        if (field(form, 'telephone')) data.telephone = field(form, 'telephone');
        var address = { '@type': 'PostalAddress' };
        if (field(form, 'street')) address.streetAddress = field(form, 'street');
        if (field(form, 'city')) address.addressLocality = field(form, 'city');
        if (field(form, 'country')) address.addressCountry = field(form, 'country').toUpperCase();
        if (Object.keys(address).length > 1) data.address = address;
      }
      if (field(form, 'description')) data.description = field(form, 'description');
      var same = field(form, 'sameAs').split(/\s+/).filter(function (s) { return /^https?:\/\/\S+$/.test(s); });
      if (same.length) data.sameAs = same;
      out.textContent = '<script type="application/ld+json">\n' + JSON.stringify(data, null, 2).replace(/<\//g, '<\\/') + '\n</' + 'script>';
      tool.querySelectorAll('[data-for]').forEach(function (el) { el.hidden = el.getAttribute('data-for').split(' ').indexOf(type) === -1; });
    };
    form.addEventListener('input', build);
    form.addEventListener('change', build);
    form.addEventListener('submit', function (e) { e.preventDefault(); });
    copy.addEventListener('click', function () {
      var done = function () {
        copy.textContent = 'Copied';
        setTimeout(function () { copy.textContent = 'Copy code'; }, 1600);
      };
      if (navigator.clipboard && window.isSecureContext) {
        navigator.clipboard.writeText(out.textContent).then(done, function () {});
      } else {
        var range = document.createRange();
        range.selectNodeContents(out);
        var sel = window.getSelection();
        sel.removeAllRanges();
        sel.addRange(range);
        try { if (document.execCommand('copy')) done(); } catch (err) { /* the code stays selected for manual copy */ }
      }
    });
    build();
  });

  // Entity recognition checker: one name and one URL fill in the check links.
  document.querySelectorAll('[data-tool="check"]').forEach(function (tool) {
    var form = tool.querySelector('form');
    var links = tool.querySelectorAll('[data-check]');
    var update = function () {
      var q = encodeURIComponent(field(form, 'name'));
      var u = encodeURIComponent(field(form, 'url'));
      var urls = {
        google: q && 'https://www.google.com/search?q=' + q,
        wikidata: q && 'https://www.wikidata.org/w/index.php?search=' + q,
        rich: u && 'https://search.google.com/test/rich-results?url=' + u,
        schema: u && 'https://validator.schema.org/#url=' + u
      };
      Array.prototype.forEach.call(links, function (a) {
        var href = urls[a.getAttribute('data-check')];
        if (href) a.href = href;
      });
    };
    form.addEventListener('input', update);
    form.addEventListener('submit', function (e) { e.preventDefault(); });
    update();
  });

  // Keyword to entity breakdown: each sample search swaps the words and the entity facts.
  document.querySelectorAll('[data-tool="query"]').forEach(function (tool) {
    var picks = tool.querySelectorAll('.qa-pick');
    var out = function (name) { return tool.querySelector('[data-f="' + name + '"]'); };
    var fill = function (list, items) {
      list.textContent = '';
      items.split('|').forEach(function (text) {
        var li = document.createElement('li');
        li.textContent = text;
        list.appendChild(li);
      });
    };
    Array.prototype.forEach.call(picks, function (btn) {
      btn.addEventListener('click', function () {
        Array.prototype.forEach.call(picks, function (b) { b.setAttribute('aria-pressed', b === btn ? 'true' : 'false'); });
        out('search').textContent = btn.textContent;
        out('entity').textContent = btn.getAttribute('data-entity');
        out('intent').textContent = 'Intent: ' + btn.getAttribute('data-intent') + '.';
        out('note').textContent = btn.getAttribute('data-note');
        fill(out('words'), btn.getAttribute('data-words'));
        fill(out('facts'), btn.getAttribute('data-facts'));
      });
    });
  });

  // Topical coverage checker: ticked subtopics give a core, outer and total count, plus the open gaps.
  // SERP snippet preview: pixel widths measured in Arial on a canvas, cut at the last whole word.
  document.querySelectorAll('[data-serp-tool]').forEach(function (tool) {
    var el = function (name) { return tool.querySelector('[data-s="' + name + '"]'); };
    var LIMITS = { desktop: { title: 600, desc: 990 }, mobile: { title: 920, desc: 1300 } };
    var FONT = { title: '20px Arial', desc: '14px Arial' };
    var ctx = document.createElement('canvas').getContext('2d');
    var device = 'desktop';
    var MONTHS = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'];
    var px = function (text, font) { ctx.font = font; return Math.round(ctx.measureText(text).width); };
    var fit = function (text, font, limit) {
      if (px(text, font) <= limit) return { text: text, cut: false };
      var words = text.split(/\s+/), out = '';
      for (var i = 0; i < words.length; i++) {
        var next = out ? out + ' ' + words[i] : words[i];
        if (px(next + ' ...', font) > limit) break;
        out = next;
      }
      return { text: (out || text.slice(0, 20)) + ' ...', cut: true };
    };
    var bold = function (node, text, kw) {
      node.textContent = '';
      var terms = kw.toLowerCase().split(/\s+/).filter(function (w) { return w.length > 2; });
      if (!terms.length) { node.textContent = text; return; }
      var re = new RegExp('(' + terms.map(function (w) { return w.replace(/[.*+?^${}()|[\]\\]/g, '\\$&'); }).join('|') + ')', 'gi');
      text.split(re).forEach(function (part, i) {
        if (i % 2) { var b = document.createElement('b'); b.textContent = part; node.appendChild(b); }
        else if (part) node.appendChild(document.createTextNode(part));
      });
    };
    var crumb = function (raw) {
      try {
        var u = new URL(/^https?:\/\//i.test(raw) ? raw : 'https://' + raw);
        var parts = u.pathname.split('/').filter(Boolean).map(function (p) { return decodeURIComponent(p).replace(/[-_]+/g, ' '); });
        return { host: u.hostname.replace(/^www\./, ''), text: [u.protocol + '//' + u.hostname].concat(parts).join(' \u203a ') };
      } catch (e) { return { host: '', text: raw }; }
    };
    var meter = function (name, width, limit, chars) {
      var bar = el(name + '-bar'), ratio = width / limit;
      bar.style.width = Math.min(100, Math.round(ratio * 100)) + '%';
      bar.className = ratio > 1 ? 'is-over' : ratio > 0.9 ? 'is-near' : '';
      el(name + '-count').textContent = width + ' / ' + limit + ' px \u00b7 ' + chars + ' characters';
    };
    var tip = function (list, cls, text) { var li = document.createElement('li'); if (cls) li.className = cls; li.textContent = text; list.appendChild(li); };
    var update = function () {
      var title = el('title').value.trim(), desc = el('desc').value.trim(), kw = el('kw').value.trim();
      var site = el('site').value.trim(), c = crumb(el('url').value.trim());
      var lim = LIMITS[device];
      var dateText = '';
      if (el('date-on').checked && el('date').value) {
        var d = new Date(el('date').value + 'T00:00:00');
        if (!isNaN(d)) dateText = MONTHS[d.getMonth()] + ' ' + d.getDate() + ', ' + d.getFullYear() + ' - ';
      }
      var tW = px(title, FONT.title), dW = px(dateText + desc, FONT.desc);
      meter('title', tW, lim.title, title.length);
      meter('desc', dW, lim.desc, desc.length);
      var t = fit(title || 'Your title tag appears here', FONT.title, lim.title);
      var dFit = fit(dateText + (desc || 'Your meta description appears here.'), FONT.desc, lim.desc);
      el('site-out').textContent = site || c.host || 'Site name';
      el('favicon').textContent = (site || c.host || 'S').charAt(0).toUpperCase();
      el('crumb').textContent = c.text;
      el('title-out').textContent = t.text;
      el('date-out').textContent = dateText;
      bold(el('desc-out'), dFit.text.slice(dateText.length), kw);
      el('card').setAttribute('data-device-view', device);
      var list = el('tips'); list.textContent = '';
      if (!title) tip(list, 'is-bad', 'Add a title tag: Google builds a title link from other page text when the title is missing.');
      else if (t.cut) tip(list, 'is-bad', 'The title is about ' + (tW - lim.title) + ' px too wide for ' + device + ', so Google is likely to cut it. Shorten the end or move the key words forward.');
      else if (title.length < 30) tip(list, 'is-warn', 'The title is short. Add a qualifier, such as the location, the year or the brand.');
      else tip(list, '', 'The title fits the ' + device + ' width.');
      if (!desc) tip(list, 'is-bad', 'Add a meta description: without one, Google picks text from the page for the snippet.');
      else if (dFit.cut) tip(list, 'is-bad', 'The description runs past the ' + device + ' width, so the end will likely be cut. Keep the answer in the first sentence.');
      else if (desc.length < 70) tip(list, 'is-warn', 'The description is short. Add a concrete detail, such as a price, a number or a date.');
      else tip(list, '', 'The description fits the ' + device + ' width.');
      if (desc && (/^[^.!]*\?/.test(desc) || /^(what|how|why|when|where|which|who|is|are|can|do|does)\b/i.test(desc)))
        tip(list, 'is-warn', 'The description opens with a question. Lead with the direct answer instead.');
      if (el('url').value.trim() && !c.host) tip(list, 'is-warn', 'Check the URL: it does not read as a valid web address, so the breadcrumb cannot be built.');
      if (title && desc && title.toLowerCase() === desc.toLowerCase()) tip(list, 'is-warn', 'The title and the description are identical. Use the description to add the answer and a detail.');
      if (kw) {
        var k = kw.toLowerCase();
        if (title && title.toLowerCase().indexOf(k) < 0) tip(list, 'is-warn', 'The focus keyword is missing from the title.');
        else if (title && title.toLowerCase().indexOf(k) > title.length * 0.5) tip(list, 'is-warn', 'The focus keyword sits in the second half of the title. Move it closer to the start.');
        if (desc && desc.toLowerCase().indexOf(k) < 0) tip(list, 'is-warn', 'The focus keyword is missing from the description, so Google has no matching words to bold.');
      }
    };
    var esc = function (s) { return s.replace(/&/g, '&amp;').replace(/"/g, '&quot;').replace(/</g, '&lt;').replace(/>/g, '&gt;'); };
    var copy = function (text) {
      var done = function () { el('copied').textContent = 'Copied'; setTimeout(function () { el('copied').textContent = ''; }, 1800); };
      if (navigator.clipboard && navigator.clipboard.writeText) navigator.clipboard.writeText(text).then(done, function () { window.prompt('Copy this text:', text); });
      else window.prompt('Copy this text:', text);
    };
    el('copy-tags').addEventListener('click', function () {
      copy('<title>' + esc(el('title').value.trim()) + '</title>\n<meta name="description" content="' + esc(el('desc').value.trim()) + '">');
    });
    el('copy-link').addEventListener('click', function () {
      var p = new URLSearchParams();
      ['title', 'desc', 'url', 'site', 'kw'].forEach(function (n) { if (el(n).value.trim()) p.set(n, el(n).value.trim()); });
      if (device !== 'desktop') p.set('device', device);
      copy(location.origin + location.pathname + '?' + p.toString());
    });
    var q = new URLSearchParams(location.search);
    ['title', 'desc', 'url', 'site', 'kw'].forEach(function (n) { if (q.has(n)) el(n).value = q.get(n); });
    if (q.get('device') === 'mobile') device = 'mobile';
    if (q.has('date')) { el('date-on').checked = true; if (/^\d{4}-\d{2}-\d{2}$/.test(q.get('date'))) el('date').value = q.get('date'); }
    var devBtns = tool.querySelectorAll('[data-device]');
    Array.prototype.forEach.call(devBtns, function (btn) {
      btn.setAttribute('aria-pressed', String(btn.getAttribute('data-device') === device));
      btn.addEventListener('click', function () {
        device = btn.getAttribute('data-device');
        Array.prototype.forEach.call(devBtns, function (x) { x.setAttribute('aria-pressed', String(x === btn)); });
        update();
      });
    });
    tool.addEventListener('input', update);
    tool.addEventListener('change', update);
    update();
  });

  // Page or section checker: 4 page rules plus the top-3 search results give a topical map decision.
  document.querySelectorAll('[data-tool="qdp"]').forEach(function (tool) {
    var rule = function (name) { return tool.querySelector('[data-rule="' + name + '"]').checked; };
    var serp = tool.querySelector('[data-qdp-serp]');
    var out = function (name) { return tool.querySelector('[data-f="' + name + '"]'); };
    var update = function () {
      var e = rule('entity'), o = rule('overlap');
      var score = [e, o, rule('pattern'), rule('demand')].filter(Boolean).length;
      var top = serp.value;
      var verdict, why;
      if (score === 0) {
        verdict = 'Tick the rules';
        why = 'Tick each rule your topic passes against its parent topic to see the decision.';
      } else if (!e && !o) {
        verdict = 'Keyword variant';
        why = 'The topic restates its parent in other words, so it belongs on the parent page as a variant phrasing, not as its own heading.';
      } else if (score < 2) {
        verdict = 'Drop or hold';
        why = score + ' of 4 rules pass. Record the topic and test it again when new query data arrives.';
      } else if (top === '') {
        verdict = score >= 3 ? 'Own page' : 'Heading on the parent page';
        why = score + ' of 4 rules pass. Check the top 3 search results to confirm the decision.';
      } else if (Number(top) >= 2) {
        verdict = 'Own page';
        why = top + ' of the top 3 results are pages dedicated to the topic, so searchers expect a page of its own. ' + score + ' of 4 rules pass.';
      } else {
        verdict = 'Heading on the parent page';
        why = 'Only ' + top + ' of the top 3 results are dedicated pages, so broader pages win this search and a heading on the parent page fits. ' + score + ' of 4 rules pass.';
      }
      out('verdict').textContent = verdict;
      out('why').textContent = why;
    };
    tool.addEventListener('change', update);
    update();
  });

  // SEO audit checklist: running score per group and overall, ticks saved in this browser.
  document.querySelectorAll('[data-checklist]').forEach(function (tool) {
    var KEY = 'dbk-seo-audit-checklist';
    var boxes = tool.querySelectorAll('input[data-chk]');
    var saved = {};
    try { saved = JSON.parse(localStorage.getItem(KEY) || '{}') || {}; } catch (e) { saved = {}; }
    Array.prototype.forEach.call(boxes, function (b) { b.checked = !!saved[b.getAttribute('data-chk')]; });
    var update = function () {
      var done = 0;
      tool.querySelectorAll('.chk-group').forEach(function (g) {
        var all = g.querySelectorAll('input[data-chk]');
        var on = g.querySelectorAll('input[data-chk]:checked').length;
        done += on;
        var count = g.querySelector('[data-chk-count]');
        count.textContent = on + ' of ' + all.length + ' passed';
        count.classList.toggle('is-done', on === all.length);
      });
      var pct = boxes.length ? Math.round(done * 100 / boxes.length) : 0;
      tool.querySelector('[data-chk-bar]').style.width = pct + '%';
      tool.querySelector('[data-chk-total]').textContent = done + ' of ' + boxes.length + ' checks passed (' + pct + '%)';
    };
    var store = function () {
      var state = {};
      Array.prototype.forEach.call(boxes, function (b) { if (b.checked) state[b.getAttribute('data-chk')] = 1; });
      try { localStorage.setItem(KEY, JSON.stringify(state)); } catch (e) { /* storage off: ticks last for this visit */ }
    };
    tool.addEventListener('change', function () { store(); update(); });
    tool.querySelector('[data-chk-print]').addEventListener('click', function () { window.print(); });
    tool.querySelector('[data-chk-reset]').addEventListener('click', function () {
      Array.prototype.forEach.call(boxes, function (b) { b.checked = false; });
      store();
      update();
    });
    update();
  });

  // Card carousel: arrows scroll one card at a time and disable at either end.
  document.querySelectorAll('[data-carousel]').forEach(function (box) {
    var track = box.querySelector('.edge-track');
    var btns = box.querySelectorAll('.edge-btn');
    var still = window.matchMedia && window.matchMedia('(prefers-reduced-motion: reduce)').matches;
    var step = function () {
      var card = track.firstElementChild;
      return card ? card.getBoundingClientRect().width + 16 : track.clientWidth;
    };
    var sync = function () {
      var max = track.scrollWidth - track.clientWidth - 2;
      btns[0].disabled = track.scrollLeft <= 2;
      btns[1].disabled = track.scrollLeft >= max;
    };
    Array.prototype.forEach.call(btns, function (btn) {
      btn.addEventListener('click', function () {
        track.scrollBy({ left: Number(btn.getAttribute('data-dir')) * step(), behavior: still ? 'auto' : 'smooth' });
      });
    });
    track.addEventListener('scroll', sync, { passive: true });
    window.addEventListener('resize', sync);
    // A slider inside a hidden tab measures 0 wide until shown, so re-check whenever its size changes.
    if ('ResizeObserver' in window) new ResizeObserver(sync).observe(track);
    sync();
  });

  // Query intent sorter: 15 intents grouped by journey stage, first matching cue wins,
  // queries with no cue go to a review list instead of a guessed group.
  var escHtml = function (s) {
    return String(s).replace(/[&<>"]/g, function (c) { return { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' }[c]; });
  };
  var INTENTS = [
    ['comparison', 'Comparison', 'this against an alternative', /\bvs\.?\b|\bversus\b|\bdifference between\b|\bcompared? (to|with)\b|\balternatives?\b|\bor\b.*\b(better|cheaper)\b/],
    ['cost', 'Cost', 'the price and what drives it', /\bcosts?\b|\bprices?\b|\bpricing\b|\bhow much\b|\bcheap(est)?\b|\bfees?\b|\bquotes?\b|\brates\b/],
    ['governance', 'Governance', 'rules, codes, warranty and law', /\bwarrant(y|ies)\b|\bpermits?\b|\blicen[cs]es?\b|\bcode requirements?\b|\blegal\b|\bregulations?\b|\bcompliance\b|\bcertifi(ed|cation)\b|\blaws?\b|\bpolicy\b|\bpolicies\b|\bguidelines\b/],
    ['diagnosis', 'Diagnosis', 'the fault behind a symptom', /\bwhy (is|does|do|are|did) my\b|\bsigns? of\b|\bsymptoms?\b|\bnot working\b|\bwon'?t\b|\bcauses?\b|\bfailure\b|\bfailing\b|\bnoise\b|\bleak(s|ing)?\b|\bsmok(e|ing)\b|\bdropped\b/],
    ['remediation', 'Remediation', 'to make it right again', /\bfix(es|ing)?\b|\brepair(s|ing)?\b|\btroubleshoot(ing)?\b|\brecover(y)?\b|\bunclog\b|\breset\b/],
    ['acquisition', 'Acquisition', 'to buy, install, hire or sign up', /\bwhere to (buy|get|find)\b|\bbuy(ing)?\b|\bfor sale\b|\bhire\b|\bnear me\b|\bhow to (install|get|order|sign up|apply)\b|\binstall(ation)?\b|\bshop\b|\border\b|\bsign up\b/],
    ['transition', 'Transition', 'to replace, upgrade or switch', /\breplac(e|ing)\b|\bupgrad(e|ing)\b|\bswitch(ing)? (from|to)\b|\bmigrat(e|ion|ing)\b|\bcancel\b|\bconvert(ing)?\b/],
    ['selection', 'Selection', 'which one or which provider', /\bbest\b|\btop \d+\b|\btop rated\b|\bhow to (choose|pick)\b|\bwhich\b|\bbrands?\b|\bcompan(y|ies)\b|\bagenc(y|ies)\b|\bprovider\b/],
    ['value', 'Value', 'the upside and whether it pays', /\bbenefits?\b|\badvantages?\b|\bpros\b|\bworth it\b|\bis .* worth\b|\broi\b|\bwhy (use|choose|get|do)\b|\bimportance\b|\bimportant\b|\bwhy .* matters?\b/],
    ['risk', 'Risk', 'the downside and failure modes', /\bdisadvantages?\b|\bcons\b|\bsafe\b|\brisks?\b|\bdangers?\b|\bdangerous\b|\bside effects?\b|\bproblems?\b|\bdownsides?\b|\bmistakes\b|\bmyths?\b/],
    ['evidence', 'Evidence', 'proof, data and cases', /\bstatistics?\b|\bstats\b|\bcase stud(y|ies)\b|\breviews?\b|\bexamples?\b|\bresults\b|\bresearch\b|\bstudy\b|\bproof\b|^(does|do|can|will) .* work\b/],
    ['taxonomy', 'Taxonomy', 'the kinds, types and sizes', /\btypes? of\b|\bkinds? of\b|\bsizes?\b|\bgrades?\b|\bvariants?\b|\bcategor(y|ies)\b|\blist of\b|\bparts of\b|\bcomponents\b/],
    ['mechanism', 'Mechanism', 'how it works and why', /\bhow (does|do|is|are)\b|\bworks?\b|\bwhy (does|do|is|are)\b|\bprocess\b|\bexplained\b/],
    ['operation', 'Operation', 'to use, maintain or improve it', /\bhow to\b|\bmaintenance\b|\bmaintain\b|\btips\b|\bguide\b|\bstrategy\b|\bchecklist\b|\bbest practices\b|\bsteps\b|\btutorial\b|\btools?\b|\bwriting\b|\boptimi[sz](e|ation)\b|\bimprove\b|\btemplate\b/],
    ['identity', 'Identity', 'a definition and scope', /\bwhat (is|are|does)\b|\bwhat'?s\b|\bmeaning\b|\bmeans\b|\bdefin(e|ition)\b|\bwho is\b|\bwho are\b/]
  ];
  var PHASES = [
    ['Understand', ['identity', 'mechanism', 'taxonomy']],
    ['Evaluate', ['value', 'comparison', 'evidence', 'risk']],
    ['Acquire', ['cost', 'selection', 'acquisition']],
    ['Operate', ['operation']],
    ['Troubleshoot', ['diagnosis', 'remediation']],
    ['Exit', ['transition']],
    ['Context', ['governance']]
  ];
  var PAGE = { cost: 'Service or product page', selection: 'Service or product page', acquisition: 'Service or product page', transition: 'Check the top results' };
  document.querySelectorAll('[data-tool="intents"]').forEach(function (tool) {
    var input = tool.querySelector('[data-int-input]');
    var out = tool.querySelector('[data-int-out]');
    var plain = '';
    var run = function () {
      var seen = {};
      var queries = input.value.split(/\n/).map(function (q) { return q.trim().replace(/\s+/g, ' '); })
        .filter(function (q) { var k = q.toLowerCase(); if (!q || seen[k]) return false; seen[k] = 1; return true; });
      if (!queries.length) {
        out.innerHTML = '<p class="tool-hint">Paste at least one query, one per line.</p>';
        return;
      }
      var groups = {}, review = [];
      queries.forEach(function (q) {
        var low = q.toLowerCase();
        for (var i = 0; i < INTENTS.length; i++) {
          if (INTENTS[i][3].test(low)) { (groups[INTENTS[i][0]] = groups[INTENTS[i][0]] || []).push(q); return; }
        }
        review.push(q);
      });
      var label = {};
      INTENTS.forEach(function (it) { label[it[0]] = it; });
      var used = Object.keys(groups).length;
      var html = '<p class="int-sum"><strong>' + queries.length + ' queries</strong>: ' + (queries.length - review.length) +
        ' sorted into ' + used + ' of 15 intents' + (review.length ? ', ' + review.length + ' to review' : '') + '.</p>';
      var text = ['Query intent sorter: ' + queries.length + ' queries'];
      PHASES.forEach(function (ph) {
        var ids = ph[1].filter(function (id) { return groups[id]; });
        if (!ids.length) return;
        html += '<div class="int-phase"><p class="int-phase-title">' + ph[0] + '</p>';
        text.push('', ph[0].toUpperCase());
        ids.forEach(function (id) {
          var page = PAGE[id] || 'Guide or blog post';
          html += '<div class="int-group"><p class="int-name"><span>' + label[id][1] + '</span><span class="int-want">' + label[id][2] +
            '</span><span class="int-page">' + page + '</span></p><ul>' +
            groups[id].map(function (q) { return '<li>' + escHtml(q) + '</li>'; }).join('') + '</ul></div>';
          text.push(label[id][1] + ' (' + page + '): ' + groups[id].join('; '));
        });
        html += '</div>';
      });
      if (review.length) {
        html += '<div class="int-phase int-review"><p class="int-phase-title">Review by hand</p><div class="int-group"><p class="int-name"><span>No clear cue</span>' +
          '<span class="int-want">a bare entity or brand name, or a phrasing the sorter does not know</span></p><ul>' +
          review.map(function (q) { return '<li>' + escHtml(q) + '</li>'; }).join('') + '</ul></div></div>';
        text.push('', 'REVIEW BY HAND: ' + review.join('; '));
      }
      plain = text.join('\n');
      html += '<div class="tool-actions"><button class="tool-copy" type="button" data-int-copy>Copy as text</button></div>';
      out.innerHTML = html;
    };
    var EXAMPLE = ['what is a turbocharger', 'how does a turbocharger work', 'types of turbochargers', 'rebuilt vs new turbocharger',
      'is a rebuilt turbo worth it', 'turbocharger cost', 'best turbocharger brands', 'where to buy turbochargers',
      'turbocharger maintenance tips', 'signs of a bad turbo', 'how to fix turbo lag', 'replace turbocharger',
      'turbocharger warranty', 'turbo failure causes', 'garrett gt35'].join('\n');
    tool.querySelector('[data-int-run]').addEventListener('click', run);
    tool.querySelector('[data-int-example]').addEventListener('click', function () { input.value = EXAMPLE; run(); });
    tool.querySelector('[data-int-clear]').addEventListener('click', function () {
      input.value = '';
      out.innerHTML = '<p class="tool-hint">Sorted queries appear here, grouped by journey stage and intent.</p>';
    });
    out.addEventListener('click', function (e) {
      var b = e.target.closest('[data-int-copy]');
      if (!b || !navigator.clipboard) return;
      navigator.clipboard.writeText(plain).then(function () { b.textContent = 'Copied'; setTimeout(function () { b.textContent = 'Copy as text'; }, 1500); });
    });
  });

  // Semantic content checker: the measurable writing rules every guide on this site passes.
  var FILLER = ['Additionally', 'As an ai', 'Beacon', 'Discover', 'Dive', 'Delve', 'Embrace', 'Utmost', 'Explore', 'elevate', 'However',
    'Bombastic', 'Boost', 'Buckle up', 'same token', 'Comparatively', 'Enhance', 'Equally', 'Ever-evolving', 'First', 'Furthermore',
    'Get ready', 'Gone are the days', 'Identically', 'light of', 'sea of', 'Lastly', 'Leverage', 'Likewise', 'Look no further', 'Maximize',
    'Moreover', 'Navigating', 'Nested', 'Plethora', 'Realm', 'Secondly', 'Shed light', 'Solace', 'Switching gears', 'Unleash',
    "We've got you covered", 'When it comes to', 'addition', 'conclusion', 'crucial', 'daunting task', 'digital landscape', 'digital world',
    'embark', 'essential', 'go deeper'];
  var STEMMED = { elevate: 1, enhance: 1, boost: 1, maximize: 1, leverage: 1, essential: 1, embark: 1, delve: 1, embrace: 1, unleash: 1, explore: 1, dive: 1 };
  var reEsc = function (s) { return s.replace(/[.*+?^${}()|[\]\\]/g, '\\$&'); };
  var fillerRe = FILLER.map(function (w) {
    var k = w.toLowerCase();
    if (k === 'first') return [w, /(?:^|[.!?]\s+)First\b(?=[,\s])/g];
    var tail = STEMMED[k] ? '(?:s|d|es|ed|ing|ment)?' : '';
    return [w, new RegExp('(?:^|[^A-Za-z-])' + reEsc(w) + tail + '(?![A-Za-z-])', 'gi')];
  });
  var STOP = ' about after also and are because been before being between both but can could does doing each from have having here how into its just more most much once only other over same should some such than that the their them then there these they this those through under until very what when where which while who whom why will with would your you '.split(' ');
  var stop = {};
  STOP.forEach(function (w) { if (w) stop[w] = 1; });
  var content = function (s) {
    return (s.toLowerCase().match(/[a-z0-9]+/g) || []).filter(function (w) { return w.length > 3 && !stop[w]; })
      .map(function (w) { return w.replace(/ies$/, 'y').replace(/(ing|ed)$/, '').replace(/s$/, ''); });
  };
  var sentences = function (s) { return s.replace(/([.!?])\s+(?=[A-Z0-9"'])/g, '$1\n').split('\n').filter(Boolean); };
  document.querySelectorAll('[data-tool="semcheck"]').forEach(function (tool) {
    var phraseIn = tool.querySelector('[data-sc-phrase]');
    var input = tool.querySelector('[data-sc-input]');
    var out = tool.querySelector('[data-sc-out]');
    var run = function () {
      var text = input.value.replace(/\r/g, '');
      var phrase = phraseIn.value.trim().toLowerCase();
      if (!text.trim()) { out.innerHTML = '<p class="tool-hint">Paste a draft to check.</p>'; return; }
      var lines = text.split('\n');
      var checks = [];
      var add = function (status, name, detail, items) { checks.push({ s: status, n: name, d: detail, i: items || [] }); };
      var lineOf = function (idx) { return text.slice(0, idx).split('\n').length; };

      // Headings and the blocks of prose under them.
      var heads = [], blocks = [], buf = [], start = 0;
      var flush = function () { if (buf.length) { blocks.push({ line: start, text: buf.join(' ') }); buf = []; } };
      lines.forEach(function (raw, i) {
        var m = raw.match(/^(#{1,4})\s+(.+)$/);
        var s = raw.trim();
        if (m) { flush(); heads.push({ line: i + 1, lvl: m[1].length, text: m[2].trim(), block: blocks.length }); return; }
        if (!s || /^([-*+]|\d+\.)\s/.test(s) || /^\|/.test(s)) { flush(); return; }
        if (!buf.length) start = i + 1;
        buf.push(s);
      });
      flush();
      var words = (text.match(/\S+/g) || []).length;

      // 1. Heading order.
      if (!heads.length) {
        add('warn', 'Heading order', 'No headings found. Mark them as # H1, ## H2 and ### H3 so the checker can test the structure.');
      } else {
        var h1 = heads.filter(function (h) { return h.lvl === 1; }).length;
        var jumps = [];
        heads.forEach(function (h, k) { if (k && h.lvl > heads[k - 1].lvl + 1) jumps.push('Line ' + h.line + ': H' + heads[k - 1].lvl + ' jumps to H' + h.lvl + ', ' + h.text); });
        if (h1 !== 1) jumps.unshift('The draft has ' + h1 + ' H1 headings; it needs exactly 1.');
        add(jumps.length ? 'fail' : 'pass', 'Heading order', jumps.length ? 'Fix the heading levels below.' : 'One H1, and no heading skips a level.', jumps);
      }

      // 2. Answer-first: the first sentence under a heading shares a content word with it.
      var late = [];
      heads.forEach(function (h) {
        if (h.lvl === 1 || /(references|sources|faq|frequently asked)/i.test(h.text)) return;
        var b = blocks[h.block];
        var next = heads.filter(function (x) { return x.line > h.line; })[0];
        if (!b || (next && b.line > next.line)) { late.push('Line ' + h.line + ': no paragraph under "' + h.text + '"'); return; }
        var first = sentences(b.text)[0];
        var hw = content(h.text), fw = content(first);
        var hit = hw.some(function (w) { return fw.indexOf(w) > -1; });
        if (hw.length && !hit) late.push('Line ' + h.line + ': "' + h.text + '" opens with "' + first.slice(0, 70) + (first.length > 70 ? '...' : '') + '"');
      });
      if (heads.length) add(late.length ? 'warn' : 'pass', 'Answer-first headings',
        late.length ? 'These sections open without the heading\'s own words, so the answer may come too late.' : 'Every section opens with a sentence that answers its heading.', late);

      // 3. Topic phrase under every H2.
      if (!phrase) {
        add('warn', 'Topic phrase coverage', 'Enter the main topic phrase to check it appears in the H1, the opening and every main section.');
      } else {
        var miss = [];
        var low = text.toLowerCase();
        var h1h = heads.filter(function (h) { return h.lvl === 1; })[0];
        if (h1h && h1h.text.toLowerCase().indexOf(phrase) < 0) miss.push('The H1 does not contain "' + phrase + '".');
        if (blocks[0] && blocks[0].text.toLowerCase().indexOf(phrase) < 0) miss.push('The opening paragraph does not contain "' + phrase + '".');
        var h2s = heads.filter(function (h) { return h.lvl === 2 && !/^references/i.test(h.text); });
        h2s.forEach(function (h, k) {
          var end = k + 1 < h2s.length ? h2s[k + 1].line : lines.length + 1;
          var seg = lines.slice(h.line - 1, end - 1).join('\n').toLowerCase();
          if (seg.indexOf(phrase) < 0) miss.push('Line ' + h.line + ': no "' + phrase + '" under "' + h.text + '"');
        });
        var count = low.split(phrase).length - 1;
        add(miss.length ? 'warn' : 'pass', 'Topic phrase coverage',
          (miss.length ? 'Add the phrase where it is missing, in a sentence that reads naturally.' : 'The phrase appears in the H1, the opening and under every main section.') + ' It appears ' + count + ' times in ' + words + ' words.', miss);
      }

      // 4. Paragraph length: 2 to 4 sentences.
      var longP = [];
      blocks.forEach(function (b) { var n = sentences(b.text).length; if (n > 4) longP.push('Line ' + b.line + ': ' + n + ' sentences'); });
      add(longP.length ? 'warn' : 'pass', 'Paragraph length', longP.length ? 'Split these paragraphs so each holds one idea in 2 to 4 sentences.' : 'Every paragraph holds 4 sentences or fewer.', longP);

      // 5. Concrete examples after plural nouns.
      var grounding = (text.match(/\b(such as|including|for example|for instance)\b|\(e\.g\./gi) || []).length;
      var per = words ? (1000 * grounding / words) : 0;
      var enough = words < 150 || per >= 2;
      add(enough ? 'pass' : 'warn', 'Concrete examples',
        grounding + ' example markers, such as "such as" or "for example", which is ' + per.toFixed(1) + ' per 1,000 words.' +
        (enough ? '' : ' Follow plural nouns with a named instance, such as a brand, a number or a place.'));

      // 6. Long sentences that separate the subject from its verb and object.
      var longS = [];
      blocks.forEach(function (b) { sentences(b.text).forEach(function (s) { var n = (s.match(/\S+/g) || []).length; if (n > 32) longS.push('Line ' + b.line + ': ' + n + ' words, "' + s.slice(0, 60) + '..."'); }); });
      add(longS.length ? 'warn' : 'pass', 'Sentence length', longS.length ? 'Shorten these so the subject stays close to its verb and object.' : 'No sentence runs past 32 words.', longS);

      // 7. Dashes and filler words.
      var bad = [];
      lines.forEach(function (l, i) { if (l.indexOf('—') > -1) bad.push('Line ' + (i + 1) + ': em dash'); if (l.indexOf('–') > -1) bad.push('Line ' + (i + 1) + ': en dash'); });
      fillerRe.forEach(function (f) {
        f[1].lastIndex = 0;
        var m;
        while ((m = f[1].exec(text))) bad.push('Line ' + lineOf(m.index + (m[0].length - m[0].replace(/^[^A-Za-z]+/, '').length)) + ': "' + f[0] + '"');
      });
      add(bad.length ? 'fail' : 'pass', 'Dashes and filler words', bad.length ? 'Replace these with plain words and commas.' : 'No dashes and none of the filler words on the list.', bad.slice(0, 20));

      var passed = checks.filter(function (c) { return c.s === 'pass'; }).length;
      var html = '<p class="int-sum"><strong>' + passed + ' of ' + checks.length + ' checks pass</strong> for ' + words + ' words, ' + heads.length + ' headings and ' + blocks.length + ' paragraphs.</p><ul class="sc-list">';
      checks.forEach(function (c) {
        var tag = { pass: 'Pass', warn: 'Review', fail: 'Fix' }[c.s];
        html += '<li class="sc-item is-' + c.s + '"><p class="sc-row"><span class="sc-tag">' + tag + '</span><strong>' + c.n + '</strong></p><p class="sc-detail">' + escHtml(c.d) + '</p>' +
          (c.i.length ? '<ul class="sc-issues">' + c.i.map(function (x) { return '<li>' + escHtml(x) + '</li>'; }).join('') + '</ul>' : '') + '</li>';
      });
      out.innerHTML = html + '</ul>';
    };
    var EXAMPLE = ['# What Is a Rebuilt Turbocharger?', '',
      'A rebuilt turbocharger is a used unit that a technician takes apart, cleans and fits with new wear parts, such as bearings and seals. It costs less than a new unit and suits engines out of warranty.', '',
      '## How Is a Rebuilt Turbocharger Made?', '',
      'A rebuilt turbocharger is made in 4 stages: teardown, cleaning, part replacement and balancing. The technician inspects the housings and replaces any worn part, such as the shaft or the compressor wheel.', '',
      '## Benefits of Buying One', '',
      'However, many buyers ask about quality. Cost is the main benefit, and the price usually sits well below a new unit, which matters for fleets that run older trucks.'].join('\n');
    tool.querySelector('[data-sc-run]').addEventListener('click', run);
    tool.querySelector('[data-sc-example]').addEventListener('click', function () { phraseIn.value = 'rebuilt turbocharger'; input.value = EXAMPLE; run(); });
    tool.querySelector('[data-sc-clear]').addEventListener('click', function () {
      phraseIn.value = ''; input.value = '';
      out.innerHTML = '<p class="tool-hint">Results appear here, with the line of each issue.</p>';
    });
  });

  // Coverage, fan-out, Knowledge Graph readiness and core update recovery checkers share one handler;
  // a tool's data-* attributes rename the two groups and the advice text.
  document.querySelectorAll('[data-tool="coverage"], [data-tool="fanout"], [data-tool="kgready"], [data-tool="corecheck"]').forEach(function (tool) {
    var picks = tool.querySelectorAll('.qa-pick');
    var cfg = {
      unit: tool.getAttribute('data-unit') || 'subtopics',
      a: tool.getAttribute('data-a') || 'core',
      b: tool.getAttribute('data-b') || 'outer',
      why: tool.getAttribute('data-why') || ' Core pages sit closest to what the site sells.',
      done: tool.getAttribute('data-done') || 'Every sample subtopic is covered. Check Search Console queries for questions this list misses.'
    };
    var cap = function (s) { return s.charAt(0).toUpperCase() + s.slice(1); };
    var out = function (name) { return tool.querySelector('[data-f="' + name + '"]'); };
    var boxes = function (name) { return out(name).querySelectorAll('input'); };
    var count = function (name) {
      return Array.prototype.filter.call(boxes(name), function (b) { return b.checked; }).length;
    };
    var gaps = function (name) {
      return Array.prototype.filter.call(boxes(name), function (b) { return !b.checked; })
        .map(function (b) { return b.parentNode.textContent.trim(); });
    };
    var update = function () {
      var core = count('core'), outer = count('outer');
      var nCore = boxes('core').length, nOuter = boxes('outer').length;
      var total = nCore + nOuter, done = core + outer;
      var pct = total ? Math.round(done * 100 / total) : 0;
      out('bar').style.width = pct + '%';
      out('score').textContent = done + ' of ' + total + ' ' + cfg.unit + ' covered (' + pct + '%)';
      out('split').textContent = cap(cfg.a) + ' ' + core + ' of ' + nCore + ', ' + cfg.b + ' ' + outer + ' of ' + nOuter + '.';
      var coreGaps = gaps('core'), outerGaps = gaps('outer');
      out('advice').textContent = coreGaps.length
        ? 'Next ' + cfg.a + ' gaps: ' + coreGaps.slice(0, 3).join(', ') + '.' + cfg.why
        : outerGaps.length
          ? 'The ' + cfg.a + ' set is covered. Next ' + cfg.b + ' gaps: ' + outerGaps.slice(0, 3).join(', ') + '.'
          : cfg.done;
    };
    var fill = function (list, items) {
      list.textContent = '';
      items.split('|').forEach(function (text) {
        var li = document.createElement('li');
        var label = document.createElement('label');
        var box = document.createElement('input');
        box.type = 'checkbox';
        label.appendChild(box);
        label.appendChild(document.createTextNode(' ' + text));
        li.appendChild(label);
        list.appendChild(li);
      });
    };
    Array.prototype.forEach.call(picks, function (btn) {
      btn.addEventListener('click', function () {
        Array.prototype.forEach.call(picks, function (b) { b.setAttribute('aria-pressed', b === btn ? 'true' : 'false'); });
        out('topic').textContent = btn.textContent;
        fill(out('core'), btn.getAttribute('data-core'));
        fill(out('outer'), btn.getAttribute('data-outer'));
        update();
      });
    });
    tool.addEventListener('change', update);
    update();
  });
})();
