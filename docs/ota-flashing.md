# Firmware lokal bauen und kontrolliert per OTA installieren

GitHub Actions kompiliert in diesem Repository keine Firmware. Ein Release
enthält ausschließlich die versionierten YAML-Dateien, die benötigten lokalen
Quellen und Sounds, Metadaten sowie SHA-256-Prüfsummen. Nanobot lädt dieses
unveränderliche Paket auf den lokalen Host, prüft es und kompiliert es dort mit
der exakt festgelegten ESPHome-Version.

Das historische Release `v1.4.2` enthält noch vorkompilierte Binaries. Die hier
beschriebene Source-only-Pipeline gilt für alle Releases, die mit dem Workflow
`Publish firmware sources` veröffentlicht werden.

## Sicherheitsgrenzen

- Firmware und HA Voice Bridge müssen dieselbe SemVer und denselben `v`-Tag
  verwenden.
- GitHub Copilot und GitHub Actions dürfen weder kompilieren noch flashen.
- Ein erfolgreicher lokaler Build ist **keine** Flash-Freigabe.
- Das produktive Kitchen Voice PE darf nur nach ausdrücklicher Freigabe durch
  Aschi geflasht werden.
- Vor jedem Flash muss ein bekannt gutes OTA-Rollback-Image lokal vorhanden
  sein.
- Für Netzwerk-OTA ausschließlich das lokal erzeugte `.ota.bin` verwenden.
- `.factory.bin` ist ausschließlich für USB-Installation oder Recovery.
- Die Acht-Megabyte-Variante nur für nachweislich passende Hardware verwenden;
  das normale Voice Preview Edition verwendet die Standardvariante.
- Während Upload und Neustart Strom und Netzwerk nicht unterbrechen.

## Hardwarevalidierung und Rollback für den Dialog-Timeout

Der 5-Sekunden-Leerlauf-Timeout mit lokalem Bestätigungston ist **nicht
hardwarevalidiert**. Vor einem genehmigten Test sind die lokale WAV-Wiedergabe,
die eingestellte Lautstärke und der Übergang vom Ton zum orangefarbenen
Abschlussimpuls auf einem nicht produktiven Gerät zu prüfen. Mögliche Risiken
sind ein nicht unterstütztes Audioformat, ein zu leiser Ton, abgeschnittene
Wiedergabe oder eine Verzögerung im lokalen Player; die Session muss auch bei
Audiofehlern zuverlässig in `sleeping` wechseln.

Bei Fehlern nach ausdrücklicher Flash-Freigabe das vor dem Update gesicherte
OTA-Image einspielen und Firmware sowie HA Voice Bridge gemeinsam auf das
vorherige bekannte gute Versionspaar zurücksetzen. Ist OTA nicht verfügbar,
den offiziellen USB-Recovery-Pfad aus Abschnitt 5 verwenden. Das
Produktionsgerät in der Küche darf ohne ausdrückliche Freigabe nicht geflasht
werden.

## Inhalt eines Source-only-Releases

Die Release-Automation veröffentlicht mindestens:

- `home-assistant-voice.yaml`;
- `home-assistant-voice.factory.yaml`;
- `home-assistant-voice.8mb.yaml`;
- `home-assistant-voice-source-vX.Y.Z.tar.gz` mit lokalen Komponenten und Sounds;
- `firmware-release.json` mit Tag, Commit, ESPHome-Version und Entrypoints;
- `SHA256SUMS.txt`.

Es werden ausdrücklich keine Firmware-Binaries in GitHub Actions erzeugt.

## Voraussetzungen auf dem Nanobot-Pi

- angemeldete GitHub CLI `gh`;
- lokaler Checkout `/home/nanobot/home-assistant-voice-pe`;
- Python drei;
- isolierte ESPHome-Installation in
  `~/.venvs/esphome-<VERSION>/bin/esphome`;
- Netzwerkzugriff zum Voice PE nur für den späteren OTA-Schritt.

Die ESPHome-Version wird nicht stillschweigend aktualisiert. Fehlt die im
Release verlangte Version, muss sie zuerst explizit in einer isolierten
virtuellen Umgebung installiert werden:

```bash
python3 -m venv "$HOME/.venvs/esphome-<VERSION>"
"$HOME/.venvs/esphome-<VERSION>/bin/python" -m pip install \
  "esphome==<VERSION>"
```

## 1. Release lokal herunterladen, prüfen und kompilieren

Der normale Ablauf baut die Standardvariante und flasht **nicht**:

```bash
cd /home/nanobot/home-assistant-voice-pe
python3 scripts/deploy_firmware_release.py vX.Y.Z
```

Das Script führt dabei aus:

1. alle Release-Assets mit `gh release download` herunterladen;
2. jede Datei gegen `SHA256SUMS.txt` prüfen;
3. Release-Tag und Commit gegen `firmware-release.json` prüfen;
4. das Source-Paket sicher entpacken;
5. die separat veröffentlichten YAML-Dateien bytegenau mit dem Source-Paket
   vergleichen;
6. die exakte ESPHome-Version prüfen;
7. lokal `esphome compile` für den im Release festgelegten Entrypoint ausführen;
8. OTA- und Factory-Image samt lokaler SHA-256-Werte unter
   `~/.cache/voice-pe-firmware/<TAG>/build/` ablegen.

Für nachweisliche Acht-Megabyte-Hardware:

```bash
python3 scripts/deploy_firmware_release.py vX.Y.Z --variant 8mb
```

Der lokale Build erzeugt außerdem `local-build.json`. Diese Datei dokumentiert
Release-Commit, Variante, ESPHome-Version, Entrypoint und Prüfsummen der lokal
erzeugten Images.

## 2. Build prüfen

Vor einer Flash-Freigabe mindestens kontrollieren:

```bash
cat "$HOME/.cache/voice-pe-firmware/vX.Y.Z/build/local-build.json"
ls -lh "$HOME/.cache/voice-pe-firmware/vX.Y.Z/build/"
```

Zusätzlich müssen erfolgreich sein:

- Source-Contract-Tests und YAML-Lint;
- passendes Bridge-Release mit demselben Tag;
- erreichbares Voice PE;
- vorhandenes, bekannt gutes Rollback-OTA-Image;
- dokumentierter USB-Recovery-Pfad.

## 3. OTA nur nach ausdrücklicher Freigabe

Erst nach Aschis ausdrücklicher Flash-Freigabe wird derselbe lokale Ablauf mit
den Sicherheitsparametern gestartet:

```bash
cd /home/nanobot/home-assistant-voice-pe
python3 scripts/deploy_firmware_release.py vX.Y.Z \
  --flash \
  --device 192.168.4.REPLACE_ME \
  --rollback-ota /pfad/zur/bekannt-guten-firmware.ota.bin \
  --flash-confirmation FLASH-KITCHEN-VOICE-PE
```

Das Script kopiert das Rollback-Image in das lokale Build-Verzeichnis, bevor es
`esphome upload` aufruft. Geräteadresse und Rollback-Datei dürfen nicht geraten
werden. Geheimnisse oder OTA-Passwörter werden nicht in das Repository
geschrieben.

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

Dafür ausschließlich ein passendes Factory-Image beziehungsweise den
offiziellen Webinstaller verwenden. Ein USB-Recovery kann eine erneute
Einrichtung oder Adoption erfordern.

### Bridge zurückrollen

Das beim Bridge-Deployment erzeugte Backup verwenden:

```bash
python3 /home/nanobot/NanoBotSkills/scripts/deploy_ha_voice_release.py \
  --rollback /home/nanobot/.nanobot/backups/ha-voice/<BACKUP>
sudo systemctl restart nanobot
```
