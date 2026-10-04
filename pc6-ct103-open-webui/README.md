# Open WebUI on pc6 CT 103

- **Host:** pc6 (`10.0.0.120`)
- **LXC:** `pc6-ct103-node` (shared with the n8n stack)
- **IP:** `10.0.0.119`
- **URL:** `http://10.0.0.119:3080`

A self-hosted chat front end for OpenRouter models. It is the browser interface
for the same models Hermes uses, so you can hold the same conversations in a
window instead of a terminal.

## First run

Open the URL and create the admin account. `ENABLE_SIGNUP` defaults to `false`,
so nobody else can register afterwards. Losing the admin account means clearing
the `admin` row from the SQLite database in `/opt/open-webui`.

## Model providers

| Provider | Configured via | Status |
|---|---|---|
| OpenRouter | `OPENAI_API_BASE_URL` + `OPENAI_API_KEY` | primary, always available |
| Ollama (pc1) | `OLLAMA_BASE_URL` | optional, see below |

OpenRouter is the reliable path. It uses a separate variable,
`OPENROUTER_API_KEY_WEBUI`, rather than reusing the Hermes key, so the two can be
rotated independently and usage is attributed separately in OpenRouter.

Ollama on pc1 answers, but it runs on CPU: `/api/ps` is empty and a short reply
takes about 9 seconds. It stays disabled through `ENABLE_OLLAMA_API=false`.
Enable it only once GPU access is fixed.

## Secrets

Two Komodo secret variables, referenced by name and never stored in Git:

| Variable | Used for |
|---|---|
| `OPEN_WEBUI_SECRET_KEY` | signs session cookies |
| `OPENROUTER_API_KEY_WEBUI` | OpenRouter |

`WEBUI_SECRET_KEY` is not a password you log in with. Changing it logs everyone
out but loses no data. The admin account lives in the volume, not in a variable.

See `.env.example` for the full set.

## Storage

Data lives in `/opt/open-webui` inside the LXC, alongside `/opt/n8n`. It is not
on the Unraid array, so back it up the same way as n8n if the chat history
matters.

## Ports on CT 103

| Port | Stack |
|---|---|
| 5678 | n8n |
| 3080 | Open WebUI |
