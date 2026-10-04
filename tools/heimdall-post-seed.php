<?php
// Etter-seeding: to ting API-et ikke lar oss fikse.
//
// 1.Kategoriene er ufestede. resolveTags() lager tagene uten `pinned`, og
//    'categories'-grenen i ItemController::dash() spør etter items som har barn
//    OG er selv pinned. Uten dette står dashbordet tomt.
//
// 2. appdescription er NULL for de apper som ble seeded med `description`
//    i stedet. PUT /api/item/{id} er en tom stub i 2.8.3, så backfillen må
//    skje her.
//
// Begge deler er idempotente: trykk på nytt uten å gjøre skade.
$db = new PDO('sqlite:/config/www/app.sqlite');
$db->setAttribute(PDO::ATTR_ERRMODE, PDO::ERRMODE_EXCEPTION);

// Samme rekkefølge som gruppene i homepage/config/services.yaml
$order = [
    'Homelab' => 0,
    'Proxmox' => 1,
    'AI & Automation' => 2,
    'Infrastructure & IPAM' => 3,
    'Monitoring' => 4,
    'Network & Utilities' => 5,
    'Media & Downloads' => 6,
    'Photos & Documents' => 7,
];

$st = $db->prepare('UPDATE items SET pinned = 1, "order" = ? WHERE title = ? AND type = 1');
foreach ($order as $title => $pos) {
    $st->execute([$pos, $title]);
}
echo "kategorier festet: {$st->rowCount()} rader siste runde\n";

// Tilbakefyll beskrivelser fra services.yaml
$map = json_decode(file_get_contents('/tmp/descriptions.json'), true);
if (!is_array($map)) {
    echo "FEIL: /tmp/descriptions.json ikke lest\n";
    exit(1);
}
$up = $db->prepare(
    'UPDATE items SET appdescription = ? WHERE title = ? AND type = 0'
);
$set = 0;
foreach ($map as $title => $desc) {
    $up->execute([$desc, $title]);
    if ($up->rowCount() > 0) {
        $set++;
    }
}
echo "beskrivelser satt: $set\n";

echo "\nkontroll:\n";
foreach ($db->query('SELECT title, pinned, "order" FROM items
                     WHERE type = 1 AND deleted_at IS NULL
                     ORDER BY "order" ASC, id ASC') as $r) {
    echo "  pinned={$r['pinned']}  order={$r['order']}  {$r['title']}\n";
}
$n = $db->query("SELECT count(*) FROM items WHERE type = 0 AND appdescription IS NOT NULL AND appdescription != ''")->fetchColumn();
$tot = $db->query("SELECT count(*) FROM items WHERE type = 0 AND deleted_at IS NULL")->fetchColumn();
echo "\napper med beskrivelse: $n / $tot\n";