# PC1 AI-heng-vakt

## Formål

Oppdage en reell Ollama-heng uten å reagere på ett kortvarig nettverksavbrudd.

## Deteksjon

Workflowen kjører hvert minutt og sjekker:

- Proxmox-/homelab-status: CT350 må fortsatt være `running`.
- Ollama `GET /api/version`.
- Tre påfølgende mislykkede Ollama-sjekker kreves før tiltak, altså omtrent
  tre minutter.
- Hvis CT350 er stoppet med vilje, nullstilles feil telleren og ingen restart
  utføres.
- Etter automatisk restart er det 30 minutters sperre før nytt forsøk.

## Tiltak

Ved bekreftet heng:

1. Stopp CT350.
2. Vent 20 sekunder.
3. Start CT350 igjen.
4. Ollama må deretter svare på neste overvåkingsrunde.

Det startes ikke modellgenerering automatisk etterpå. Det hindrer at en feil
umiddelbart gjentas og gir GPU-en tid til å kjøle seg ned.

## Begrensninger

Dette er en konservativ container-restart, ikke en PC-restart. Hvis hele PC1
eller strømpluggen henger, kan ikke n8n i CT310 nå den. Det krever en separat
Home Assistant-/smartplugg-vakt med flere mislykkede strøm- og nettverkssignaler
før eventuell strøm av/på. Det bør ikke aktiveres før PC1-hengen er skilt fra
vanlige nettverksavbrudd.

## Drift

Workflow-ID: `QNvvZA4ZAqAoK9xd`.
Workflowen er aktiv og første planlagte kjøring er verifisert som `success`.
