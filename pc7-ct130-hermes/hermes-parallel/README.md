# Hermes parallell CT arbeidsflyt

Dette er en konservativ, lesende inventar- og planleggingsmodell for CT130. Inventaret leser CT-status parallelt og deterministisk. Planleggeren velger høyst tre uavhengige A-oppgaver, med én CT-lås per oppgave og eksplisitte ressurslåser for repository og kartpublisering. B venter på Roger og blokkerer ikke. C (OPNsense, Emby, nettverk eller vert) kan aldri kjøre. Ukjent klasse blir B.

K44 er seedet som A-avsluttet med feil til B fordi den avvek fra godkjent sikkerhetsomfang. K45 er B og aldri autoeksekverbar. K47 er A-avsluttet. Gamle køoppgaver endres ikke.

Før en virkelig A-adapter kan kobles på må den følge plasskontroll, beholdt snapshot, én avgrenset endring og helsekontroll. Feil skal rulle tilbake én gang til snapshot uten retteforsøk og flytte funnet til B. Tre feil på rad pauser planleggeren og varsler. Nødstopp er `~/.hermes/ko/STOPP`; den gamle hermes-ko.timer og nye timer skal aldri være aktive samtidig.

Kjør `hermes_parallel_dispatch.py --self-test` før aktivering.
