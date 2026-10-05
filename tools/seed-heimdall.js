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
const yaml = require('js-yaml');

// Repo root by default, so `node tools/seed-heimdall.js` works with no
// environment set. Override with SCRATCH when services.yaml lives elsewhere.
const SCRATCH = process.env.SCRATCH || path.join(__dirname, '..');
const HEIMDALL = 'http://10.0.0.128:3012';
const SERVICES = path.join(SCRATCH, 'homepage/config/services.yaml');
// Heimdall's own app catalogue, committed next to this script so a fresh
// checkout works offline. Falls back to the scratch copy if absent.
const SUPPORTED = fs.existsSync(path.join(__dirname, 'supportedapps.json'))
  ? path.join(__dirname, 'supportedapps.json')
  : path.join(SCRATCH, 'supportedapps.json');
const DRY = process.argv.includes('--dry-run');
// Remove items that exist in Heimdall but no longer in services.yaml. Off by
  // default: pruning deletes data, so it must be asked for explicitly.
  // NOTE: on Heimdall 2.8.3 DELETE /api/item/{id} returns HTTP 500 for every
  // existing row, so this only DETECTS orphans — the actual removal is a
  // database operation. See references/heimdall-tweaks.md in the
  // homelab-infrastructure-automation skill.
const PRUNE = process.argv.includes('--prune');

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
  'Netdata Cloud': 'https://cdn.jsdelivr.net/npm/simple-icons@latest/icons/netdata.svg',
  'Netdata Tower': 'https://cdn.jsdelivr.net/npm/simple-icons@latest/icons/netdata.svg',
  'Netdata pc6': 'https://cdn.jsdelivr.net/npm/simple-icons@latest/icons/netdata.svg',
  'Netdata pve': 'https://cdn.jsdelivr.net/npm/simple-icons@latest/icons/netdata.svg',
  'Netdata pc9': 'https://cdn.jsdelivr.net/npm/simple-icons@latest/icons/netdata.svg',
  'Grafana CT109': 'https://cdn.jsdelivr.net/npm/simple-icons@latest/icons/grafana.svg',
  // Scanopy has no icon in Simple Icons or selfh.st; falls back to a generic
  // tile until a real brand asset exists.
  'Scanopy': 'https://cdn.jsdelivr.net/npm/@mdi/svg@latest/svg/sitemap.svg',
  'Crafty': 'https://cdn.jsdelivr.net/npm/@mdi/svg@latest/svg/gamepad-variant.svg',
  'Cleanuparr': 'https://cdn.jsdelivr.net/npm/@mdi/svg@latest/svg/delete-sweep.svg',
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

// The route is DELETE /api/item/{id} keyed on the numeric id, not the title.
// Sending one without the CSRF token answers 419, which is how the route was
// confirmed to exist at all.
async function del(id) {
  const r = await fetch(`${HEIMDALL}/api/item/${id}`, {
    method: 'DELETE',
    headers: {
      Accept: 'application/json',
      Cookie: cookieHeader(),
      'X-XSRF-TOKEN': decodeURIComponent(cookies['XSRF-TOKEN']),
      'X-Requested-With': 'XMLHttpRequest',
    },
  });
  return { status: r.status, body: await r.text() };
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
  const noIconList = [];
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
        noIconList.push(`${s.name} (ikon-URL 404)`);
      }
    } else {
      noIcon++;
      noIconList.push(`${s.name} (ikke i biblioteket, ingen CDN-URL)`);
    }
    plan.push(item);
  }
  console.log(`innebygd ikon: ${builtIn}   cdn-ikon: ${cdnOk}   uten ikon: ${noIcon}`);
  if (noIconList.length) {
    console.log('  mangler ikon:');
    for (const n of noIconList) console.log(`    - ${n}`);
  }

  if (DRY) {
    console.log('\n-- dry run, ingenting sendt. første tre:');
    console.log(JSON.stringify(plan.slice(0, 3), null, 1));
    return;
  }

  // /api/item does not include the numeric id — only `appid`, which is null for
    // apps with no built-in icon. The rendered dashboard page does carry it, as
    // data-id on each <section class="item-container">, so scrape the id from
    // there rather than guessing or touching the database.
    async function idFromDashboard(title) {
      const html = await (await fetch(`${HEIMDALL}/`)).text();
      const re = new RegExp(
        `data-name="${title.replace(/[.*+?^\${}()|[\]\\]/g, '\\$&')}"[^>]*data-id="(\\d+)"`,
        'i'
      );
      const m = html.match(re);
      return m ? m[1] : null;
    }

    // The existing check needs the id, not just the title, because pruning deletes
    // by id. Fetch the full objects once and key on both.
    const current = await (await fetch(`${HEIMDALL}/api/item`)).json();
    const existing = new Map(current.map((x) => [x.title, x.id]));
    const idOf = new Map(current.map((x) => [x.title, x.id]));
    if (existing.size) {
      console.log(`\nalle rede i Heimdall, hopper over: ${[...existing.keys()].join(', ')}`);
    }

    const wanted = new Set(plan.map((i) => i.title));
    const orphans = [...existing.keys()].filter((t) => !wanted.has(t));
    if (orphans.length) {
      console.log(`\ndisse finnes i Heimdall, men ikke i services.yaml: ${orphans.join(', ')}`);
      if (!PRUNE) {
        console.log('  (kjør med --prune for å fjerne dem)');
      } else {
        await primeSession();
        for (const title of orphans) {
          const id = await idFromDashboard(title);
          if (!id) { console.log(`  FEIL fant ikke id for ${title} i dashboarden`); continue; }
          const r = await del(id);
          console.log(`  ${r.status >= 200 && r.status < 300 ? 'fjernet' : 'FEIL'} ${title} (id ${id}, HTTP ${r.status})`);
          await new Promise((res) => setTimeout(res, 120));
        }
      }
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