# Nettverksinterface-overvåking på CT104

Den faktiske kjørende observability-stacken er `CT104` (`pc9-ct104-observability`).

- Prometheus: `http://10.0.0.126:9090`
- Alertmanager: `http://10.0.0.126:9093`
- Blackbox exporter: `http://10.0.0.126:9115`
- Prometheus image: `prom/prometheus:v3.7.3`
- Scrape/evaluation interval: 30 sekunder
- Prometheus data retention: 90 dager / 12 GB

Prometheus ble verifisert med `/-/ready` (HTTP 200), og eksisterende targets ble lest tilbake. Før endringen hadde Prometheus jobber for blackbox HTTP/TCP og `homelab-exporter`; ingen `network-interface`-jobb eller `network_interface_*`-serier fantes.

## Ny nettverksjobb

Prometheus skal scrape den read-only eksportøren på:

```text
http://10.0.0.135:9122/metrics
```

Jobbnavn:

```text
network-interface
```

Metrikkene er kumulative kernel-tellere og skal tolkes med `rate()` i PromQL. Eksportøren skal kjøres på miljøet som eier `10.0.0.135`, med `eth0` som standardinterface.

## Varsler

- `NetworkInterfaceLinkDown`: carrier nede i 2 minutter.
- `NetworkInterfaceRxDroppedRateHigh`: over 10 droppede RX-pakker per sekund i 5 minutter.
- `NetworkInterfaceRxDroppedRatioHigh`: over 0,1 prosent RX-dropped i 5 minutter, med minst 1 drop per sekund.

Ingen av disse varslene skal starte recovery eller restarte nettverkstjenester automatisk.
