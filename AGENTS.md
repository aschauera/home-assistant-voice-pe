# Agent-Hinweise

Vor Änderungen am Branch `custom-firmware` zuerst
[`docs/branch-status-custom-firmware.md`](docs/branch-status-custom-firmware.md)
lesen.

Wichtige Regeln:

- Die Hauptlinie dieses Forks heißt `dev`, nicht `main`.
- Der offene Dialogmodus der Version `0.2.0-dev` liegt derzeit im
  uncommitteten Working Tree. Nicht mit `reset --hard`, `clean` oder einem
  Branchwechsel verwerfen.
- Eine grüne CI auf `origin/dev` bestätigt nur die bereits gemergte Version
  0.1 mit LED-Overrides, nicht den aktuellen Dialogmodus.
- Das Produktionsgerät in der Küche niemals ohne erfolgreichen Build,
  Artefaktprüfung, Rollback-Pfad und ausdrückliche Freigabe flashen.
- Änderungen in logisch getrennten Commits halten; Tests und Dokumentation vor
  einem PR aktualisieren.
