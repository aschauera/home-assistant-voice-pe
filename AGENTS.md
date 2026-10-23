# Agent-Hinweise

Vor Änderungen am Branch `open-mic` zuerst
[`docs/branch-status-open-mic.md`](docs/branch-status-open-mic.md)
lesen.

Wichtige Regeln:

- Die Hauptlinie dieses Forks heißt `dev`, nicht `main`.
- Der offene Dialogmodus der Version `0.2.0-dev` liegt auf dem Branch
  `open-mic`; Änderungen nicht versehentlich auf `dev` entwickeln.
- Eine grüne CI auf `origin/dev` bestätigt nur die bereits gemergte Version
  0.1 mit LED-Overrides. Für den Dialogmodus immer die Läufe des Branches
  `open-mic` beziehungsweise seines Pull Requests prüfen.
- Das Produktionsgerät in der Küche niemals ohne erfolgreichen Build,
  Artefaktprüfung, Rollback-Pfad und ausdrückliche Freigabe flashen.
- Änderungen in logisch getrennten Commits halten; Tests und Dokumentation vor
  einem PR aktualisieren.
