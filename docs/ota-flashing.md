# GitHub-Release prüfen und kontrolliert per OTA installieren

Firmware wird in diesem Repository nicht mehr auf dem Nanobot-Pi kompiliert.
Pull Requests und Pushes validieren nur Quellen. Erst ein veröffentlichtes
GitHub-Release startet den Workflow `Build and publish firmware release`.
Dieser verwendet den gepinnten offiziellen ESPHome-Workflow und baut genau eine
Firmwarevariante: `home-assistant-voice.factory.yaml` für das normale 16-MB
Home Assistant Voice Preview Edition.

Das historische Pre-Release `v1.4.3` war ein Source-only-Release und enthält
keine von diesem Ablauf erwarteten Binärartefakte. Der hier beschriebene Ablauf
gilt für nachfolgende Releases mit Metadatenschema 2.

## Sicherheitsgrenzen

- Firmware und HA Voice Bridge müssen dieselbe SemVer und denselben `v`-Tag
  verwenden.
- GitHub Actions kompiliert ausschließlich beim Ereignis `release.published`.
  Pushes, Pull Requests und manuelle Workflow-Aufrufe kompilieren nicht.
- Pro Release wird nur die Standardvariante für das 16-MB-Gerät gebaut. Die
  8-MB-Variante wird weder kompiliert noch veröffentlicht.
- GitHub Actions und Copilot dürfen niemals ein Gerät flashen.
- Ein erfolgreicher Release-Build oder Download ist **keine** Flash-Freigabe.
- Das produktive Kitchen Voice PE darf nur nach ausdrücklicher Freigabe durch
  Aschi geflasht werden.
- Vor jedem Flash muss ein bekannt gutes OTA-Rollback-Image lokal vorhanden
  sein.
- Für Netzwerk-OTA ausschließlich das verifizierte `.ota.bin` verwenden.
  `.factory.bin` ist ausschließlich für USB-Installation oder Recovery.
- Während Upload und Neustart Strom und Netzwerk nicht unterbrechen.

## Hardwarevalidierung und Rollback für den Dialog-Timeout

Der 5-Sekunden-Leerlauf-Timeout mit lokalem Bestätigungston ist **nicht
hardwarevalidiert**. Vor einem genehmigten Test sind die lokale WAV-Wiedergabe,
die eingestellte Lautstärke und der Übergang vom Ton zum orangefarbenen
Abschlussimpuls auf einem nicht produktiven Gerät zu prüfen. Mögliche Risiken
sind ein nicht unterstütztes Audioformat, ein zu leiser Ton, abgeschnittene
Wiedergabe oder eine Verzögerung im lokalen Player; die Session muss auch bei
Audiofehlern zuverlässig in `sleeping` wechseln.

Bei Fehlern nach ausdrücklicher Flash-Freigabe das bekannte gute OTA-Image
einspielen und Firmware sowie HA Voice Bridge gemeinsam auf das vorherige
Versionspaar zurücksetzen. Ist OTA nicht verfügbar, den offiziellen
USB-Recovery-Pfad verwenden.

## Inhalt eines Release-Builds

Die Release-Automation veröffentlicht gemeinsam:

- `home-assistant-voice.yaml`;
- `home-assistant-voice.factory.yaml`;
- `home-assistant-voice-source-vX.Y.Z.tar.gz` mit lokalen Komponenten und Sounds;
- `home-assistant-voice-standard-vX.Y.Z.ota.bin` für Netzwerk-OTA;
- `home-assistant-voice-standard-vX.Y.Z.factory.bin` für USB/Recovery;
- `firmware-release.json` mit Tag, Commit, ESPHome-Version, Standard-Entrypoint
  und SHA-256 der beiden Firmware-Images;
- `SHA256SUMS.txt` für den vollständigen veröffentlichten Asset-Satz.

`home-assistant-voice.8mb.yaml` bleibt gegebenenfalls als Entwicklungsquelle im
Repository, ist aber kein Release-Entrypoint oder Release-Asset.

## 1. Release veröffentlichen und Workflow abwarten

Die Projektversion im Standard-Entrypoint muss zum Release-Tag passen. Nach dem
Veröffentlichen des Releases startet automatisch der einzige Firmware-Build.
Vor der lokalen Bereitstellung muss der Workflow vollständig erfolgreich sein.
Ein frisch veröffentlichtes Release kann bis dahin vorübergehend noch keine
Firmware-Assets enthalten.

Der Workflow führt aus:

1. exakten Release-Tag und Commit auflösen;
2. Contract-/Unit-Tests ausführen und unveränderliche Quellen paketieren;
3. mit dem gepinnten offiziellen ESPHome-Workflow ausschließlich
   `home-assistant-voice.factory.yaml` kompilieren;
4. genau ein OTA-/Factory-Paar akzeptieren;
5. Metadaten und gemeinsame SHA-256-Prüfsummen erzeugen;
6. alle verifizierten Assets an dasselbe GitHub-Release hängen;
7. den endgültigen Asset-Namenssatz gegen die lokal erzeugte Liste prüfen.

Es gibt bewusst keinen `workflow_dispatch`-Build und keinen zweiten
8-MB-Build. Bei einer erneuten Ausführung akzeptiert der Workflow vorhandene
Assets nur, wenn Namen und Inhalte vollständig identisch sind. Teilweise,
fremde oder veränderte Assets führen zum Abbruch und werden nie automatisch
überschrieben.

## 2. Release lokal herunterladen und prüfen

Voraussetzungen:

- angemeldete GitHub CLI `gh`;
- lokaler Checkout `/home/nanobot/home-assistant-voice-pe`;
- Python drei.

Für Download und Prüfung ist keine lokale ESPHome-Installation nötig:

```bash
cd /home/nanobot/home-assistant-voice-pe
python3 scripts/deploy_firmware_release.py vX.Y.Z
```

Das Script:

1. lädt alle Assets des angegebenen Releases herunter;
2. verlangt, dass der heruntergeladene Asset-Satz exakt `SHA256SUMS.txt`
   entspricht, damit weder Dateien fehlen noch ungeprüfte Dateien verwendet
   werden;
3. prüft jede SHA-256-Prüfsumme;
4. prüft Metadatenschema, Release-Tag und unveränderlichen Git-Commit;
5. akzeptiert ausschließlich die Variante `standard-16mb`;
6. prüft OTA- und Factory-Image zusätzlich gegen `firmware-release.json`;
7. vergleicht die direkten Standard-YAML-Dateien bytegenau mit dem Source-Paket;
8. legt die verifizierten Images unter
   `~/.cache/voice-pe-firmware/<TAG>/verified/` ab;
9. beendet sich ohne Flash.

Kontrolle:

```bash
ls -lh "$HOME/.cache/voice-pe-firmware/vX.Y.Z/verified/"
sha256sum "$HOME/.cache/voice-pe-firmware/vX.Y.Z/verified/"*.ota.bin
```

Zusätzlich müssen erfolgreich beziehungsweise vorhanden sein:

- Source-Validation und GitHub-Release-Build;
- passendes Bridge-Release mit demselben Tag;
- erreichbares Voice PE;
- bekannt gutes Rollback-OTA-Image;
- dokumentierter USB-Recovery-Pfad.

## 3. OTA nur nach ausdrücklicher Freigabe

Das Release-Script kompiliert auch beim Flash nicht. Es nutzt das bereits
verifizierte OTA-Image. Für den Upload benötigt es jedoch den zur Release-
Metadatei passenden ESPHome-CLI-Stand. Fehlt die isolierte Installation:

```bash
python3 -m venv "$HOME/.venvs/esphome-<VERSION>"
"$HOME/.venvs/esphome-<VERSION>/bin/python" -m pip install \
  "esphome==<VERSION>"
```

Erst nach Aschis ausdrücklicher Flash-Freigabe:

```bash
cd /home/nanobot/home-assistant-voice-pe
python3 scripts/deploy_firmware_release.py vX.Y.Z \
  --flash \
  --device 192.168.4.REPLACE_ME \
  --rollback-ota /pfad/zur/bekannt-guten-firmware.ota.bin \
  --flash-confirmation FLASH-KITCHEN-VOICE-PE
```

Das Script verifiziert das Release bei jedem Lauf erneut, kopiert das
Rollback-Image in das lokale `verified`-Verzeichnis und ruft danach
`esphome upload` mit dem veröffentlichten OTA-Image auf. Es führt keinen
Compiler aus. Geräteadresse und Rollback-Datei dürfen nicht geraten werden;
Geheimnisse oder OTA-Passwörter gehören nicht ins Repository.

## 4. Physische Verifikation

Nach dem Neustart mindestens prüfen:

1. Das Voice PE ist in ESPHome und Home Assistant wieder online.
2. Firmware und laufende Bridge melden dasselbe Versionspaar.
3. Wake Word und erster Turn funktionieren.
4. Lokaler Remote-ACK und finale TTS werden vollständig abgespielt.
5. Ein Folgeturn funktioniert ohne neues Wake Word.
6. Exit-Phrasen, Leerlauf-Timeout, mittlere Taste und Mute beenden die Session
   wie in `docs/dialogmodus.md` beschrieben.
7. LED-Zustände und Diagnosesensoren entsprechen dem Release.
8. Es treten keine unerwarteten Reboots, Audioabbrüche oder Endlossessions auf.

Die ESPHome-Weboberfläche behält ihre eigene YAML. Ein späteres
`Install -> Wirelessly` aus dem Device Builder kann die Custom Firmware mit dem
dort gespeicherten Stand überschreiben.

## 5. Rollback und Recovery

### Gerät ist per OTA erreichbar

Das vor dem Flash gesicherte bekannte gute `.ota.bin` mit ESPHome OTA
zurückspielen. Firmware und Bridge als Paar zurückrollen und danach erneut
physisch prüfen.

### Gerät ist nicht mehr per OTA erreichbar

USB-Recovery über den offiziellen ESPHome-Webinstaller:

```text
https://esphome.github.io/home-assistant-voice-pe/
```

Dafür ausschließlich das passende Factory-Image beziehungsweise den
offiziellen Webinstaller verwenden. Ein USB-Recovery kann eine erneute
Einrichtung oder Adoption erfordern.

### Bridge zurückrollen

Das beim Bridge-Deployment erzeugte Backup verwenden:

```bash
python3 /home/nanobot/NanoBotSkills/scripts/deploy_ha_voice_release.py \
  --rollback /home/nanobot/.nanobot/backups/ha-voice/<BACKUP>
sudo systemctl restart nanobot
```
