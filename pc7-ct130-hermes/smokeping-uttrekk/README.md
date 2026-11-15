# Smokeping-uttrekk

Henter timesverdier fra Smokeping i CT113 og skriver døgntall for de siste 30 kalenderdøgnene til `/srv/nettkart/www/smokeping.json` i CT120. Manglende mål/målepunkt hoppes over. Skriptet skriver ingenting ved vellykket ordinær kjøring.

```sh
python3 -m py_compile smokeping_uttrekk.py
python3 smokeping_uttrekk.py --selvtest
python3 smokeping_uttrekk.py --ikke-skriv
install -m 755 smokeping_uttrekk.py ~/.hermes/scripts/smokeping_uttrekk.py
hermes cron create '20 * * * *' --timezone Europe/Oslo --name 'Smokeping-uttrekk' --script ~/.hermes/scripts/smokeping_uttrekk.py --no-agent --deliver local
```
