// Seed Heimdall with the same services Homepage lists.
//
// Heimdall 2.8 keeps apps in SQLite, so there is no config file to commit. Its
// REST API (Route::resource('api/item')) accepts POST /api/item with a `tags`
// array of tag titles, creating missing tags automatically.
//
// Icon handling matters: storelogic() runs any http(s) `icon` URL through an
// SSRF guard that rejects private addresses, and a failed fetch throws a
// ValidationException that aborts the whole create. So every CDN icon is probed
// first and only verified ones are sent. Apps in Heimdall's own library
// (supportedapps.json, 681 entries) send `appid` instead and use the bundled
// icon, with no network call at all.
//
// Usage: node seed-heimdall.js [--dry-run]
const fs = require('fs');
const path = require('path');
const yaml = require('/home/hermes/.hermes/cache/scratch/node_modules/js-yaml');

const SCRATCH = process.env.SCRATCH || '/home/hermes/.hermes/cache/scratch';
const HEIMDALL = 'http://10.0.0.128:3012';
const SERVICES = path.join(SCRATCH, 'homelab-komodo/homepage/config/services.yaml');
const SUPPORTED = path.join(SCRATCH, 'supportedapps.json');
const DRY = process.argv.includes('--dry-run');

// CDN icons for the services Heimdall has no built-in icon for. Only the ones
// that probe 200 are actually sent.
const CDN = {
  'Homepage': 'https://cdn.jsdelivr.net/npm/simple-icons@latest/icons/homepage.svg',
  'Glance': 'https://cdn.jsdelivr.net/npm/simple-icons@latest/icons/glance.svg',
  'Dashy': 'https://cdn.jsdelivr.net/npm/@mdi/svg@latest/svg/view-dashboard.svg',
  'Komodo': 'https://cdn.jsdelivr.net/gh/selfhst/icons@main/svg/komodo.svg',
  'pc1': 'https://cdn.jsdelivr.net/npm/simple-icons@latest/icons/proxmox.svg',
  'pc6': 'https://cdn.jsdelivr.net/npm/simple-icons@latest/icons/proxmox.svg',
  'pc9': 'https://cdn.jsdelivr.net/npm/simple-icons@latest/icons/proxmox.svg',
  'pve (pc8)': 'https://cdn.jsdelivr.net/npm/simple-icons@latest/icons/proxmox.svg',
  'Ollama': 'https://cdn.jsdelivr.net/npm/simple-icons@latest/icons/ollama.svg',
  'Spend OpenRouter': 'https://cdn.jsdelivr.net/npm/simple-icons@latest/icons/openrouter.svg',
  'Pi-hole pc8': 'https://cdn.jsdelivr.net/npm/simple-icons@latest/icons/pihole.svg',
  'Pi-hole pc9': 'https://cdn.jsdelivr.net/npm/simple-icons@latest/icons/pihole.svg',
  'UniFi Network': 'https://cdn.jsdelivr.net/npm/simple-icons@latest/icons/ubiquiti.svg',
  'Sonos': 'https://cdn.jsdelivr.net/npm/simple-icons@latest/icons/sonos.svg',
  'Unraid Tower': 'https://cdn.jsdelivr.net/gh/selfhst/icons@main/svg/unraid.svg',
  'Hermes Agent': 'https://cdn.jsdelivr.net/npm/@mdi/svg@latest/svg/robot.svg',
  'DiskSpeed': 'https://cdn.jsdelivr.net/npm/@mdi/svg@latest/svg/harddisk.svg',
  'iVentoy': 'https://cdn.jsdelivr.net/npm/@mdi/svg@latest/svg/server-network.svg',
  'Grovemap': 'https://cdn.jsdelivr.net/npm/@mdi/svg@latest/svg/earth.svg',
};

const norm = (s) => s.toLowerCase().replace(/[^a-z0-9]/g, '');

async function probe(url) {
  try {
    const r = await fetch(url, { method: 'GET', redirect: 'follow' });
    return r.status === 200;
  } catch {
    return false;
  }
}

// Heimdall runs its API routes through Laravel's web middleware, so POST needs
// a CSRF token. Laravel accepts the URL-decoded XSRF-TOKEN cookie back in the
// X-XSRF-TOKEN header, which is what its own JS does. Keep one session cookie
// jar across every request or the session and the token fall out of sync.
let cookies = {};

async function primeSession() {
  const r = await fetch(`${HEIMDALL}/`, { redirect: 'manual' });
  const raw = r.headers.getSetCookie ? r.headers.getSetCookie() : [];
  for (const c of raw) {
    const [pair] = c.split(';');
    const idx = pair.indexOf('=');
    if (idx > 0) cookies[pair.slice(0, idx).trim()] = pair.slice(idx + 1).trim();
  }
  if (!cookies['XSRF-TOKEN']) throw new Error('ingen XSRF-TOKEN-cookie fra GET /');
  return cookies;
}

const cookieHeader = () =>
  Object.entries(cookies).map(([k, v]) => `${k}=${v}`).join('; ');

async function post(item) {
  const r = await fetch(`${HEIMDALL}/api/item`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      Accept: 'application/json',
      Cookie: cookieHeader(),
      'X-XSRF-TOKEN': decodeURIComponent(cookies['XSRF-TOKEN']),
      'X-Requested-With': 'XMLHttpRequest',
    },
    body: JSON.stringify(item),
  });
  const body = await r.text();
  return { status: r.status, body };
}

// resolveTags() creates tags WITHOUT pinned, so a freshly seeded category is
// invisible on the dashboard: the 'categories' branch of ItemController::dash()
// queries items that have children AND are themselves pinned. Categories
// therefore need pinning after seeding. /api/item does not expose tag ids and
// PUT /api/item/{id} is an empty stub in 2.8.3, so that step is a small SQL
// pass; see tools/README.md in the repo.
async function pinItem(id) {
  const r = await fetch(`${HEIMDALL}/pin/${id}`, {
    headers: { Cookie: cookieHeader(), 'X-Requested-With': 'XMLHttpRequest' },
    redirect: 'manual',
  });
  return r.status;
}

(async () => {
  const supported = JSON.parse(fs.readFileSync(SUPPORTED, 'utf8')).apps;
  const byName = new Map(supported.map((a) => [norm(a.name), a.appid]));

  const raw = yaml.load(fs.readFileSync(SERVICES, 'utf8'));
  const services = [];
  for (const entry of raw) {
    const group = Object.keys(entry)[0];
    for (const s of entry[group]) {
      const name = Object.keys(s)[0];
      const v = s[name] || {};
      services.push({ group, name, url: v.href || '', description: v.description || '' });
    }
  }
  console.log(`tjenester i services.yaml: ${services.length}`);

  // Resolve the icon for each service once, up front.
  const plan = [];
  let builtIn = 0, cdnOk = 0, noIcon = 0;
  for (const [i, s] of services.entries()) {
    const item = {
      title: s.name,
      url: s.url,
      // appdescription, NOT description. storelogic() overwrites `description`
      // with a JSON config blob (Item::checkConfig), so a plain string sent
      // there is discarded. The text shown on the tile lives in appdescription.
      appdescription: s.description,
      tags: [s.group],
      order: i,
      pinned: true,
    };
    const appid = byName.get(norm(s.name));
    if (appid) {
      item.appid = appid;
      builtIn++;
    } else if (CDN[s.name]) {
      if (await probe(CDN[s.name])) {
        item.icon = CDN[s.name];
        cdnOk++;
      } else {
        noIcon++;
        console.log(`  ! ikon 404, sender uten: ${s.name}`);
      }
    } else {
      noIcon++;
    }
    plan.push(item);
  }
  console.log(`innebygd ikon: ${builtIn}   cdn-ikon: ${cdnOk}   uten ikon: ${noIcon}`);

  if (DRY) {
    console.log('\n-- dry run, ingenting sendt. første tre:');
    console.log(JSON.stringify(plan.slice(0, 3), null, 1));
    return;
  }

  // Idempotent: skip anything already present, so a re-run after a partial
  // failure cannot create duplicates.
  const existing = new Set(
    (await (await fetch(`${HEIMDALL}/api/item`)).json()).map((x) => x.title)
  );
  if (existing.size) {
    console.log(`\nallerede i Heimdall, hopper over: ${[...existing].join(', ')}`);
  }

  await primeSession();
  console.log('sesjon primet, sender...');

  let ok = 0, skipped = 0;
  const failed = [];
  for (const item of plan) {
    if (existing.has(item.title)) { skipped++; continue; }
    const r = await post(item);
    if (r.status >= 200 && r.status < 300 && r.body.includes('OK')) ok++;
    else failed.push({ title: item.title, status: r.status, body: r.body.slice(0, 160) });
    await new Promise((res) => setTimeout(res, 120));
  }
  console.log(`\nopprettet: ${ok}   hoppet over: ${skipped}   mislyktes: ${failed.length}`);
  if (failed.length) {
    console.log('feilet:');
    for (const f of failed) console.log('  ', JSON.stringify(f));
  }

  const list = await (await fetch(`${HEIMDALL}/api/item`)).json();
  console.log(`\nGET /api/item gir nå ${list.length} apper`);
  const tags = new Set(list.flatMap((x) => x.tags || []));
  console.log('kategorier:', [...tags].join(', '));
})();