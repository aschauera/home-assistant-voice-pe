# Release-Pairing: Voice-PE-Firmware und HA Voice Bridge

Die Open-Mic-Funktion besteht aus Firmware und Bridge. Beide Komponenten werden getrennt veröffentlicht, aber als ausdrücklich kompatibles Paar betrieben. Für alle künftigen Paare gilt: Beide Seiten haben dieselbe SemVer und denselben `v`-Tag. Die Firmware-Projektversion lautet beispielsweise `1.4.3`, während Firmware und Bridge beide unter dem GitHub-Tag `v1.4.3` veröffentlicht werden.

## Letztes historisches Release-Paar

| Komponente | Default-Branch | Release |
|---|---|---|
| Voice-PE-Firmware | `dev` | [`0.2.1`](https://github.com/aschauera/home-assistant-voice-pe/releases/tag/0.2.1) |
| HA Voice Bridge | `main` | [`v1.4.1`](https://github.com/aschauera/NanoBotSkills/releases/tag/v1.4.1) |

Dieses bereits veröffentlichte Paar stammt aus der früheren Versionskonvention und
bleibt unverändert. Die identische Versionsregel gilt ab dem nächsten Paar.

## Aktuelles gekoppeltes Pre-Release

| Komponente | Default-Branch | Release |
|---|---|---|
| Voice-PE-Firmware | `dev` | [`v1.4.3`](https://github.com/aschauera/home-assistant-voice-pe/releases/tag/v1.4.3) |
| HA Voice Bridge | `main` | [`v1.4.3`](https://github.com/aschauera/NanoBotSkills/releases/tag/v1.4.3) |

Beide Komponenten verwenden Version `1.4.3` und denselben Tag `v1.4.3`.
Da der neue LED-, Timeout-, Audio- und Fast-Path-Stack noch nicht gemeinsam auf
der produktiven Kitchen Voice PE hardwarevalidiert wurde, bleiben beide
Veröffentlichungen zunächst Pre-Releases.

## Verbindliche Regel

Für jede neue Firmware-/Bridge-Veröffentlichung müssen SemVer und `v`-Tag auf
beiden Seiten übereinstimmen. Jedes Firmware-Release muss in seinen
GitHub-Release-Notes die getestete Bridge-Version direkt verlinken. Jedes
Bridge-Release muss umgekehrt die neueste ausdrücklich kompatible Firmware-
Version direkt verlinken.

Ein Verweis auf einen Branch oder auf `latest` reicht nicht, weil diese Ziele veränderlich sind. Die Release-Notizen müssen einen unveränderlichen Tag-Link enthalten.

## Veröffentlichung einer Firmware-Version

1. Kompatible Bridge-Version prüfen:

   ```bash
   gh release view v1.4.3 \
     --repo aschauera/NanoBotSkills \
     --json tagName,isPrerelease,targetCommitish,url
   ```

2. Projektversion und Tag angleichen und den Zielcommit taggen.
3. Release veröffentlichen. Erst das Ereignis `release.published` startet den
   Workflow `Build and publish firmware release`. Pushes, Pull Requests und
   manuelle Workflow-Aufrufe kompilieren keine Firmware.
4. Der Workflow validiert die Quellen und kompiliert mit dem gepinnten
offiziellen ESPHome-Workflow ausschließlich
   `home-assistant-voice.factory.yaml` für das normale 16-MB-Gerät. Er hängt ein
   OTA- und ein Factory-Image, die beiden Standard-YAML-Dateien, das
   Source-Paket, `firmware-release.json` und gemeinsame `SHA256SUMS.txt` an das
   Release. Die 8-MB-Variante gehört nicht zum Release. Vorhandene Assets werden
   nur bei bytegenauer Identität akzeptiert und niemals automatisch ersetzt.
5. Nach erfolgreichem Workflow die veröffentlichten Assets mit
   `scripts/deploy_firmware_release.py <TAG>` auf dem Nanobot-Pi herunterladen
   und vollständig prüfen. Dabei wird lokal nicht kompiliert und nicht
   geflasht.
6. Release-Notes müssen mindestens enthalten:
   - Firmware-SemVer `1.4.3`, gemeinsamer Tag `v1.4.3` und Commit;
   - direkten Link zur kompatiblen Bridge-Version;
   - Status von Source-Tests und GitHub-Release-Build;
   - Prüfsumme des veröffentlichten OTA-Images;
   - Hinweis auf OTA-, USB- und Rollback-Pfad.
7. Ohne gemeinsame Hardwarevalidierung nur als Pre-Release veröffentlichen.
8. Nach Veröffentlichung beide Release-Seiten erneut auf Tag, Commit, Status,
   Assets und gegenseitige Links prüfen.

GitHub Actions kompiliert genau eine Firmwarevariante pro veröffentlichtem
Release, flasht aber niemals ein Gerät. Ein erfolgreicher Release-Build
berechtigt nicht zum Flashen; das produktive Gerät erfordert weiterhin Aschis
ausdrückliche Freigabe.

## Veröffentlichung einer Bridge-Version

Vor Veröffentlichung muss im Bridge-Repository die neueste kompatible Firmware ermittelt werden:

```bash
gh release list --repo aschauera/home-assistant-voice-pe --limit 20
gh release view v1.4.3 \
  --repo aschauera/home-assistant-voice-pe \
  --json tagName,isPrerelease,targetCommitish,url
```

Die Bridge-Release-Notes müssen den ausgegebenen Firmware-Release-Link direkt
enthalten und SemVer sowie Tag der Firmware entsprechen. Gibt es kein
validiertes stabiles Firmware-Pendant, bleibt die Bridge ein Draft oder
Pre-Release.

## Rollback

Ein Rollback wird als Paar geplant:

- Firmware auf ein bekanntes kompatibles OTA- oder Factory-Image zurücksetzen;
- Bridge über das beim Deployment erzeugte Backup oder ein früheres Release zurückrollen;
- danach Versionskonsistenz, Voice-Pipeline, ACK, finale TTS und Folgeturn erneut prüfen.
