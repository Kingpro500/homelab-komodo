# pc6-ct200-alloy

Grafana Alloy sender Docker-loggene på pc6 CT200 (Emby primary) til VictoriaLogs på CT135
(`http://10.0.0.211:9428`). Egen Komodo-stack `pc6-ct200-alloy` slik at Emby primary-stacken ikke berøres.
Label `host=pc6-ct200`, `container=<navn>`. Ingen porter eksponeres; docker.sock er read-only.

Spørring i Grafana/VictoriaLogs: `{host="pc6-ct200"}`.
Deploy kun via Komodo: PullStack → DeployStack → sjekk at `alloy` kjører og at loggene dukker opp.
