# PC1 GPU-vakt

## Formål

Overvåker RTX 3070-temperatur på PC1 og gjør et avgrenset automatisk tiltak
før maskinen rekker å restarte.

## Målinger

GPU-eksportøren kjører som `pc1-gpu-exporter.service` på PC1 og eksponerer
Prometheus-metrikker på `10.0.0.112:9105/metrics`:

- temperatur
- effekt og power-limit
- GPU-belastning
- brukt/total VRAM
- viftehastighet
- GPU- og minneklokke

Prometheus-jobben heter `pc1-gpu` og scraper hvert 15. sekund.

## Grenser og tiltak

- Over **75 °C i 2 minutter**: warning og n8n frigjør PC1 ved å stoppe CT102
  (Pi-hole-reserve).
- Over **82 °C i 1 minutt**: critical og n8n stopper både CT350 (Ollama) og
  CT102. Dette er med vilje den eneste automatiske stoppingen av AI-containeren.
- Det gjøres ingen automatisk reboot av PC1 og ingen automatisk endring av
  NVIDIA power-limit.

Alertmanager sender samtidig alarmen til telefon-workflowen.

## Kontroll

n8n-workflow: `PC1-GPU-vakt` (`UaSRI3ympnMSLotC`), webhook:
`POST http://10.0.0.119:5678/webhook/pc1-gpu-alert`.

## Gjenoppretting

Etter at temperaturen er normalisert må CT350 startes manuelt eller via den
avtalte AI-startflyten. CT102 kan startes med `/webhook/ai-stop`.

## Begrensning

NVIDIA-container-testen verifiserte at GPU-en og device-nodene er tilgjengelige
inne i Docker, men CUDA-imageet inneholdt ikke `nvidia-smi`. Den direkte
Ollama/NVIDIA-målingen og Prometheus-eksportøren er derfor den operative
sannhetskilden.
