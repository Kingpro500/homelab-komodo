# Dagsrapport linjekvalitet

`dagsrapport.py` lager eller erstatter dagsrapportblokken for gårsdagen på linjekvalitet-siden. Den regner punkt 1–4 deterministisk, forsøker lokal Ollama-oppsummering og publiserer bare når de deterministiske punktene er endret. AI-feil utelater kun AI-avsnittet.

Kjøringer:

- `python3 dagsrapport.py --selvtest`
- `python3 dagsrapport.py --ikke-publiser`
- uten valg: oppdater kartkilden og publiser ved endring
