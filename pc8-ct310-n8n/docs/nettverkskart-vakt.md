# Nettverkskart-vakt (n8n)

Workflow `Nettverkskart-vakt` (id `Vpp9OIz3GzupC0JJ`), kjører daglig 08:30 på n8n (CT103). Eksport: `pc8-ct310-n8n/workflows/nettverkskart-vakt.json` (hemmeligheter erstattet med `REDACTED_*`).

Hva den sjekker:
1. Alle CT/VM i Proxmox (`/cluster/resources?type=vm`) mot `data-vmid` på kartet (http://10.0.0.124:3020/). Manglende CT/VM gir varsel.
2. Hull i kartversjoner: de siste 30 versjonene må ha et endringsnotat (kart eller `endringer.html`).

Varsling: via `homelab-alerts`, ett varsel per nytt funn (lagres i workflow static data, nullstilles når funnet er rettet). Ingen automatiske endringer.

Bakgrunn: flere AI-tråder oppdaterer kartet samtidig. `nettkart-publish` slår nå sammen kopier (`nettkart-merge`), og vakten fanger det som likevel glipper, også endringer som ikke går via publiseringsskriptet.

Proxmox-token hentes fra n8n-workflowen (ikke i repoet); ved rotasjon må kodenoden oppdateres.
