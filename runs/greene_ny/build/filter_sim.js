// Click-test the dashboard filters in isolation. Loads the live
// dashboard/data.js, reproduces app.js prep()/applyFilters() with the
// new click-to-select semantics, and confirms every filter type
// changes the visible count appropriately.
const fs = require('fs');

global.window = {};
eval(fs.readFileSync('dashboard/data.js', 'utf8'));
const records = window.LEADS.records;
const total = records.length;

const FCL_TYPES = {
  foreclosure_notice: 1, tax_foreclosure_notice: 1, notice_of_sale: 1,
  final_judgment_of_foreclosure: 1, lis_pendens: 1, mechanics_lien: 1,
};
const ESTATE_TYPES = {
  estate_titled_property: 1, letters_testamentary: 1,
  letters_of_administration: 1, estate_notice: 1,
};
const TAX_LIEN_TYPES = { state_tax_lien: 1, federal_tax_lien: 1 };

function parseDate(s) {
  if (!s) return null;
  const m = String(s).match(/^(\d{4})-(\d{2})-(\d{2})/);
  if (m) return new Date(+m[1], +m[2]-1, +m[3]);
  const d = new Date(s); return isNaN(d.getTime()) ? null : d;
}
const TODAY = (() => { const d = new Date(); d.setHours(0,0,0,0); return d; })();

records.forEach(r => {
  r.signal_types = r.signal_types || [];
  r.signals = r.signals || [];
  const fs = (r.signals||[]).find(x => FCL_TYPES[x.signal_type]);
  r._isFcl = !!fs;
  const sd = fs ? parseDate(fs.sale_date) : null;
  r._days = sd ? Math.round((sd - TODAY) / 86400000) : null;
  r._assessed = Number(r.assessed_value) || 0;
  r._review = r.parcel_resolution_status === 'REVIEW_REQUIRED';
  r._isNew = !!r.is_new;
  r._daysSince = typeof r.days_since_event === 'number' ? r.days_since_event : null;
  r._last30 = !!r.last_30_days;
  r._isHistorical = !!r.is_historical;
  r._stackDepth = Number(r.stack_depth || r.signal_count || 1);
  r._blob = [r.owner_name, r.property_full_address, r.mailing_full_address]
    .join(' ').toLowerCase();
});

function defaultState() {
  return {
    search: '', saleWindow: 'any', recordedWindow: 'any',
    valMin: null, valMax: null,
    signals: {},      // empty = no filter (show all)
    owners:  {},      // empty = no filter (show all)
    absentee: false, oos: false, review: false,
    multiOnly: false, newOnly: false, currentOnly: false,
  };
}

function applyFilters(state) {
  const sigSel = Object.keys(state.signals).filter(k => state.signals[k]);
  const ownSel = Object.keys(state.owners).filter(k => state.owners[k]);
  const anySig = sigSel.length > 0, anyOwn = ownSel.length > 0;
  const win  = state.saleWindow     === 'any' ? null : Number(state.saleWindow);
  const rwin = state.recordedWindow === 'any' ? null : Number(state.recordedWindow);
  return records.filter(r => {
    if (state.review && !r._review) return false;
    if (anySig && !(r.signal_types||[]).some(t => state.signals[t])) return false;
    if (anyOwn && !state.owners[r.owner_type || 'UNKNOWN']) return false;
    if (state.absentee && !r.absentee_owner_flag) return false;
    if (state.oos && !r.out_of_state_owner_flag) return false;
    if (state.multiOnly && r._stackDepth < 2) return false;
    if (state.newOnly && !r._isNew) return false;
    if (state.currentOnly && r._isHistorical) return false;
    if (win != null && (!r._isFcl || r._days == null || r._days < 0 || r._days > win)) return false;
    if (rwin != null) {
      if (r._daysSince == null) return false;
      if (rwin === 0 && r._daysSince !== 0) return false;
      if (rwin > 0 && (r._daysSince < 0 || r._daysSince > rwin)) return false;
    }
    if (state.valMin != null && r._assessed < state.valMin) return false;
    if (state.valMax != null && (r._assessed > state.valMax || r._assessed === 0)) return false;
    if (state.search && r._blob.indexOf(state.search) < 0) return false;
    return true;
  });
}

const scenarios = [
  ['Default (no filters, click-to-select empty)', () => defaultState()],
  ['Signal: notice_of_sale only',
    () => { const s=defaultState(); s.signals.notice_of_sale=true; return s; }],
  ['Signal: lis_pendens only',
    () => { const s=defaultState(); s.signals.lis_pendens=true; return s; }],
  ['Signal: probate (letters_of_admin + letters_test + estate_notice)',
    () => { const s=defaultState();
      s.signals.letters_of_administration=true; s.signals.letters_testamentary=true; s.signals.estate_notice=true; return s; }],
  ['Signal: tax_foreclosure_notice only',
    () => { const s=defaultState(); s.signals.tax_foreclosure_notice=true; return s; }],
  ['Owner type: ESTATE only',
    () => { const s=defaultState(); s.owners.ESTATE=true; return s; }],
  ['Owner type: LIFE_ESTATE only',
    () => { const s=defaultState(); s.owners.LIFE_ESTATE=true; return s; }],
  ['Owner type: ENTITY only',
    () => { const s=defaultState(); s.owners.ENTITY=true; return s; }],
  ['Owner type: INDIVIDUAL only',
    () => { const s=defaultState(); s.owners.INDIVIDUAL=true; return s; }],
  ['Owner type: UNKNOWN only',
    () => { const s=defaultState(); s.owners.UNKNOWN=true; return s; }],
  ['Absentee owners only',
    () => { const s=defaultState(); s.absentee=true; return s; }],
  ['Out-of-state owners only',
    () => { const s=defaultState(); s.oos=true; return s; }],
  ['Review required only',
    () => { const s=defaultState(); s.review=true; return s; }],
  ['Multi-year stack only (stack_depth ≥ 2)',
    () => { const s=defaultState(); s.multiOnly=true; return s; }],
  ['NEW today (recorded_date == today)',
    () => { const s=defaultState(); s.recordedWindow='0'; s.newOnly=true; return s; }],
  ['Last 30 days',
    () => { const s=defaultState(); s.recordedWindow='30'; return s; }],
  ['Last 90 days',
    () => { const s=defaultState(); s.recordedWindow='90'; return s; }],
  ['Last 365 days',
    () => { const s=defaultState(); s.recordedWindow='365'; return s; }],
  ['Current cycle only (not historical)',
    () => { const s=defaultState(); s.currentOnly=true; return s; }],
  ['Foreclosures sale window 21d',
    () => { const s=defaultState(); s.saleWindow='21'; return s; }],
  ['Foreclosures sale window 60d',
    () => { const s=defaultState(); s.saleWindow='60'; return s; }],
  ['Min assessed value 50000',
    () => { const s=defaultState(); s.valMin=50000; return s; }],
  ['Max assessed value 25000',
    () => { const s=defaultState(); s.valMax=25000; return s; }],
  ['Search "ROUTE 23"',
    () => { const s=defaultState(); s.search='route 23'; return s; }],
  ['Search "ATHENS"',
    () => { const s=defaultState(); s.search='athens'; return s; }],
  ['Search "DILLMAN"',
    () => { const s=defaultState(); s.search='dillman'; return s; }],
  ['Stacked: ESTATE + probate signal',
    () => { const s=defaultState();
      s.owners.ESTATE=true;
      s.signals.letters_of_administration=true; s.signals.letters_testamentary=true; s.signals.estate_notice=true;
      return s; }],
];

console.log(`Total records: ${total}\n`);
console.log('| Filter scenario                                                | Visible | Δ        |');
console.log('|----------------------------------------------------------------|---------|----------|');
const failures = [];
scenarios.forEach(([name, make]) => {
  const state = make();
  const out = applyFilters(state);
  const ch = out.length === total ? '— same'
    : (out.length < total ? `−${total - out.length}` : `+${out.length - total}`);
  console.log(`| ${name.padEnd(62)} | ${String(out.length).padStart(7)} | ${ch.padEnd(8)} |`);
  // Sanity rule: ANY non-default filter MUST change the count
  const isDefault = name.startsWith('Default');
  if (!isDefault && out.length === total)
    failures.push(`${name} did not change count`);
  if (out.length < 0) failures.push(`${name} produced negative count`);
});

console.log('\nFailures:', failures.length ? failures : 'none — every filter changed visible count');

console.log('\n--- Default sort top-of-list check (urgency tier) ---');
// Compute tier per record (mirror urgencyTier from app.js)
function tier(r) {
  if (r._isFcl && r._days != null && r._days >= 0 && r._days <= 21) return 1;
  if (r._isFcl && r._days != null && r._days > 21 && r._days <= 60) return 2;
  if (!r._isHistorical) return r._stackDepth >= 2 ? 3 : 4;
  if (r._stackDepth >= 2) return 5;
  return r._daysSince != null ? 6 : 7;
}
const tierCounts = {};
records.forEach(r => { tierCounts[tier(r)] = (tierCounts[tier(r)]||0)+1; });
console.log('Tier counts:', tierCounts);

// Top-10 of default sort
const sorted = records.slice().map(r => ({...r, _tier: tier(r)})).sort((a,b) => {
  if (a._tier !== b._tier) return a._tier - b._tier;
  const ad = a._daysSince==null?1e9:a._daysSince;
  const bd = b._daysSince==null?1e9:b._daysSince;
  if (ad !== bd) return ad - bd;
  if (a._stackDepth !== b._stackDepth) return b._stackDepth - a._stackDepth;
  return b._assessed - a._assessed;
});
console.log('\nTop-10 default sort:');
sorted.slice(0, 10).forEach((r,i) => {
  console.log(`  ${i+1}. tier=${r._tier} hist=${r._isHistorical} stack=${r._stackDepth} owner=${r.owner_type} sig=${r.signal_types[0]} owner_name="${r.owner_name}"`);
});
