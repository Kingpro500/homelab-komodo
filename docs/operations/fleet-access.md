# Fleet access model

Private fleet data is intentionally kept outside Git.

- Use a host-local `fleet.env` on Komodo Core for internal addresses and operational inventory.
- Keep the private Codex SSH key only on the Codex host.
- Keep onboarding keys, API tokens, passwords, and SSH private keys out of Git.
- Commit only `ops/fleet.env.example`, deployment templates, and non-sensitive documentation.
- Use one `codex` diagnostic identity on each managed Linux node. State-changing operations remain explicit.

See `ops/fleet.env.example` for the required private inventory variables.
