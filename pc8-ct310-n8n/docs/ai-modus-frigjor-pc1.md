# AI-modus – Ollama på PC1

Workflow-ID: `TVxIF3OGvWTOVdVW`

Styrer kun Ollama-gjesten CT350 (`ct156-ollama`) på node `pc1`. Start-grenen verifiserer Ollama `/api/version` før suksess. Stopp-grenen bruker separat kontrollnode og kjører ikke health-sjekk etter stopp.

Webhooker: `POST /webhook/ai-start` og `POST /webhook/ai-stop`. Pi-hole CT102, Matrix og Home Assistant styres ikke.
