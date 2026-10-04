# Gjeldssystem — Brother + Paperless-ngx + n8n

Bygget 4. oktober 2026. Alt er testet og kjørt; det som gjenstår er oppsett
som krever at du logger inn med ditt eget brukernavn og passord.

## Hva du har

| Fil | Hva det er |
|---|---|
| `wf-1-uttrekk.json` | Ligger i n8n. Leser tall fra Paperless, kjører LLM kun når regex feiler |
| `wf-2-ramsey.json` | Ligger i n8n. Kjører simuleringen og lager rapporten |
| `gjeldmotor.mjs` | Selve beregningsmotoren. 36 tester passer |
| `test-gjeldmotor.mjs` | Testene. `node test-gjeldmotor.mjs` |
| `uttrekk.js` | Utrekkskoden fra workflow 1, som egen fil for feilsøking |
| `kreditorer.csv` | De 22 kreditorene, klar til import i Google Sheets |
| `EKSEMPEL-RAPPORT.txt` | Rapporten slik den ferdig ser ut |
| `oversikt.html` | Visuell oversikt |
| `OPPSETT.json` | Trinn-for-trinn oppsett |

## Arkitektur

```
Brother-skanner
      │  "Scan to E-mail", emne GJELD
      ▼
   Gmail  ──────────────────────────┐
      │                             │ Paperless henter posten selv
      ▼                             │ (innebygd IMAP/Gmail OAuth)
Paperless-ngx  10.0.0.131:8000      │
      │  tag: skann                 │
      ▼                             │
  n8n workflow 1  ◄─────────────────┘
      │  regex-uttrekk → LLM kun ved feil
      │  skriver til Google Sheets
      ▼
  Google Sheets  "Gjeldsoversikt"
      │
      ▼
  n8n workflow 2
      │  Ramsey-simulering
      ▼
  Rapport (tekst + oversikt)
```

**Hvorfor Paperless henter posten selv:** Paperless-ngx 6.0 har innebygd
e-postimport. Da slipper n8n Gmail-node og OAuth-credential, og du har
ett sted å slette dokumenter i stedet for to.

**Hvorfor workflow-triggere ikke er satt opp:** Paperless kan kalle en
webhook når et dokument blir lagt til, og da slipper du polling. Det er
et valg jeg har lagt igjen som dokumentert, ikke konfigurert, fordi det
forutsetter at du vil redigere workflowen i GUI.

## Oppsett — de fire tingene bare du kan gjøre

### 1. Paperless-token

Åpne http://10.0.0.131:8000 og logg inn. Hvis du aldri har vært inn,
får du førstegangs-skjermen der du lager superuser.

Deretter: profilikonet → Application API Token
(eller åpne `http://10.0.0.131:8000/api/profile/generate_auth_token`)

Legg tokenen som `PAPERLESS_TOKEN` i Komodo, stack `pc6-ct154-paperless`.
Og som `PAPERLESS_TOKEN` + `OPENROUTER_API_KEY` i stack `pc6-ct103-n8n`.

Test før du går videre:

```bash
curl -H "Authorization: Token <TOKEN>" \
  'http://10.0.0.131:8000/api/documents/?page_size=1'
```

Svar 200 = riktig. Svar 401 = tokenen er feil.

### 2. Tags i Paperless

Lag disse fire taggene: `skann`, `faktura`, `gjeld`, `uutrekt`.

Workflow 1 henter bare dokumenter med tag `skann`. Uten den taggen får
den 0 dokumenter hver gang, uten feilmelding. Det er den vanligste
feilen i oppsett som ligner på dette.

### 3. Skanneren

Trykk på Brother: **Scan → Scan to E-mail**

- Format: **PDF**
- Oppløsning: **300 dpi** for gjeldsdokumenter (200 går, 400 er bare tregere)
- Filnavn: `BROTHER-%Y%m%d-` slik at datoen følger med
- Mottaker: **en egen adresse**, ikke din personlige
- Emne: **GJELD** — workflowen filtrerer på dette

Lag en Gmail-filter: emne inneholder `GJELD` → flytt til merknad `GjeldInn`.
Ikke velg «Merk som lest», du vil se at det kommer.

### 4. Koble Paperless til postkassen

Paperless → Settings → Mail Accounts → Add

- IMAP: `imap.gmail.com`, port `993`, **SSL**
- Username: din fulle gmail-adresse
- Password: enten Google-OAuth eller et app-passord

**Anbefalt: Gmail OAuth** (konto-type 2 i Paperless). Da slipper du
app-passord. Sett opp en OAuth-client i Google Cloud Console, scope
`gmail.readonly`, og trykk «Connect» i Paperless.

**Alternativ: app-passord.** Google-konto → Sikkerhet → 2-trinns
bekreftelse på → App-passord. Kopier det 16-tegns passordet. Mellomromene
er normale, ikke en feil.

Legg også til en Mail Rule: alt med emne `GJELD` får tag `skann`.

Verifiser: Paperless → Tasks skal vise en grønn «Mail Fetch».

## Regnearket

Lag et Google-regneark, navn `Gjeldsoversikt`. Ark `Kreditorer`, rad 1:

```
kreditor | saldo | rente | min_betaling | forfall | dokumentasjon | oppdatert | kilde | status
```

Importer `kreditorer.csv` (er semikolon-delt, som norsk Excel vil ha).

I workflow 2, node «Les kreditor-arket»: bytt `GJELD_REGNEARK_ID` med
ID-en i URL-en din:

```
https://docs.google.com/spreadsheets/d/DENNE_ID/edit
                                     ^^^^^^^^^
```

## Sett budsjettet riktig

Workflow 2 har en «Budsjett»-node med 20 000. Dette er **hvor mye som
faktisk kan gå til gjeld etter hus, mat, bil og andre faste utgifter.**
Ikke nettopptjent.

Er den under summen av minimumsbetalingene, sier systemet fra. Det er
riktig, og det er det viktigste funnet i hele oppsettet.

## Verifisert i denne kjøringen

- Paperless 6.0.0 svarer på `/api/schema/` uten auth — API-et er lest,
  ikke antatt. Endepunkter, enums og felter er hentet derfra.
- Paperless har `workflow_triggers`, `mail_accounts` og `post_document`.
- Alle 12 noder workflow 1 trenger finnes i din n8n.
- n8n API godtok begge workflowene (HTTP 200).
- Motortesten: 36 tester passer.
- Utrekksparseren: 37 beløpsformater + 12 datoformater passer.
- Simuleringen er kjørt to ganger uavhengig og gir samme svar:
  100 måneder / 691 033 kr ved 20 000 kr budsjett.

## Feil du kan møte på

| Symptom | Årsak |
|---|---|
| 0 dokumenter, ingen feil | Taggen `skann` mangler |
| 401 fra Paperless | Token feil, eller n8n ikke restartet etter env-endring |
| Tomt regneark | Google Sheets-credential ikke koblet |
| «OCR-tekst for kort» | Paperless ikke ferdig OCR-et, eller dårlig skann |
| Rapporten sier UTSLAG | Riktig svar, ikke en feil |

## Ikke gjort, og hvorfor

- **Paperless workflow-trigger i stedet for 5-minutters polling.** Mulig,
  og ville spart 1440 API-kall i døgnet, men krever at du redigerer
  workflowen i GUI. Pollingen koster ingenting mer enn litt CPU.
- **Avslagsforhandling automatiskert.** Skal ikke automatiseres. Det er
  en forhandling med en motpart, ikke en API-kall.
- **Gjeldshåndtering integrert.** Det avgjøres av forvalter, ikke av et
  regneark.