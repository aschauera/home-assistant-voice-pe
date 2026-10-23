# Branch-Status: `custom-firmware`

> Agent-Handoff und Arbeitsstand vom 23. Oktober 2026. Vor Änderungen zuerst
> diesen Stand mit `git status`, `git diff` und den aktuellen CI-Läufen
> abgleichen.

## Kurzfassung

Der Branch entwickelt eine eigene Firmware für die Home Assistant Voice:
Preview Edition. Ziel ist ein begrenzter, sicher beendbarer Dialog mit mehreren
aufeinanderfolgenden Turns ohne erneutes Wake Word. Die bestehende
Home-Assistant-Assist-Pipeline bleibt erhalten: lokale Intents laufen weiterhin
lokal, nur nicht lokal beantwortete Anfragen gehen an den konfigurierten
Conversation Agent.

Die Implementierung ist **halbduplex**. Barge-in, Full-Duplex und eine eigene
Voice Activity Detection gehören ausdrücklich nicht zum aktuellen Umfang.

**Wichtig:** Die Hauptlinie dieses Forks heißt `dev`; es gibt keinen
`main`-Branch. Der Branch `custom-firmware` baut auf `origin/dev` auf und hält
die Version 0.2 mit offenem Dialogmodus in logisch getrennten Commits. Neue
Firmwarearbeit gehört auf diesen Branch und nicht direkt auf `dev`.

## Branch- und Remote-Beziehungen

| Referenz | Stand | Bedeutung |
|---|---|---|
| `upstream/dev` | `d4e6fa4` | Offizielle ESPHome-Quellbasis ohne Nanobot-Erweiterungen |
| `origin/dev` | `b257923` | Hauptlinie des Forks; Merge von PR Nummer eins |
| `custom-firmware` | `origin/dev` plus eigene Commits | Veröffentlichter Entwicklungsbranch für Version 0.2 |
| `feat/nanobot-led-control` | `9ea10c0` | Alter, bereits gemergter Feature-Branch; Remote-Branch entfernt |

Wesentliche eigene Commits des Branches:

- `d897294`: Agent-Handoff und Branch-Dokumentation;
- `df01e05`: vendorter Voice-Assistant-Playback-Fix;
- `46e5a27`: begrenzter offener Dialogmodus und lokales ACK-Audio;
- `8efdf91`: Contract-Tests und CI für ESPHome 2026.10.0;
- `0b1e318`: Anpassung der vendorten Audioquelle an die 2026.10-API.

Der Branch trackt `origin/custom-firmware`. Der Working Tree soll nach dem
Dokumentations-Commit sauber sein.

## Vergleich zur Hauptlinie `dev`

### Bereits in `origin/dev` enthalten: Version 0.1

PR [Nummer eins](https://github.com/aschauera/home-assistant-voice-pe/pull/1)
führte folgende Funktionen ein:

- Home-Assistant-Select `Nanobot LED state`;
- Zustände `off`, `thinking`, `ack`, `replying`, `follow_up`, `done`, `error`;
- zeitlich begrenzte LED-Overrides mit Fail-safe;
- Priorität für Provisionierung, Verbindungsfehler, Hardwareinteraktion, Timer,
  native Voice-Assistant-Fehler und Mute;
- deaktivierter offizieller HTTP-Updater, damit die Custom Firmware nicht
  unbemerkt durch Upstream-Firmware ersetzt wird;
- fork-sicherer GitHub-Actions-Build für Factory- und Acht-Megabyte-Variante.

Der Build von `origin/dev` war in GitHub Actions erfolgreich:

- Run `39925822229`;
- `home-assistant-voice.factory.yaml` erfolgreich;
- `home-assistant-voice.8mb.yaml` erfolgreich;
- Artefakte `home-assistant-voice` und `ha-voice-8mb` wurden erzeugt.

Diese grüne CI bestätigt ausschließlich den committed Stand von Version 0.1,
nicht automatisch den offenen Dialogmodus auf `custom-firmware`.

### Auf `custom-firmware` committed: Version 0.2

Der Branch erweitert Version 0.1 um:

- Konfigurationsschalter `Open dialog mode`, standardmäßig aktiv;
- Wake-freie Folgeturns über `voice_assistant.start_continuous`;
- maximale Sessiondauer von zwei Minuten;
- maximal zwanzig Antworten pro Session;
- deterministisches lokales Sleep Word `Stop`;
- zusätzliche erkannte Exit-Phrasen wie `Tschüss`, `Bye`, `Goodbye`,
  `Auf Wiedersehen` und `Dialog beenden`;
- Abbruch über mittlere Taste, Hardware-/Software-Mute, Verbindungsverlust und
  Voice-Assistant-Fehler;
- Diagnose-Entities `Dialog state` und `Dialog session active`;
- Dialogzustände `sleeping`, `activating`, `waiting`, `listening`,
  `processing`, `remote_ack`, `replying`, `follow_up`, `ending`, `error`;
- lokal eingebettete deutsch-österreichische Bestätigung `Einen Moment.`;
- ESPHome-Native-API-Aktion `dialog_remote_ack` für den Remote-Agent-Pfad;
- angepasste Dialog-LEDs: Grün für Öffnen/Schließen, Violett für Folgeturn,
  Amber für Verarbeitung, Blau für Remote-ACK, Cyan für Antwort und Rot für
  Fehler;
- Upgrade der Konfiguration und CI auf ESPHome `2026.10.0`;
- Projektversion `0.2.0-dev` für Factory- und Acht-Megabyte-Variante;
- lokal vendorte `voice_assistant`-Komponente als Playback-Race-Fix;
- Contract-Tests und erweiterte YAML-Lint-CI.

## Zweck und Architektur

### Gewünschter Ablauf

1. Ein normales Wake Word startet eine begrenzte Dialogsession.
2. Home Assistant hört mit seiner bestehenden VAD zu.
3. Lokale Intents werden weiterhin von Home Assistant ausgeführt.
4. Nur der ausgewählte Remote Conversation Agent darf
   `dialog_remote_ack` auslösen.
5. Die Antwort wird vollständig wiedergegeben.
6. Danach öffnet Continuous Mode den nächsten Folgeturn ohne neues Wake Word.
7. Ein Exit-Ereignis beendet Continuous Mode, schließt das Mikrofon und setzt
   die Firmware auf den normalen Idle-Zustand zurück.

### Abgrenzung

Der Branch baut keinen eigenen Sprachstack. Wake Word, STT, lokale
Intent-Erkennung, Conversation Agent, TTS und VAD bleiben Bestandteile der
Home-Assistant-Assist-Pipeline. Die Firmware ergänzt Sessionsteuerung, lokale
ACK-Wiedergabe, LED-Feedback und Schutzgrenzen.

Es gibt derzeit **kein Barge-in**. Normale Wake Words werden während einer
aktiven Dialogsession ignoriert; `Stop` beendet die Session. Die Firmware kann
außerdem nicht selbst erkennen, ob Home Assistant lokal oder remote geroutet
hat. Dafür braucht die Nanobot-Conversation-Integration den dokumentierten
API-Hook.

## Relevante Dateien

| Datei | Inhalt/Zweck |
|---|---|
| `home-assistant-voice.yaml` | Dialogzustandsmaschine, Exit-Pfade, LED-Steuerung, API-Aktion und Voice-Assistant-Callbacks |
| `home-assistant-voice.factory.yaml` | Factory-Build, Projektversion `0.2.0-dev`, kein offizieller HTTP-Updater |
| `home-assistant-voice.8mb.yaml` | Acht-Megabyte-Build, Projektversion `0.2.0-dev` |
| `sounds/remote_ack_einen_moment.mp3` | Lokal eingebettetes ACK-Audio |
| `custom_components/voice_assistant/` | Gepinnter Playback-Start-/Continuous-Mode-Fix |
| `docs/dialogmodus.md` | Fachliche Architektur, Zustände, Integrationsvertrag, Grenzen und Rollback |
| `tests/test_custom_firmware.py` | Statische Contract- und Provenienztests |
| `.github/workflows/build.yml` | Build beider Firmwarevarianten mit ESPHome 2026.10.0 |
| `.github/workflows/yaml-lint.yml` | YAML-Lint plus Python-Contract-Tests |

## Vendorte ESPHome-Komponente

`custom_components/voice_assistant/voice_assistant.h` stammt unverändert aus
`esphome/esphome`, PR `19408`, Commit
`04caa3846f3e94b51dd2de3ca25c5d935aa992da`. Die C++-Datei enthält dieselbe
Korrektur mit drei mechanischen ESPHome-2026.10.0-Anpassungen von `fill(0)` auf
`fill(0, false)`. Die Komponente verhindert, dass Continuous Mode das Mikrofon
erneut öffnet, bevor eine verspätet gestartete oder noch laufende TTS-Ausgabe
wirklich beendet ist.

`__init__.py` basiert auf ESPHome 2026.10.0 und ergänzt die dazugehörige
Codegen-Option `tts_playback_start_timeout`. Details und Prüfsummen stehen in
`custom_components/voice_assistant/README.md` und den Contract-Tests.

Die vendorte Komponente erst entfernen, wenn ein veröffentlichter ESPHome-Tag
denselben Fix enthält und beide Firmwarevarianten dagegen erfolgreich gebaut
und außerhalb des Produktionsgeräts getestet wurden.

## Integrationsgrenze zu Nanobot

Die lokale Bestätigung darf nicht bei lokalen Home-Assistant-Intents ertönen.
Die Nanobot-Conversation-Integration muss daher:

1. `satellite_id` beziehungsweise `device_id` aus dem Conversation Input
   auswerten;
2. erst beim tatsächlichen Eintritt in `conversation.nanobot` die zum Gerät
   gehörende ESPHome-Aktion `dialog_remote_ack` fire-and-forget aufrufen;
3. die Remote-Anfrage parallel ohne Warten fortsetzen;
4. die bisherige gestreamte ACK-TTS für dieses Gerät deaktivieren, damit keine
   doppelte Bestätigung gesprochen wird;
5. bei fehlender Aktion oder unbekanntem Satelliten normal ohne ACK fortfahren.

Diese Nanobot-/Home-Assistant-Integrationsänderung liegt nicht in diesem
Firmware-Repository und ist noch nicht als End-to-End-Verhalten verifiziert.

## Aktueller Prüfstand

Am 23. Oktober 2026 wurde geprüft:

- `python3 -m unittest discover -s tests -v`: **fünf von fünf Tests bestanden**;
- YAML-Lint und Contract-Tests: GitHub-Actions-Run `39963914491` erfolgreich;
- Firmware-Build: GitHub-Actions-Run `39963909725` erfolgreich;
- `home-assistant-voice.factory.yaml` mit ESPHome 2026.10.0 kompiliert;
- `home-assistant-voice.8mb.yaml` mit ESPHome 2026.10.0 kompiliert;
- beide Artefaktarchive entpackt und ihre Manifeste geprüft;
- beide Manifeste melden Projektversion `0.2.0-dev` und Chipfamilie `ESP32-S3`.

Wichtige Firmware-Prüfsummen:

| Datei | SHA-256 |
|---|---|
| `home-assistant-voice-esp32s3.factory.bin` | `bbe437a766ec0be965f628c6b3fdfe6b56ddb63638bc9deff00680e4b6fffcdd` |
| `home-assistant-voice-esp32s3.ota.bin` | `f58649231b7974fe5e7ddebfdc0fab2e72c96405e58868be5db853e46c1d8885` |
| `ha-voice-8mb-esp32s3.factory.bin` | `11aeec5f7699936eaa7efcbf67ef35c37c887c02d19a3d8678b920001794d917` |
| `ha-voice-8mb-esp32s3.ota.bin` | `240b37f2c2abd4545fdc218a0057511f8b72aa492c4839f2b50a28d61c7e69ee` |

Der erste Build-Run `39962290987` scheiterte an drei veralteten Aufrufen von
`RingBufferAudioSource::fill(0)`. Commit `0b1e318` passte diese entsprechend der
ESPHome-2026.10.0-API auf `fill(0, false)` an; der anschließende vollständige
Build war grün.

Daraus folgt: Version 0.2 ist statisch geprüft, vollständig kompiliert und als
CI-Artefakt inspiziert, aber noch **nicht auf Hardware validiert**.

## Produktionsstatus und Sicherheitsgrenze

Das Küchengerät ist das einzige Produktionsgerät. Von diesem Branch wurde
nichts geflasht. Ein erfolgreicher Build allein ist noch keine
Installationsfreigabe.

Bekannte Produktions-Entities:

- `assist_satellite.home_assistant_voice_0a6c07_assist_satellite`
- `light.home_assistant_voice_0a6c07_led_ring`
- `media_player.home_assistant_voice_0a6c07_media_player`

**Die Produktions-Voice-PE darf erst nach erfolgreichem Build beider Varianten,
Artefaktprüfung, dokumentiertem Rollback-Pfad und ausdrücklicher Freigabe durch
Aschi aktualisiert werden.**

## Sichere nächste Schritte

1. Den Remote-ACK-Hook in der Nanobot-Conversation-Integration separat
   implementieren und testen.
2. Zustandsübergänge, Exit-Pfade, lange/verspätete TTS und Selbsthören zunächst
   auf Nicht-Produktionshardware oder in einer kontrollierten Testumgebung
   validieren.
3. Erst danach eine explizite Flash-Freigabe einholen.

## Schnelle Wiederaufnahme für Agents

```bash
git status --short --branch
git diff --stat
git diff -- home-assistant-voice.yaml
python3 -m unittest discover -s tests -v
gh run list --repo aschauera/home-assistant-voice-pe --limit 10
```

Nicht von einer grünen CI auf `origin/dev` auf die Buildfähigkeit von
`custom-firmware` schließen. Vor jeder strukturellen Änderung zuerst den
Branch-Diff und `docs/dialogmodus.md` vollständig lesen.
