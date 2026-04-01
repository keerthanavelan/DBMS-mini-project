// ─── CONFIG ───────────────────────────────────────────────
const BASE_URL = 'http://127.0.0.1:5000';

// ─── STATE ────────────────────────────────────────────────
let currentUser = null;
let activeTrip  = null;
let trips    = [];
let expenses = {};

// ─── AUTH ─────────────────────────────────────────────────
function switchTab(t) {
  document.getElementById('form-in').style.display = t === 'in' ? 'block' : 'none';
  document.getElementById('form-up').style.display = t === 'up' ? 'block' : 'none';
  document.getElementById('tin').classList.toggle('active', t === 'in');
  document.getElementById('tup').classList.toggle('active', t === 'up');
}

async function doLogin() {
  const email = val('li-e'), pass = val('li-p');
  if (!email || !pass) { setErr('li-err', 'Fill in all fields'); return; }
  setErr('li-err', '');
  try {
    const r = await fetch(`${BASE_URL}/api/login`, { 
      method:'POST', 
      headers:{'Content-Type':'application/json'}, 
      body: JSON.stringify({ email, password: pass }) 
    });
    const d = await r.json();
    if (!d.success) { 
      setErr('li-err', d.message || 'Invalid credentials'); 
      return; 
    }
    currentUser = { user_id: d.data.user_id, name: d.data.name, email: d.data.email };
    onLoggedIn();
  } catch (error) { 
    setErr('li-err', 'Cannot reach server'); 
    console.error('Login error:', error);
  }
}

async function doRegister() {
  const name = val('ru-n'), email = val('ru-e'), pass = val('ru-p');
  if (!name || !email || !pass) { setErr('ru-err', 'Fill in all fields'); return; }
  if (pass.length < 6) { setErr('ru-err', 'Password must be 6+ characters'); return; }
  setErr('ru-err', '');
  try {
    const r = await fetch(`${BASE_URL}/api/register`, { 
      method:'POST', 
      headers:{'Content-Type':'application/json'}, 
      body: JSON.stringify({ name, email, password: pass }) 
    });
    const d = await r.json();
    if (!d.success) { 
      setErr('ru-err', d.message || 'Registration failed'); 
      return; 
    }
    currentUser = { user_id: d.data.user_id, name: d.data.name, email: d.data.email };
    onLoggedIn();
  } catch (error) { 
    setErr('ru-err', 'Cannot reach server'); 
    console.error('Registration error:', error);
  }
}

async function onLoggedIn() {
  const n = cap(currentUser.name);
  document.getElementById('navAv').textContent   = n[0].toUpperCase();
  document.getElementById('navName').textContent = n;
  document.getElementById('navbar').style.display     = 'flex';
  document.getElementById('page-login').style.display = 'none';
  await fetchTrips();
  showPage('dashboard');
  toast('Welcome, ' + n + ' ✈');
}

async function fetchTrips() {
  try {
    const r = await fetch(`${BASE_URL}/api/trips?user_id=${currentUser.user_id}`);
    const d = await r.json();
    if (!d.success) {
      toast(d.message || 'Failed to load trips');
      return;
    }
    trips = d.data || [];
    expenses = {};
    for (const trip of trips) {
      await fetchExpensesForTrip(trip.trip_id);
    }
  } catch (error) {
    console.error('Error fetching trips:', error);
    toast('Failed to load trips');
  }
}

async function fetchExpensesForTrip(tripId) {
  try {
    const r = await fetch(`${BASE_URL}/api/expenses?trip_id=${tripId}`);
    const d = await r.json();
    if (d.success) {
      expenses[tripId] = d.data || [];
    } else {
      expenses[tripId] = [];
    }
  } catch (error) {
    console.error('Error fetching expenses:', error);
    expenses[tripId] = [];
  }
}

function logout() {
  currentUser = null; activeTrip = null;
  document.getElementById('navbar').style.display     = 'none';
  document.getElementById('page-login').style.display = 'grid';
  document.querySelectorAll('.page').forEach(p => p.style.display = 'none');
}

// ─── ROUTING ──────────────────────────────────────────────
function showPage(name) {
  document.querySelectorAll('.page').forEach(p => p.style.display = 'none');
  const el = document.getElementById('page-' + name);
  el.style.display = 'block';
  el.style.animation = 'none'; el.offsetHeight; el.style.animation = '';

  document.querySelectorAll('.nl').forEach(l => l.classList.toggle('active',
    (name === 'dashboard' && l.textContent.includes('Dashboard')) ||
    (name === 'flights'   && l.textContent.includes('Flight'))    ||
    (name === 'trips'     && l.textContent.includes('Trip'))
  ));

  if (name === 'dashboard') renderDashboard();
  if (name === 'trips')     renderTrips();
}

// ─── DASHBOARD ────────────────────────────────────────────
async function renderDashboard() {
  const h = new Date().getHours();
  const greet = h < 12 ? 'Good morning' : h < 17 ? 'Good afternoon' : 'Good evening';
  const name  = currentUser ? ', ' + cap(currentUser.name) : '';
  document.getElementById('dash-greeting').textContent = greet + name;

  try {
    const timelineRes = await fetch(`${BASE_URL}/api/analytics/timeline?user_id=${currentUser.user_id}`);
    const timelineData = await timelineRes.json();
    const categoryRes = await fetch(`${BASE_URL}/api/analytics/category-breakdown?user_id=${currentUser.user_id}`);
    const categoryData = await categoryRes.json();
    
    const allExp = timelineData.success ? timelineData.data : [];
    const spent = allExp.reduce((s, e) => s + e.amount, 0);
    const totalB = trips.reduce((s, t) => s + t.total_budget, 0);
    const avgB = trips.length ? Math.round(totalB / trips.length) : 0;
    const util = totalB ? Math.round((spent / totalB) * 100) : 0;

    document.getElementById('dash-stats').innerHTML = `
      <div class="stat-card"><div class="sl">Total Trips</div><div class="sv">${trips.length}</div><div class="ssub">planned</div></div>
      <div class="stat-card"><div class="sl">Total Spent</div><div class="sv">₹${fmtN(spent)}</div><div class="ssub">across all trips</div></div>
      <div class="stat-card"><div class="sl">Avg Budget</div><div class="sv">₹${fmtN(avgB)}</div><div class="ssub">per trip</div></div>
      <div class="stat-card"><div class="sl">Budget Used</div><div class="sv">${util}%</div><div class="ssub">${util > 90 ? '⚠ running low' : 'of total budget'}</div></div>
    `;

    document.getElementById('dash-trips').innerHTML = trips.map(t => {
      const exp = expenses[t.trip_id] || [];
      const sp = exp.reduce((s, e) => s + e.amount, 0);
      const pct = Math.min((sp / t.total_budget) * 100, 100);
      const over = sp > t.total_budget;
      return `
        <div class="dash-trip-row" onclick="showPage('trips')">
          <div class="dtr-top">
            <div class="dtr-route">${t.source} → ${t.destination}</div>
            <div class="dtr-amount">₹${fmtN(sp)} <span style="color:#c0b0a0;font-weight:400">/ ₹${fmtN(t.total_budget)}</span></div>
          </div>
          <div class="dtr-date">${t.departure_date} – ${t.return_date}</div>
          <div class="budget-bar"><div class="budget-fill ${over ? 'over' : ''}" style="width:${pct}%"></div></div>
        </div>`;
    }).join('') +
    `<div style="margin-top:14px;text-align:right">
      <button class="btn-select" onclick="showPage('trips')">Manage trips →</button>
    </div>`;

    const pieData = categoryData.success ? categoryData.data : [];
    const pieExpList = pieData.map(item => ({ category: item.category, amount: item.total_amount }));
    renderPie('dash-pie', 'dash-pie-legend', pieExpList, 60, 60, 44);
    renderBar('dash-bar', trips, expenses);
    const timelineExpList = timelineData.success ? timelineData.data.map(item => ({
      ...item,
      tripSrc: item.source,
      tripDst: item.destination
    })) : [];
    renderTimeline('dash-timeline', timelineExpList);
  } catch (error) {
    console.error('Error rendering dashboard:', error);
    toast('Failed to load dashboard data');
  }
}

// ─── FLIGHTS ──────────────────────────────────────────────
async function searchFlights() {
  const src  = val('s-src');
  const dst  = val('s-dst');
  const cls  = val('s-cls');
  const stpRaw = val('s-stp');
  const maxP = parseFloat(val('s-price')) || Infinity;
  const el   = document.getElementById('fres');

  el.innerHTML = `<div class="loading"><span class="spinner"></span>Searching flights…</div>`;

  try {
    const params = new URLSearchParams();
    if (src) params.append('source', src);
    if (dst) params.append('destination', dst);
    if (cls) params.append('travel_class', cls);
    if (stpRaw === 'zero') params.append('stops', '0');
    else if (stpRaw === 'one') params.append('stops', '1');
    else if (stpRaw === 'two_or_more') params.append('stops', '2');
    if (maxP !== Infinity) params.append('max_price', maxP);

    const r = await fetch(`${BASE_URL}/api/flights/search?${params.toString()}`);
    const d = await r.json();

    if (!d.success) {
      el.innerHTML = `<div class="empty">Error: ${d.message}</div>`;
      return;
    }

    const res = d.data;
    if (!res.length) {
      el.innerHTML = `<div class="empty">No flights found for this route. Try removing some filters.</div>`;
      return;
    }

    const minPrice = Math.min(...res.map(f => f.price));
    const SC = { 0:'s0', 1:'s1', 2:'s2' };
    const SL = { 0:'Direct', 1:'1 Stop', 2:'2+ Stops' };

    el.innerHTML = `<div class="res-label">${res.length} result${res.length > 1 ? 's' : ''} found</div>` +
      res.map(f => {
        const cheapest = f.price === minPrice;
        const urgency  = f.days_left <= 7
          ? `<span class="trend-up">↑ Price rising — ${f.days_left}d left</span>`
          : f.days_left >= 25
          ? `<span class="trend-down">↓ Good time to book</span>`
          : `<span style="color:#c0b0a0;font-size:.68rem">${f.days_left} days at this price</span>`;
        return `
          <div class="flight-card ${cheapest ? 'is-cheapest' : ''}">
            <div class="fc-airline">
              <div class="name">${f.airline_name}${cheapest ? '<span class="cheapest-badge">Cheapest</span>' : ''}</div>
              <div class="num">${f.flight_number}</div>
            </div>
            <div class="fc-route">
              <div class="fc-time">
                <div class="t">${f.departure_time.replace(/_/g,' ')}</div>
                <div class="c">${f.source}</div>
              </div>
              <div class="fc-mid">
                <div class="fc-line"></div>
                <div class="fc-dur">${f.duration} hour(s)</div>
              </div>
              <div class="fc-time">
                <div class="t">${f.arrival_time.replace(/_/g,' ')}</div>
                <div class="c">${f.destination}</div>
              </div>
            </div>
            <div style="text-align:center">
              <span class="stops-badge ${SC[f.stops] || 's1'}">${SL[f.stops] || f.stops}</span>
            </div>
            <div class="fc-fare">
              <div class="price">₹${f.price.toLocaleString()}</div>
              <div class="cls">${f.travel_class}</div>
              <div class="days" style="margin-top:4px">${urgency}</div>
              <button class="btn-select" onclick='saveFlightAsExpense(${JSON.stringify(f).replace(/'/g, "&apos;")})'">Select →</button>
            </div>
          </div>`;
      }).join('');
  } catch (error) {
    console.error('Flight search error:', error);
    el.innerHTML = `<div class="empty">Failed to search flights. Please try again.</div>`;
  }
}

async function saveFlightAsExpense(flight) {
  if (!activeTrip) {
    toast("Select a trip first");
    return;
  }

  const payload = {
    trip_id: activeTrip.trip_id,
    category: "Transport",
    amount: flight.price,
    expense_date: today(), // or let user pick
    description: `${flight.airline_name} ${flight.flight_number} | ${flight.source} → ${flight.destination}`
  };

  const res = await fetch(`${BASE_URL}/api/expenses`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload)
  });

  const data = await res.json();
  toast(data.message);
}

// ─── TRIPS ────────────────────────────────────────────────
async function renderTrips() {
  await fetchTrips();
  const grid = document.getElementById('tgrid');
  grid.innerHTML = trips.map(t => {
    const exp  = expenses[t.trip_id] || [];
    const sp   = exp.reduce((s, e) => s + e.amount, 0);
    const pct  = Math.min((sp / t.total_budget) * 100, 100);
    const over = sp > t.total_budget;
    const sel  = activeTrip && activeTrip.trip_id === t.trip_id;
    return `
      <div class="trip-card ${sel ? 'selected' : ''}" onclick="selectTrip(${t.trip_id})">
        <div class="trip-route">${t.source} → ${t.destination}</div>
        <div class="trip-dates">${t.departure_date} – ${t.return_date}</div>
        <div class="budget-labels">
          <span>₹${fmtN(sp)} spent</span>
          <span>₹${fmtN(t.total_budget)}</span>
        </div>
        <div class="budget-bar">
          <div class="budget-fill ${over ? 'over' : ''}" style="width:${pct}%"></div>
        </div>
        <div class="trip-tags">
          <span class="ttag">${exp.length} expense${exp.length !== 1 ? 's' : ''}</span>
          <span class="ttag ${over ? 'warn' : ''}">${over ? '⚠ Over budget' : '✓ On track'}</span>
        </div>
      </div>`;
  }).join('') + `<div class="add-trip-card" onclick="openModal()">＋ New trip</div>`;
}

function selectTrip(id) {
  activeTrip = trips.find(t => t.trip_id === id);
  renderTrips();
  renderExpensePanel();
  document.getElementById('exp-panel').style.display = 'block';
  setTimeout(() => document.getElementById('exp-panel').scrollIntoView({ behavior:'smooth', block:'start' }), 50);
}

async function renderExpensePanel() {
  if (!activeTrip) return;
  document.getElementById('exp-trip-label').textContent = `${activeTrip.source} → ${activeTrip.destination}`;
  await fetchExpensesForTrip(activeTrip.trip_id);
  const exp = expenses[activeTrip.trip_id] || [];

  try {
    const r = await fetch(`${BASE_URL}/api/trips/budget-summary?trip_id=${activeTrip.trip_id}`);
    const d = await r.json();
    let spent = 0, remaining = 0;
    if (d.success && d.data) {
      spent = d.data.spent;
      remaining = d.data.remaining;
    } else {
      spent = exp.reduce((s, e) => s + e.amount, 0);
      remaining = activeTrip.total_budget - spent;
    }
    document.getElementById('budget-row').innerHTML = `
      <div class="bri"><div class="bl">Total Budget</div><div class="bv">₹${fmtN(activeTrip.total_budget)}</div></div>
      <div class="bri"><div class="bl">Total Spent</div><div class="bv">₹${fmtN(spent)}</div></div>
      <div class="bri"><div class="bl">Remaining</div><div class="bv ${remaining < 0 ? 'over' : ''}">${remaining < 0 ? '-' : ''}₹${fmtN(Math.abs(remaining))}</div></div>
    `;
  } catch (error) {
    const spent = exp.reduce((s, e) => s + e.amount, 0);
    const remaining = activeTrip.total_budget - spent;
    document.getElementById('budget-row').innerHTML = `
      <div class="bri"><div class="bl">Total Budget</div><div class="bv">₹${fmtN(activeTrip.total_budget)}</div></div>
      <div class="bri"><div class="bl">Total Spent</div><div class="bv">₹${fmtN(spent)}</div></div>
      <div class="bri"><div class="bl">Remaining</div><div class="bv ${remaining < 0 ? 'over' : ''}">${remaining < 0 ? '-' : ''}₹${fmtN(Math.abs(remaining))}</div></div>
    `;
  }

  document.getElementById('exp-body').innerHTML = exp.length
    ? exp.map((e) => `
          <tr>
            <td><span class="cat-pill c${e.category}">${e.category}</span></td>
            <td>${e.description || '—'}</td>
            <td>${e.expense_date}</td>
            <td style="font-weight:500;color:var(--terra)">₹${fmtN(e.amount)}</td>
            <td><button class="del-btn" onclick="deleteExpense(${e.expense_id})">✕</button></td>
          </tr>`)
      .join('')
    : `<tr><td colspan="5" class="empty">No expenses yet</td></tr>`;

  const pieData = exp.map(e => ({ category: e.category, amount: e.amount }));
  renderPie('exp-pie', 'exp-pie-legend', pieData, 55, 55, 42);
}

async function deleteExpense(expenseId) {
  if (!activeTrip) return;
  try {
    const r = await fetch(`${BASE_URL}/api/expenses/${expenseId}`, { method: 'DELETE' });
    const d = await r.json();
    if (!d.success) {
      toast(d.message || 'Failed to delete expense');
      return;
    }
    await fetchExpensesForTrip(activeTrip.trip_id);
    renderExpensePanel();
    renderTrips();
    toast('Expense removed');
  } catch (error) {
    console.error('Error deleting expense:', error);
    toast('Failed to delete expense');
  }
}

async function addExpense() {
  if (!activeTrip) { toast('Select a trip first'); return; }
  const cat  = val('ec');
  const desc = val('ed') || 'Expense';
  const amt  = parseFloat(val('ea'));
  const date = val('edt') || today();
  if (!amt || amt <= 0) { toast('Enter a valid amount'); return; }

  try {
    const r = await fetch(`${BASE_URL}/api/expenses`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        trip_id: activeTrip.trip_id,
        category: cat,
        description: desc,
        amount: amt,
        expense_date: date
      })
    });
    const d = await r.json();
    if (!d.success) {
      toast(d.message || 'Failed to add expense');
      return;
    }
    document.getElementById('ea').value = '';
    document.getElementById('ed').value = '';
    await fetchExpensesForTrip(activeTrip.trip_id);
    renderExpensePanel();
    renderTrips();
    toast('Expense added ✓');
  } catch (error) {
    console.error('Error adding expense:', error);
    toast('Failed to add expense');
  }
}

// ─── MODAL ────────────────────────────────────────────────
function openModal()  { document.getElementById('tmod').classList.add('open'); }
function closeModal() { document.getElementById('tmod').classList.remove('open'); }

async function saveTrip() {
  const src    = val('ms');
  const dst    = val('md2');
  const dep    = val('mdep');
  const ret    = val('mret');
  const budget = parseFloat(val('mbgt'));
  if (!dep || !budget) { toast('Enter departure date and budget'); return; }
  if (src === dst)     { toast("Source and destination can't be the same"); return; }

  try {
    const r = await fetch(`${BASE_URL}/api/trips`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        user_id: currentUser.user_id,
        source_city_name: src,
        destination_city_name: dst,
        departure_date: dep,
        return_date: ret || dep,
        total_budget: budget
      })
    });
    const d = await r.json();
    if (!d.success) {
      toast(d.message || 'Failed to create trip');
      return;
    }
    closeModal();
    await fetchTrips();
    renderTrips();
    toast('Trip created 🗺');
  } catch (error) {
    console.error('Error creating trip:', error);
    toast('Failed to create trip');
  }
}

// ─── SHARED RENDERERS ─────────────────────────────────────
const PIE_COLORS = ['#c4995a','#7c4f2a','#5e8c6a','#d4a870','#9e6840','#a8c4ae','#8c7a6a'];

function renderPie(svgId, legId, expList, cx, cy, r) {
  const ct = {};
  expList.forEach(e => { if (e.amount > 0) ct[e.category] = (ct[e.category] || 0) + e.amount; });
  const total = Object.values(ct).reduce((a, b) => a + b, 0) || 1;
  let sa = 0;
  const slices = Object.entries(ct).map(([cat, v], i) => {
    const ang = (v / total) * 360;
    const path = describeArc(cx, cy, r, sa, sa + ang);
    sa += ang;
    return { cat, v, col: PIE_COLORS[i % PIE_COLORS.length], path };
  });
  document.getElementById(svgId).innerHTML = slices.length
    ? slices.map(s => `<path d="${s.path}" fill="${s.col}" stroke="white" stroke-width="2"/>`).join('')
    : `<circle cx="${cx}" cy="${cy}" r="${r}" fill="#ede5d8"/>`;
  document.getElementById(legId).innerHTML = slices.map(s =>
    `<div class="pie-leg-item"><div class="pie-dot" style="background:${s.col}"></div><span>${s.cat} — ₹${fmtN(s.v)}</span></div>`
  ).join('') || '<span style="color:#c8b8a8;font-size:.78rem">No expenses yet</span>';
}

function renderBar(containerId, tripsArr, expObj) {
  const maxB = Math.max(...tripsArr.map(t => t.total_budget), 1);
  document.getElementById(containerId).innerHTML = tripsArr.map(t => {
    const sp = (expObj[t.trip_id] || []).reduce((a, e) => a + e.amount, 0);
    const bh = (t.total_budget / maxB) * 100;
    const sh = (sp / maxB) * 100;
    return `<div class="bar-col">
      <div class="bar-pair">
        <div class="bar" style="height:${bh}px;background:var(--mist)"></div>
        <div class="bar" style="height:${sh}px;background:var(--clay)"></div>
      </div>
      <div class="bar-label">${t.source.slice(0,3)}→${t.destination.slice(0,3)}</div>
    </div>`;
  }).join('') || '<span style="color:#c8b8a8;font-size:.8rem">No trips yet</span>';
}

function renderTimeline(containerId, expList) {
  const catColors = { Food:'#c4995a', Transport:'#3d6fa8', Hotel:'#5e8c6a', Activity:'#7a5a9e', Misc:'#8c7a6a' };
  document.getElementById(containerId).innerHTML = expList.length
    ? `<div class="timeline-wrap">` + expList.map(e => `
        <div class="tl-item">
          <div class="tl-dot" style="background:${catColors[e.category] || '#c4995a'}"></div>
          <div class="tl-date">${e.expense_date}</div>
          <div class="tl-main">
            <div class="tl-desc">${e.description}</div>
            <div class="tl-trip">${e.tripSrc} → ${e.tripDst}</div>
          </div>
          <span class="cat-pill c${e.category}" style="margin-right:10px">${e.category}</span>
          <div class="tl-amt">₹${fmtN(e.amount)}</div>
        </div>`).join('') + `</div>`
    : '<span style="color:#c8b8a8;font-size:.82rem">No expenses across any trip yet</span>';
}

// ─── UTILS ────────────────────────────────────────────────
function val(id)  { return document.getElementById(id).value.trim(); }
function setErr(id, msg) { document.getElementById(id).textContent = msg; }
function cap(s)   { return s.charAt(0).toUpperCase() + s.slice(1); }
function today()  { return new Date().toISOString().split('T')[0]; }
function fmtN(n)  { return Number(n).toLocaleString('en-IN'); }

let toastTimer;
function toast(msg) {
  const t = document.getElementById('tst');
  t.textContent = msg;
  t.classList.add('show');
  clearTimeout(toastTimer);
  toastTimer = setTimeout(() => t.classList.remove('show'), 2600);
}

function pxy(cx, cy, r, deg) {
  const rad = (deg - 90) * Math.PI / 180;
  return { x: cx + r * Math.cos(rad), y: cy + r * Math.sin(rad) };
}
function describeArc(cx, cy, r, s, e) {
  if (e - s >= 360) e = 359.99;
  const S = pxy(cx, cy, r, s), E = pxy(cx, cy, r, e);
  return `M ${cx} ${cy} L ${S.x} ${S.y} A ${r} ${r} 0 ${e - s > 180 ? 1 : 0} 1 ${E.x} ${E.y} Z`;
}

document.getElementById('tmod').addEventListener('click', function(e) {
  if (e.target === this) closeModal();
});