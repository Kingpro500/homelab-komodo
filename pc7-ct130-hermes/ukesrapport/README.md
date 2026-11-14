# Ukesrapport linjekvalitet

Skriptet `ukesrapport.py` kjører uten AI-kall hver søndag kl. 20:00 Europe/Oslo. Det leser bare linjekvalitetsdata og drift-vakt, beregner de sju siste hele dagene mot de sju foregående, og oppdaterer kun `<ul id="funn">` samt «Sist gjennomgått» i kartkilden på CT120.

Kilder:

- `http://10.0.0.124:3020/linjekvalitet.json`
- `http://10.0.0.135:9118/drift`

Nullverdier utelates i beregninger. Ugyldige eller utilgjengelige kilder, feil HTML-struktur eller feil CT120-rute gir exit 1 uten endring. All kilde-tekst HTML-escapes. En identisk rapport gjør ingen endring og publiserer ikke.

Førstegangsinstallasjon:

```sh
install -m 755 ukesrapport.py ~/.hermes/scripts/ukesrapport.py
hermes cron create '0 20 * * 0' --timezone Europe/Oslo --name 'Ukesrapport linjekvalitet' --script ~/.hermes/scripts/ukesrapport.py --no-agent --deliver local
```

Test:

```sh
python3 -m py_compile ukesrapport.py
python3 ukesrapport.py --selvtest
```

Etter vellykket publisering sendes én melding via samme `notify_ha.py`-rute som øvrige lokale rapportskript. Meldingsfeil logges, men gir exit 0.
