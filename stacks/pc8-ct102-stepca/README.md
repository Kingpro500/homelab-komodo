# step-ca Stack

Internal Certificate Authority (smallstep step-ca) for the homelab. Issues
and auto-renews TLS certificates for all internal services (10.0.0.0/24) that
normally show "certificate not trusted / has expired" to browsers and clients.

## Service
Private CA + ACME server on port 9000. Clients that trust the root CA get
valid, auto-renewed HTTPS certs for internal-only services that the public
Let's Encrypt chain cannot cover (no public domain, dynamic WAN IP).

The CA exposes the **ACME protocol** (`https://10.0.0.117:9000/acme/...`), so
any ACME-capable client (Caddy, certbot, acme.sh, Traefik, cert-manager)
inside the LAN can use it as its "Let's Encrypt" endpoint.

## Components
- **step-ca** (port 9000): root + intermediate CA, ACME + JWK provisioner.

## First-time setup (Komodo)

1. **Komodo stack configuration:**
   - Stack name: `pc8-ct102-stepca`
   - Server: `pc8-ct102-core`
   - Run directory: `stacks/pc8-ct102-stepca`
   - File paths: `docker-compose.yml`
   - Source: `https://github.com/Kingpro500/homelab-komodo`, branch `main`
   - Stack Environment (Komodo → stack → environment) — set both:
     - `STEPCA_PASSWORD` — password protecting the signing keys (choose a
       long, random password).
     - `STEPCA_ADMIN_PASSWORD` — password for the `admin` JWK provisioner.
     These are needed **only on first boot** (CA initialization). Do not
     commit a runtime `.env` for this stack; the init values come from
     Komodo's Stack Environment.

2. **Deploy:** Komodo UI → Stacks → `pc8-ct102-stepca` → Deploy.
   Wait for the container to start (~15s). First boot generates the root +
   intermediate keys and certs into the `stepca_data` volume.

3. **Verify CA is up:**
   ```sh
   ssh root@10.0.0.102 'pct exec 102 -- docker logs stepca | tail -20'
   # should end with: Serving HTTPS on :9000 ... 
   curl -s https://10.0.0.117:9000/step_ca/ -k | head
   # {{ "ca": "..." }}  -> step-ca health/roots endpoint answers
   ```

## Trusting the root CA on a client

The root cert lives `docker exec stepca cat /home/step/certs/root_ca.crt`.
Install it in the trusted store of each device (phone, iPad, browser). Then
any cert the CA signs is trusted.

- macOS / iOS: open the `.crt`, verify, enable full trust in Keychain.
- Windows: import into "Trusted Root Certification Authorities".
- Linux / Firefox: add to the system trust store or the browser store.

Once a Caddy / acme client points at the ACME endpoint and you have
split-DNS, services can be served over HTTPS with this CA's certs with no
external dependency.

## Volumes
- `stepca_data`: all CA state (root + intermediate keys/certs, db, config).

## Ports
- 9000: CA API + ACME endpoint (max_cert_ttl applied).

## Documentation
- step-ca: https://smallstep.com/docs/step-ca/
- Docker image: https://hub.docker.com/r/smallstep/step-ca
- ACME with step-ca: https://smallstep.com/docs/step-ca/acme/
