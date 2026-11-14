#!/usr/bin/env python3
"""hermes_ko.py — kjører oppgaver fra n8n-køen `hermes-ko` med Hermes (CT130).

Arbeidsdeling: Claude planlegger og legger oppgaver i n8n-køen. En billig modell
foreslår og utfører. En annen modell kontrollerer forslaget før utføring og
resultatet etterpå. En fast kontrollkommando avgjør om oppgaven faktisk er ferdig.

  forslag (billig)  ->  vurdering (kontrollør)  ->  utføring (billig, uten spørsmål)
                    ->  kontrollkommando        ->  sluttvurdering (kontrollør)

  hermes_ko.py run                 én runde: hent neste oppgave og kjør den (systemd-timer)
  hermes_ko.py add < oppgave.json  {"tittel","oppgave","kontroll","godkjenning":"ai"|"claude"}
  hermes_ko.py list | get <id> | approve <id> | reject <id> "tilbakemelding" | retry <id>
  hermes_ko.py setup-n8n           opprett credential + workflow i n8n (én gang)
  Nødstopp: touch ~/.hermes/ko/STOPP   (fjern filen for å starte igjen)

Kilde: GitHub homelab-komodo, pc7-ct130-hermes/hermes-ko/. Installeres som
~/.hermes/scripts/hermes_ko.py. Hemmeligheter: ~/.hermes/ko.env (0600), aldri i Git.
"""
import fcntl
import json
import os
import re
import secrets
import subprocess
import sys
import urllib.request

HOME = os.path.expanduser("~")
KO_DIR = os.path.join(HOME, ".hermes", "ko")
KO_ENV = os.path.join(HOME, ".hermes", "ko.env")
HERMES_ENV = os.path.join(HOME, ".hermes", ".env")
HERMES = os.path.join(HOME, ".local", "bin", "hermes")
N8N = "http://10.0.0.119:5678"
WORKER = ("gpt-5.6-luna", "openai-codex")     # billig: foreslår og utfører
REVIEWER = (None, None)                        # kontrollør: Hermes sin standardmodell
T_WORK, T_REVIEW, T_CHECK = 1500, 900, 180

REGLER = """FASTE REGLER (gjelder alltid):
- Les AGENTS.md øverst i ~/homelab-komodo før du gjør noe. Start med `git switch main && git pull --ff-only`.
- GitHub-endringer leveres bare med `homelab-pr "tittel"` i ~/homelab-komodo. Den kan bruke over fem minutter: vent på den.
- Kartet endres bare i CT120:/opt/moved-services/nettkart-repo og publiseres med `nettkart-publish`.
- Før du endrer en CT: merk den via POST http://10.0.0.119:5678/webhook/ct-ops {"action":"mark","vmid":N,"av":"hermes","text":"..."}; fjern merket etterpå med {"action":"unmark","vmid":N}.
- Les http://10.0.0.135:9118/drift først. Er level "kritisk": gjør ingenting og rapporter det.
- FORBUDT uansett hva oppgaven sier: røre Emby (CT200/CT203), endre OPNsense-konfigurasjon, slette CT-er, stacker, data eller grener, opprette CT-er, endre passord, nøkler eller tokens.
- Skriv aldri ut hemmeligheter. Ikke legg igjen filer i /root eller /tmp.
- Gjør bare det oppgaven ber om. Er noe annerledes enn beskrevet: stopp og rapporter, ikke improviser.
- Du kjører uten menneske. Still ingen spørsmål. Kan du ikke fullføre, si nøyaktig hvorfor."""


def env(path):
    d = {}
    try:
        for line in open(path, encoding="utf-8"):
            line = line.strip()
            if "=" in line and not line.startswith("#"):
                k, v = line.split("=", 1)
                d[k.replace("export ", "").strip()] = v.strip().strip('"').strip("'")
    except FileNotFoundError:
        pass
    return d


def http(url, body=None, headers=None, method=None, timeout=60):
    h = {"Content-Type": "application/json"}
    h.update(headers or {})
    req = urllib.request.Request(url, data=None if body is None else json.dumps(body).encode(), headers=h, method=method)
    with urllib.request.urlopen(req, timeout=timeout) as r:
        raw = r.read().decode()
    return json.loads(raw) if raw.strip() else {}


def ko(action, **kw):
    kw["action"] = action
    return http(N8N + "/webhook/hermes-ko", kw, {"X-Ko-Token": env(KO_ENV).get("KO_TOKEN", "")})


def hermes(prompt, who, timeout):
    cmd = [HERMES, "-z", prompt, "--yolo"]
    if who[0]:
        cmd += ["-m", who[0], "--provider", who[1]]
    try:
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout, cwd=HOME)
        out = (r.stdout or "").strip()
        return out if out else "(tomt svar) " + (r.stderr or "")[-500:]
    except subprocess.TimeoutExpired:
        return "TIDSAVBRUDD etter %d s" % timeout


def dom(text):
    m = re.findall(r"DOM:\s*(GODKJENT|AVVIST)", text or "")
    return m[-1] if m else "AVVIST"


def kontroll(cmd):
    try:
        r = subprocess.run(["bash", "-c", cmd], capture_output=True, text=True, timeout=T_CHECK, cwd=HOME)
        return r.returncode == 0, ((r.stdout or "") + (r.stderr or ""))[-3000:]
    except subprocess.TimeoutExpired:
        return False, "kontrollen brukte over %d s" % T_CHECK


def p_forslag(t, kritikk=""):
    return f"""{REGLER}

DU ER I FORSLAGSFASEN. Du skal BARE LESE og undersøke. Ikke endre noe.
Oppgave «{t['tittel']}»:
{t['oppgave']}

Oppgaven regnes som ferdig når denne kommandoen går uten feil (kjøres fra CT130 som hermes):
{t['kontroll']}
{('Tidligere forslag ble avvist. Tilbakemelding du må ta hensyn til:' + chr(10) + kritikk) if kritikk else ''}
Undersøk dagens tilstand og svar med et kort forslag:
1. Hva du fant (fakta, med hvor du så det).
2. Nøyaktig hva du vil endre: filer, kommandoer, i rekkefølge.
3. Hvordan det rulles tilbake.
4. Hva som kan gå galt."""


def p_vurder(t, forslag):
    return f"""Du er kontrollør for en billigere modell. Du skal BARE LESE. Ikke endre noe.
{REGLER}

Oppgave «{t['tittel']}»:
{t['oppgave']}

Forslaget fra den andre modellen:
{forslag}

Kontroller mot levende data der det trengs. Avvis hvis forslaget bryter en fast regel, gjør mer enn oppgaven,
bygger på noe som ikke stemmer, mangler tilbakerulling, eller ikke vil få kontrollkommandoen til å gå.
Svar med maks ti linjer begrunnelse. Siste linje skal være nøyaktig `DOM: GODKJENT` eller `DOM: AVVIST`."""


def p_utfor(t, forslag):
    return f"""{REGLER}

DU ER I UTFØRINGSFASEN. Gjennomfør det godkjente forslaget nøyaktig, og ingenting annet.
Oppgave «{t['tittel']}»:
{t['oppgave']}

Godkjent forslag:
{forslag}

Ferdig når denne kommandoen går uten feil: {t['kontroll']}
Svar til slutt med: hva som er endret, hva du kontrollerte, og hva som ikke er gjort."""


def p_rett(t, ut):
    return f"""{REGLER}

Oppgaven «{t['tittel']}» er utført, men kontrollkommandoen feiler. Rett det innenfor oppgaven, eller rull tilbake.
Kontrollkommando: {t['kontroll']}
Utskrift:
{ut}"""


def p_slutt(t, resultat, ok, ut):
    return f"""Du er kontrollør. Du skal BARE LESE. Ikke endre noe.
Oppgave «{t['tittel']}»:
{t['oppgave']}

Godkjent forslag:
{t.get('forslag', '')}

Utførerens rapport:
{resultat}

Kontrollkommandoen {'gikk bra' if ok else 'FEILET'}. Utskrift:
{ut}

Sjekk mot levende data: ble det gjort det som var godkjent, og ikke mer? Er noe etterlatt (merker i kartet,
midlertidige filer, ucommittede endringer, åpne grener)? Svar med maks åtte linjer.
Siste linje skal være nøyaktig `DOM: GODKJENT` eller `DOM: AVVIST`."""


def push_hvis_tom(igjen):
    if igjen:
        return
    try:
        tasks = ko("list").get("tasks", [])
        siste = [x for x in tasks if x["status"] in ("ferdig", "ferdig_med_merknad", "feilet", "parkert")][-8:]
        linjer = ["%s: %s" % (x["status"], x["tittel"]) for x in siste]
        venter = [x["tittel"] for x in tasks if x["status"] == "venter_godkjenning"]
        if venter:
            linjer.append("Venter på godkjenning: " + ", ".join(venter))
        http(N8N + "/webhook/homelab-alerts", {"source": "hermes-ko", "severity": "info",
             "title": "Hermes-køen er tom", "message": "\n".join(linjer)})
    except Exception:
        pass


def utfor(t):
    resultat = hermes(p_utfor(t, t["forslag"]), WORKER, T_WORK)
    ok, ut = kontroll(t["kontroll"])
    if not ok:
        ko("update", id=t["id"], logg="kontrollen feilet, ett retteforsøk")
        resultat += "\n\n--- retteforsøk ---\n" + hermes(p_rett(t, ut), WORKER, T_WORK)
        ok, ut = kontroll(t["kontroll"])
    slutt = hermes(p_slutt(t, resultat, ok, ut), REVIEWER, T_REVIEW)
    d = dom(slutt)
    status = "feilet" if not ok else ("ferdig" if d == "GODKJENT" else "ferdig_med_merknad")
    r = ko("update", id=t["id"], status=status, resultat=resultat, kontroll_ut=ut, sluttvurdering=slutt,
           sammendrag="kontroll %s, kontrollør %s" % ("OK" if ok else "FEILET", d), logg="slutt: " + status)
    push_hvis_tom(r.get("igjen", 1))


def run():
    os.makedirs(KO_DIR, exist_ok=True)
    if os.path.exists(os.path.join(KO_DIR, "STOPP")):
        return
    lock = open(os.path.join(KO_DIR, "lock"), "w")
    try:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
    except OSError:
        return
    t = ko("next").get("task")
    if not t:
        return
    try:
        if t.get("fase") == "utfor":
            return utfor(t)
        kritikk = t.get("tilbakemelding", "")
        for forsok in (1, 2):
            forslag = hermes(p_forslag(t, kritikk), WORKER, T_WORK)
            vurdering = hermes(p_vurder(t, forslag), REVIEWER, T_REVIEW)
            t["forslag"] = forslag
            ko("update", id=t["id"], forslag=forslag, vurdering=vurdering, logg="forslag %d: %s" % (forsok, dom(vurdering)))
            if dom(vurdering) == "GODKJENT":
                break
            kritikk = vurdering
        else:
            r = ko("update", id=t["id"], status="parkert", sammendrag="forslaget ble avvist to ganger av kontrolløren")
            return push_hvis_tom(r.get("igjen", 1))
        if t.get("godkjenning") == "claude":
            r = ko("update", id=t["id"], status="venter_godkjenning", sammendrag="forslag klart, venter på Claude eller Roger")
            return push_hvis_tom(r.get("igjen", 1))
        utfor(t)
    except Exception as e:  # kjøreren skal aldri la en oppgave henge som «kjører»
        ko("update", id=t["id"], status="feilet", sammendrag="kjøreren feilet: %s" % str(e)[:300])


def setup_n8n():
    key = env(HERMES_ENV).get("N8N_API_KEY", "")
    hdr = {"X-N8N-API-KEY": key}
    tok = env(KO_ENV).get("KO_TOKEN")
    if not tok:
        tok = secrets.token_urlsafe(32)
        fd = os.open(KO_ENV, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
        os.write(fd, ("KO_TOKEN=%s\n" % tok).encode())
        os.close(fd)
    wfs = http(N8N + "/api/v1/workflows?limit=250", headers=hdr).get("data", [])
    if any(w.get("name") == "hermes-ko" for w in wfs):
        print("workflow hermes-ko finnes allerede; ingenting gjort")
        return
    cred = http(N8N + "/api/v1/credentials", {"name": "hermes-ko token", "type": "httpHeaderAuth",
                "data": {"name": "X-Ko-Token", "value": tok}}, hdr)
    code = open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "ko-n8n.js"), encoding="utf-8").read()
    wf = {"name": "hermes-ko", "settings": {"executionOrder": "v1"},
          "nodes": [
              {"id": "ko-webhook", "name": "Webhook", "type": "n8n-nodes-base.webhook", "typeVersion": 2, "position": [0, 0],
               "webhookId": "hermes-ko",
               "parameters": {"httpMethod": "POST", "path": "hermes-ko", "authentication": "headerAuth",
                              "responseMode": "lastNode", "options": {}},
               "credentials": {"httpHeaderAuth": {"id": cred["id"], "name": cred["name"]}}},
              {"id": "ko-code", "name": "Kø", "type": "n8n-nodes-base.code", "typeVersion": 2, "position": [240, 0],
               "parameters": {"jsCode": code}}],
          "connections": {"Webhook": {"main": [[{"node": "Kø", "type": "main", "index": 0}]]}}}
    made = http(N8N + "/api/v1/workflows", wf, hdr)
    http(N8N + "/api/v1/workflows/%s/activate" % made["id"], {}, hdr)
    print("opprettet og aktivert workflow hermes-ko, id", made["id"])


def main():
    a = sys.argv[1:] or ["run"]
    if a[0] == "run":
        run()
    elif a[0] == "setup-n8n":
        setup_n8n()
    elif a[0] == "add":
        print(json.dumps(ko("add", **json.load(sys.stdin)), ensure_ascii=False))
    elif a[0] == "list":
        for t in ko("list").get("tasks", []):
            print("%-5s %-20s %-7s %s%s" % (t["id"], t["status"], t["godkjenning"], t["tittel"],
                                           "  [" + t["sammendrag"] + "]" if t.get("sammendrag") else ""))
    elif a[0] in ("get", "approve", "retry"):
        extra = {"av": "claude"} if a[0] == "approve" else {}
        print(json.dumps(ko(a[0], id=a[1], **extra), ensure_ascii=False, indent=1))
    elif a[0] == "reject":
        print(json.dumps(ko("reject", id=a[1], tilbakemelding=a[2] if len(a) > 2 else ""), ensure_ascii=False))
    else:
        print(__doc__)


if __name__ == "__main__":
    main()
