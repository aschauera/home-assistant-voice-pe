# Agent-Hinweise

Der Open-Mic-Modus ist ab Firmware `0.2.0` Bestandteil des Default-Branches
`dev`. Für historischen Branch-Kontext kann
[`docs/branch-status-open-mic.md`](docs/branch-status-open-mic.md) gelesen werden.
Für Installation oder Recovery niemals Befehle improvisieren, sondern die
geprüfte OTA-Anleitung unter
[`docs/ota-flashing.md`](docs/ota-flashing.md) verwenden. Die verbindliche
Release-Kopplung steht in
[`docs/release-pairing.md`](docs/release-pairing.md).

Wichtige Regeln:

- Die Hauptlinie dieses Forks heißt `dev`, nicht `main`.
- Der offene Dialogmodus wird auf `dev` weiterentwickelt. Feature-Arbeit gehört
  in eigene Branches und wird per Merge-Commit nach `dev` übernommen.
- Jede neue Firmware-Version muss in den Release-Notes die kompatible HA Voice
  Bridge direkt verlinken. Umgekehrt muss jedes neue Bridge-Release die letzte
  kompatible Firmware-Version direkt verlinken.
- Firmware und HA Voice Bridge verwenden künftig stets dieselbe SemVer und
  denselben `v`-Tag als fest gekoppeltes Paar: Firmware-Projektversion `1.4.3`
  und Git-Tag `v1.4.3` gehören zur Bridge-Version `1.4.3` mit Tag `v1.4.3`.
  Historische Paare wie Firmware `0.2.1` mit Bridge `v1.4.1` bleiben unverändert.
- Das aktuelle gekoppelte Pre-Release ist Firmware `1.4.3` mit Tag `v1.4.3`
  zusammen mit HA Voice Bridge `1.4.3` unter demselben Tag. Bis zur gemeinsamen
  Hardwarevalidierung bleiben beide Veröffentlichungen Pre-Releases.
- Gibt es noch kein gemeinsam validiertes stabiles Paar, beide Seiten nur als
  Draft oder Pre-Release kennzeichnen.
- Das Produktionsgerät in der Küche niemals ohne erfolgreichen Build,
  Artefaktprüfung, Rollback-Pfad und ausdrückliche Freigabe flashen.
- Für Netzwerk-OTA ausschließlich `home-assistant-voice-esp32s3.ota.bin`
  verwenden; `factory.bin` ist USB-Installation beziehungsweise Recovery.
- Vor dem Flash muss die HA Voice Bridge des gleichen gekoppelten Versionspaars
  aus dem Default-Branch `main` von `aschauera/NanoBotSkills` vollständig laufen.
- Änderungen in logisch getrennten Commits halten; Tests und Dokumentation vor
  einem PR aktualisieren.

## Build- und Deployment-Grenze

- GitHub Copilot und GitHub Actions dürfen in diesem Repository keine Firmware
  kompilieren, keine Firmware-Binaries erzeugen und kein Gerät flashen.
- Insbesondere dürfen GitHub Copilot und andere Cloud-Agenten weder
  `esphome compile` noch `esphome run` oder `esphome upload` ausführen.
- Pull Requests werden ausschließlich mit YAML-Lint und den lokalen
  Contract-/Unit-Tests validiert.
- Release-Automation darf nur die versionierten YAML- und Source-Dateien
  paketieren und mit Prüfsummen veröffentlichen.
- Kompilierung und Flash erfolgen ausschließlich lokal durch Nanobot mit der im
  Release festgelegten ESPHome-Version. Das Produktionsgerät darf weiterhin
  nur nach ausdrücklicher Freigabe geflasht werden.
