# pc6-ct250-alloy

Grafana Alloy sender Docker-loggene på pc6 CT250 (Tunarr primary) til VictoriaLogs på CT135
(`http://10.0.0.211:9428`). Egen Komodo-stack `pc6-ct250-alloy` slik at Tunarr primary-stacken ikke berøres.
Label `host=pc6-ct250`, `container=<navn>`. Ingen porter eksponeres; docker.sock er read-only.

Spørring i Grafana/VictoriaLogs: `{host="pc6-ct250"}`.
Deploy kun via Komodo: PullStack → DeployStack → sjekk at `alloy` kjører og at loggene dukker opp.
