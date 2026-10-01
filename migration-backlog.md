# Migration backlog

Work listed here is deliberately queued until the Ollama / n8n / Hermes work on
pc1 is complete. Every Docker workload is deployed through Komodo; Tower data
is retained until the new service has been accepted.

| Workload | Destination | Status | Notes |
| --- | --- | --- | --- |
| iVentoy | To be chosen | Planned | New dedicated service; identify existing media and network requirements first. |
| UniFi Network Application | pc9, dedicated CT | Planned | Replaces the previously prepared pc6 CT plan; do not start the pc6 migration until pc9 is ready. |
| Uptime Kuma | pc6 CT 109 | Done | Running through Komodo. Review stale Tower-based monitors separately. |
| Homepage | pc6 CT 109 | Done | Running through Komodo. |
| Speedtest Tracker | pc6 CT 109 | Done | Running through Komodo. |
| Audiobookshelf | pc6 CT 109 | Prepared | Stack files exist locally but are intentionally not deployed or committed yet. |
| Podgrab | pc6 CT 109 | Planned | Identify Tower configuration and storage path before migration. |
