// Apply per-category colours and a deterministic order to Heimdall.
//
// Heimdall 2.8.3 has no working item-update route: PUT /api/item/{id} is an empty
// stub, so an existing item's colour cannot be changed over the API. Its SQLite
// database is the only place these two fields can be set.
//
// Schema facts this depends on, verified against a live copy:
//   - the tables are `items` and `item_tag`; there is no `tags` table. A tag IS
//     an item, linked by item_tag.tag_id -> items.id.
//   - type=0 marks an application, type=1 marks a tag, id=0 is `app.dashboard`.
//   - `order` is a reserved SQL word and must be quoted in every statement.
//   - `description` is overwritten by storelogic() with a JSON config blob, so
//     visible text belongs in `appdescription`. Colour has no such problem.
//
// Usage:
//   node heimdall-style.js <app.sqlite>          # dry run, writes nothing
//   node heimdall-style.js <app.sqlite> --apply  # writes; stop Heimdall first
//
// Requires Node 22+ for node:sqlite. Copy the file out of the running volume,
// run it against the copy, then push it back.
const { DatabaseSync } = require('node:sqlite');

// Dark, desaturated tones: the white icon and label sit on top, so these stay
// dark enough to keep white text legible in Heimdall's dark theme.
const CATEGORY_COLOUR = {
  'Homelab': '#2f4858',
  'Proxmox': '#6b4c9a',
  'AI & Automation': '#0f5c5c',
  'Monitoring': '#7a3b2e',
  'Network & Utilities': '#8a6d1f',
  'Media & Downloads': '#7b2d5e',
  'Photos & Documents': '#2d5c7b',
  'Infrastructure & IPAM': '#4a5520',
};

function style(db, { apply }) {
  const now = new Date().toISOString().slice(0, 19).replace('T', ' ');
  const run = (sql, params) => (apply ? db.prepare(sql).run(...params) : null);

  const tagIds = new Map(
    db.prepare('SELECT title, id FROM items WHERE type = 1').all().map((r) => [r.title, r.id])
  );

  let tagsColoured = 0;
  for (const [title, colour] of Object.entries(CATEGORY_COLOUR)) {
    const id = tagIds.get(title);
    if (!id) continue;
    run('UPDATE items SET colour = ?, updated_at = ? WHERE id = ?', [colour, now, id]);
    tagsColoured++;
  }

  const apps = db
    .prepare(
      `SELECT i.id, i.title, i."order" AS ord, t.title AS category
         FROM items i
         JOIN item_tag it ON it.item_id = i.id
         JOIN items t ON t.id = it.tag_id
        WHERE i.type = 0 AND t.type = 1
        ORDER BY t.title, i."order", i.title`
    )
    .all();

  const byCategory = new Map();
  for (const app of apps) {
    if (!byCategory.has(app.category)) byCategory.set(app.category, []);
    byCategory.get(app.category).push(app);
  }

  // Seeded apps can share an `order` value (two both at 4). Sorting on
  // (order, title) makes the sequence deterministic before renumbering.
  let appsColoured = 0;
  let ordersChanged = 0;
  for (const [category, list] of byCategory) {
    list.sort((a, b) => (a.ord ?? 999) - (b.ord ?? 999) || a.title.localeCompare(b.title));
    const colour = CATEGORY_COLOUR[category] ?? '#37474f';
    list.forEach((app, index) => {
      if (app.ord !== index) {
        run('UPDATE items SET "order" = ?, updated_at = ? WHERE id = ?', [index, now, app.id]);
        ordersChanged++;
      }
      run('UPDATE items SET colour = ?, updated_at = ? WHERE id = ?', [colour, now, app.id]);
      appsColoured++;
    });
  }

  return { tagsColoured, appsColoured, ordersChanged };
}

if (require.main === module) {
  const [dbPath, ...flags] = process.argv.slice(2);
  if (!dbPath) {
    console.error('bruk: node heimdall-style.js <app.sqlite> [--apply]');
    process.exit(1);
  }
  const apply = flags.includes('--apply');
  const db = new DatabaseSync(dbPath);
  if (apply) db.exec('BEGIN');
  try {
    const stats = style(db, { apply });
    if (apply) db.exec('COMMIT');
    console.log(apply ? 'skrev:' : 'dry run (ingenting skrevet):', stats);
  } catch (err) {
    if (apply) db.exec('ROLLBACK');
    console.error('feilet:', err.message);
    process.exit(1);
  } finally {
    db.close();
  }
}

module.exports = { style, CATEGORY_COLOUR };