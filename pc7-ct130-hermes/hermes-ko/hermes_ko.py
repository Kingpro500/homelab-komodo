#!/usr/bin/env python3
"""hermes_ko.py — kjører oppgaver fra n8n-køen `hermes-ko` med Hermes (CT130).

Arbeidsdeling: Claude planlegger og legger oppgaver i n8n-køen. En billig modell
foreslår og utfører. En annen modell kontrollerer forslaget før utføring og
resultatet etterpå. En fast kontrollkommando avgjør om oppgaven faktisk er ferdig.

  forslag (billig)  ->  vurdering (kontrollør)  ->  utføring (billig, uten spørsmål)
                    ->  kontrollkommando        ->  sluttvurdering (kontrollør)

Kontrollørens dom på et forslag (endret 17. nov 2026, se README «Kontrollørens dom»):
  GODKJENT  utføres. Kontrollørens vilkår følger med til utføreren.
  AVVIST    bare av fem navngitte grunner. Nytt forslag én gang; i runde to ser
            kontrolløren sin forrige vurdering og skal bare sjekke om den er løst.
  BLOKKERT  feilen ligger i oppgaven, ikke forslaget. Parkeres straks med
            sammendrag «trenger beslutning: …». Roger må bestemme.
Begrunnelsen lagres i oppgavens hendelseslogg og i sammendraget.

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
import time
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
LOKAL_URL = "http://10.0.0.133:11434/api/generate"
LOKAL_MODELL = "qwen3:8b"
T_LOKAL = 60
ACTIVE = {"worker_id": "", "lock_id": ""}
LANES = ("infra", "general", "diagnostics", "file-read", "network-map-read", "inventory")
READ_ONLY_LANES = ("diagnostics", "file-read", "network-map-read", "inventory")

REGLER = """FASTE REGLER (gjelder alltid):
- Les AGENTS.md øverst i ~/homelab-komodo før du gjør noe. Start med `git switch main && git pull --ff-only`.
- GitHub-endringer leveres bare med `homelab-pr "tittel"` i ~/homelab-komodo. Den kan bruke over fem minutter: vent på den.
- Kartet endres bare i CT120:/opt/moved-services/nettkart-repo og publiseres med `nettkart-publish`.
- Før du endrer en CT: merk den via POST http://10.0.0.119:5678/webhook/ct-ops {"action":"mark","vmid":N,"av":"hermes","text":"..."}; fjern merket etterpå med {"action":"unmark","vmid":N}. `text` må være 3-140 tegn og bare inneholde bokstaver, tall, mellomrom og tegnene . , : / ( ) - (ingen anførselstegn, =, + eller %). `av` skal være nøyaktig hermes. Svaret må ha "ok": true. Stopper du underveis, fjern alltid merker du har satt før du rapporterer. ct-ops bruker ofte 20 sekunder og kan bruke 3 minutter: bruk tidsgrense 200 sekunder på kallet. Svarer den BLOKKERT eller ikke i tide: vent 60 sekunder og prøv igjen, inntil 3 ganger. Aktive merker leses med: ssh pc6 'cat /var/lib/ct-ops/marks.json' (tom liste er {}). Kontroller der at dine merker er borte før du rapporterer.
- Les http://10.0.0.135:9118/drift først. Er level "kritisk": gjør ingenting og rapporter det.
Unntak: er det eneste kritiske funnet map:dirty, kontroller selv med ssh pc6 'pct exec 120 -- git -C /opt/moved-services/nettkart-repo status --short'. Er utskriften tom, er funnet utdatert (drift-vakten oppdateres hvert 15. minutt), og du skal fortsette. Er den ikke tom: vent 3 minutter og kontroller én gang til før du stopper.
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
    if action in ("update", "retry") and ACTIVE["lock_id"]:
        kw.setdefault("worker_id", ACTIVE["worker_id"])
        kw.setdefault("lock_id", ACTIVE["lock_id"])
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
    m = re.findall(r"DOM:\s*(GODKJENT|AVVIST|BLOKKERT)", text or "")
    return m[-1] if m else "UTILGJENGELIG"


def kort(text, n=380):
    """Kontrollørens begrunnelse på én linje, uten DOM-linjen, til sammendraget."""
    linjer = [x.strip() for x in (text or "").splitlines()
              if x.strip() and not x.strip().startswith("DOM:")]
    return " ".join(linjer)[:n]


def beslutning(text):
    """Linjen kontrolløren skriver ved BLOKKERT: hva Roger må ta stilling til."""
    for linje in (text or "").splitlines():
        if linje.strip().startswith("BESLUTNING:"):
            return linje.strip()[len("BESLUTNING:"):].strip()[:380]
    return kort(text)


def pause(minutter, grunn):
    with open(os.path.join(KO_DIR, "PAUSE"), "w", encoding="utf-8") as f:
        f.write(str(time.time() + minutter * 60) + "\n")
        f.write(grunn + "\n")


def lokal_sjekk(t, forslag):
    try:
        oppgave = t.get("oppgave", "")
        linjer = oppgave.splitlines()
        if "Steg:" not in linjer:
            return "HOPPET OVER", "ingen nummererte steg"
        start = linjer.index("Steg:") + 1
        steg = [linje.strip() for linje in linjer[start:]
                if re.match(r"^\d+\.\s+", linje.strip())]
        if not steg:
            return "HOPPET OVER", "ingen nummererte steg"
        prompt = (
            "Oppgaven krever disse stegene i denne rekkefølgen:\n"
            + "\n".join(steg)
            + "\nForslaget sier:\n"
            + forslag[:12000]
            + "\nSvar med nøyaktig ett ord først, MANGLER eller KOMPLETT. "
              "Ved MANGLER: skriv deretter numrene på stegene som mangler "
              "helt i forslaget. Et steg som er gjengitt med andre ord teller "
              "som med."
        )
        svar = http(LOKAL_URL, {
            "model": LOKAL_MODELL,
            "prompt": prompt,
            "stream": False,
            "options": {"temperature": 0},
        }, timeout=T_LOKAL)
        tekst = re.sub(r"<think>.*?</think>", "", svar.get("response", ""), flags=re.S).strip()
        if tekst.startswith("MANGLER"):
            return "MANGLER", tekst[:300]
        if tekst.startswith("KOMPLETT"):
            return "KOMPLETT", ""
        return "HOPPET OVER", "uventet svar fra lokal modell"
    except Exception as e:
        return "HOPPET OVER", str(e)[:300]


def kontroll(cmd):
    try:
        r = subprocess.run(["bash", "-c", cmd], capture_output=True, text=True, timeout=T_CHECK, cwd=HOME)
        return r.returncode == 0, ((r.stdout or "") + (r.stderr or ""))[-3000:]
    except subprocess.TimeoutExpired:
        return False, "kontrollen brukte over %d s" % T_CHECK


def avgjort(t):
    tilbakemelding = t.get("tilbakemelding", "")
    return (
        "AVGJØRELSER FRA CLAUDE (gjelder foran oppgaveteksten og er ikke avvik):\n"
        + tilbakemelding
        if tilbakemelding else ""
    )


def p_forslag(t, kritikk=""):
    return f"""{REGLER}

DU ER I FORSLAGSFASEN. Du skal BARE LESE og undersøke. Ikke endre noe.
Lane: {t.get('kategori', 'general')}. Ressurser: {', '.join(t.get('ressurser', [])) or 'ingen'}.
Hvis lane er diagnostics, file-read, network-map-read eller inventory, er dette READ ONLY: ingen skrivekommandoer, deploy, restart, nettverkskartendring eller publisering. Foreslå kun lesing og kontrollkommandoer.
Oppgave «{t['tittel']}»:
{t['oppgave']}
{avgjort(t)}

Oppgaven regnes som ferdig når denne kommandoen går uten feil (kjøres fra CT130 som hermes):
{t['kontroll']}
{('Tidligere forslag ble avvist. Tilbakemelding du må ta hensyn til:' + chr(10) + kritikk) if kritikk else ''}
Undersøk dagens tilstand og svar med et kort forslag:
1. Hva du fant (fakta, med hvor du så det).
2. Nøyaktig hva du vil endre: filer, kommandoer, i rekkefølge.
3. Hvordan det rulles tilbake.
4. Hva som kan gå galt."""


def p_vurder(t, forslag, forrige=""):
    runde2 = f"""
DETTE ER ANDRE RUNDE. Din vurdering av det første forslaget var:
{forrige}

Vurder nå bare to ting: er innvendingene over løst, og bryter det nye forslaget en fast regel?
Kom ikke med nye innvendinger om forhold du kunne tatt opp sist. Motsi ikke din forrige vurdering.
""" if forrige else ""
    return f"""Du er kontrollør for en billigere modell. Du skal BARE LESE. Ikke endre noe.
{REGLER}

Oppgave «{t['tittel']}»:
{t['oppgave']}
{avgjort(t)}

Kontrollkommandoen som avgjør om oppgaven er ferdig (kjøres fra CT130 som hermes):
{t['kontroll']}

Forslaget fra den andre modellen:
{forslag}
{runde2}
Kontroller mot levende data der det trengs.

AVVIS bare av en av disse fem grunnene, og si hvilken:
1. Forslaget bryter en fast regel.
2. Forslaget gjør mer enn oppgaven ber om.
3. Forslaget bygger på en faktafeil som du selv har kontrollert.
4. Forslaget endrer noe uten å si hvordan det rulles tilbake.
5. Forslaget vil ikke få kontrollkommandoen til å gå.
Alt annet er ikke avvisningsgrunn: manglende detaljer, ønsker om flere tester, backup, filer eller
fremgangsmåter som verken står i de faste reglene eller i oppgaven. Slikt skriver du som linjer som begynner
med `VILKÅR:`, og godkjenner. Utføreren får vilkårene og må følge dem.
Kunne du ikke kontrollere noe selv, si det, men avvis ikke av den grunn alene.

Bruk BLOKKERT når feilen ligger i oppgaven og ikke i forslaget: oppgaveteksten stemmer ikke med virkeligheten,
kontrollkommandoen kan ikke gå uansett hva som gjøres, eller oppgaven krever noe de faste reglene forbyr.
Da skal Roger bestemme. Skriv én linje som begynner med `BESLUTNING:` og sier hva han må ta stilling til.

Svar med maks ti linjer begrunnelse. Siste linje skal være nøyaktig `DOM: GODKJENT`, `DOM: AVVIST` eller `DOM: BLOKKERT`."""


def p_utfor(t, forslag):
    return f"""{REGLER}

DU ER I UTFØRINGSFASEN. Gjennomfør det godkjente forslaget nøyaktig, og ingenting annet.
Lane: {t.get('kategori', 'general')}. Ressurser: {', '.join(t.get('ressurser', [])) or 'ingen'}.
READ ONLY lanes diagnostics, file-read, network-map-read og inventory må aldri skrive, deploye, restarte eller endre/publisere nettverkskartet. Avvis eller stopp dersom godkjent forslag bryter dette.
Oppgave «{t['tittel']}»:
{t['oppgave']}
{avgjort(t)}

Godkjent forslag:
{forslag}
{('Kontrollørens vurdering. Linjer som begynner med VILKÅR skal følges:' + chr(10) + t['vilkar']) if t.get('vilkar') else ''}

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
{avgjort(t)}

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
    if d == "UTILGJENGELIG":
        slutt = "ikke vurdert: kontrolløren var utilgjengelig"
        status = "ferdig_med_merknad"
    else:
        status = "feilet" if not ok else (
            "ferdig" if d == "GODKJENT" else "ferdig_med_merknad"
        )
    r = ko("update", id=t["id"], status=status, resultat=resultat, kontroll_ut=ut, sluttvurdering=slutt,
           sammendrag="kontroll %s, kontrollør %s" % ("OK" if ok else "FEILET", d), logg="slutt: " + status)
    push_hvis_tom(r.get("igjen", 1))


def run(lane="general"):
    if lane not in LANES:
        raise ValueError("ugyldig lane: " + lane)
    ACTIVE["worker_id"] = "%s-%s-%s" % (lane, os.uname().nodename, os.getpid())
    ACTIVE["lock_id"] = ""
    os.makedirs(KO_DIR, exist_ok=True)
    if os.path.exists(os.path.join(KO_DIR, "STOPP")):
        return
    pausefil = os.path.join(KO_DIR, "PAUSE")
    if os.path.exists(pausefil):
        with open(pausefil, encoding="utf-8") as f:
            tidspunkt = float(f.readline().strip())
        if tidspunkt > time.time():
            return
        os.unlink(pausefil)
    # Lokal lås er kun per lane. n8n sin atomiske lane- og ressurslås
    # er autoritativ og skal ikke serialisere uavhengige lanes.
    lock = open(os.path.join(KO_DIR, "lock-" + lane), "w")
    try:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
    except OSError:
        return
    t = ko("next", lane=lane, worker_id=ACTIVE["worker_id"]).get("task")
    if not t:
        return
    ACTIVE["lock_id"] = t.get("lock_id")
    try:
        if t.get("fase") == "utfor":
            return utfor(t)
        kritikk = t.get("tilbakemelding", "")
        forrige = ""
        for forsok in (1, 2):
            forslag = hermes(p_forslag(t, kritikk), WORKER, T_WORK)
            if forsok == 1:
                lokal_dom, lokal_tekst = lokal_sjekk(t, forslag)
                ko("update", id=t["id"], logg="lokal sjekk: " + lokal_dom)
                if lokal_dom == "MANGLER":
                    t["forslag"] = forslag
                    kritikk = (
                        "Lokal forhåndssjekk (qwen3:8b) fant at forslaget "
                        "mangler steg: " + lokal_tekst
                    )
                    continue
            vurdering = hermes(p_vurder(t, forslag, forrige), REVIEWER, T_REVIEW)
            t["forslag"] = forslag
            d = dom(vurdering)
            ko("update", id=t["id"], forslag=forslag, vurdering=vurdering,
               logg="forslag %d: %s\n%s" % (forsok, d, vurdering[-3500:]))
            if d == "UTILGJENGELIG":
                ko("update", id=t["id"], logg="kontrollør utilgjengelig, venter 30 minutter")
                pause(30, vurdering[:200])
                ko("retry", id=t["id"])
                return
            if d == "BLOKKERT":
                r = ko("update", id=t["id"], status="parkert",
                       sammendrag="trenger beslutning: " + beslutning(vurdering))
                return push_hvis_tom(r.get("igjen", 1))
            if d == "GODKJENT":
                t["vilkar"] = vurdering
                break
            kritikk = vurdering
            forrige = vurdering
        else:
            r = ko("update", id=t["id"], status="parkert",
                   sammendrag="forslaget ble avvist to ganger av kontrolløren: " + kort(vurdering))
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
        lane = "general"
        if len(a) > 1:
            if a[1].startswith("--lane="):
                lane = a[1].split("=", 1)[1]
            elif a[1] == "--lane" and len(a) > 2:
                lane = a[2]
            elif not a[1].startswith("--"):
                lane = a[1]
        run(lane)
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
