# UniFi WiFi-klient og radiomålinger

Samler og eksporterer trådløse klientverdier fra UniFi til Prometheus. Samleren kjører hvert minutt i `unifi-network-collector.service` via timeren. Eksportøren kjører som `wan-flap-metrics.service` på port 9130.

## SQLite-tabeller

Samleren oppretter bare disse nye tabellene med `CREATE TABLE IF NOT EXISTS`:

```sql
CREATE TABLE IF NOT EXISTS unifi_client_snapshots (
  observed_at TEXT NOT NULL, mac TEXT NOT NULL, ip TEXT, name TEXT, hostname TEXT,
  radio TEXT, signal_dbm REAL, tx_retries INTEGER, tx_packets INTEGER,
  retry_ratio REAL, tx_rate_mbps REAL, satisfaction REAL, PRIMARY KEY (mac)
);
```

```sql
CREATE TABLE IF NOT EXISTS unifi_radio_snapshots (
  observed_at TEXT NOT NULL, ap TEXT NOT NULL, radio TEXT NOT NULL,
  channel_utilization REAL, PRIMARY KEY (ap, radio)
);
```

Kun `is_wired=false` lagres. Retry-andel beregnes fra tellerendringer; ved første måling, reset eller null pakker er verdien NULL. `tx_rate` konverteres fra kbit/s til Mbit/s. Tabellen inneholder siste rad per klient eller AP/radio.

## Prometheus

Eksportøren skriver nyere rader enn fem minutter og utelater NULL-verdier:

- `unifi_client_signal_dbm{mac,ip,name,radio}`
- `unifi_client_retry_ratio{mac,ip,name,radio}`
- `unifi_client_tx_rate_mbps{mac,ip,name,radio}`
- `unifi_client_satisfaction{mac,ip,name,radio}`
- `unifi_radio_channel_utilization{ap,radio}`

Labelverdier escapes etter Prometheus-reglene. `name` bruker `name`, deretter `hostname`, ellers tom streng. Nye tabeller leses i egen feilhåndtering slik at eksisterende OPNsense- og UniFi-metrikker fortsatt eksporteres hvis den nye lesingen feiler.

Eksempel:

```text
unifi_client_signal_dbm{mac="aa:bb:cc:dd:ee:ff",ip="192.0.2.25",name="Stue Laptop",radio="na"} -58
unifi_client_retry_ratio{mac="aa:bb:cc:dd:ee:ff",ip="192.0.2.25",name="Stue Laptop",radio="na"} 0.0125
unifi_client_tx_rate_mbps{mac="aa:bb:cc:dd:ee:ff",ip="192.0.2.25",name="Stue Laptop",radio="na"} 433.2
unifi_client_satisfaction{mac="aa:bb:cc:dd:ee:ff",ip="192.0.2.25",name="Stue Laptop",radio="na"} 97
unifi_radio_channel_utilization{ap="AP Stue",radio="na"} 18
```

## Validering og drift

- Kjør `python3 -m py_compile` på begge Python-filene.
- Kjør samleren manuelt to ganger med minst 20 sekunder mellomrom ved funksjonsendringer.
- Restart `wan-flap-metrics.service` etter endringer i eksportøren.
- Kontroller `/metrics` for både de nye og eksisterende metrikknavnene.

## Tilbakerulling

Legg tilbake sikkerhetskopiene av de to Python-filene, kjør py_compile, restart `wan-flap-metrics.service`, og sammenlign metrikknavnene med baseline. De nye SQLite-tabellene skal bli liggende. Systemd-filene i denne katalogen er referansefiler og inneholder ingen hemmeligheter.
