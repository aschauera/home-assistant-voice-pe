# Gepinnte Voice-Assistant-Komponente

Die C++-Implementierung ist eine unveränderte, lokale Momentaufnahme der
ESPHome-Komponente `voice_assistant` aus:

- Upstream: `esphome/esphome`
- Pull Request: `#19408`
- Commit: `04caa3846f3e94b51dd2de3ca25c5d935aa992da`
- Abrufdatum: 23. Oktober 2026

`voice_assistant.h` stammt exakt aus diesem Commit. `voice_assistant.cpp` ist
inhaltlich dieselbe Korrektur, enthält aber drei mechanische Anpassungen an die
ESPHome-2026.10.0-API: Aufrufe von `RingBufferAudioSource::fill(0)` wurden zu
`fill(0, false)`, entsprechend der veröffentlichten Komponente dieses Releases.
`__init__.py` basiert auf ESPHome 2026.10.0 und ergänzt daraus die validierte
Option `tts_playback_start_timeout`, damit die Komponente mit der
veröffentlichten Codegen-API kompatibel bleibt.

Der Patch behebt für den offenen Dialogmodus den bekannten Fehler, bei dem die
Voice PE nach einem festen Timeout erneut zuhört, obwohl die eigene TTS-Antwort
noch nicht begonnen hat oder noch abgespielt wird. Die lokale Kopie verhindert,
dass ein beweglicher PR-Branch oder ESPHome `dev` unbemerkt den Firmware-Build
verändert.

Die Dateien dürfen erst entfernt werden, wenn ein veröffentlichter ESPHome-Tag
dieselbe Korrektur enthält und beide Firmwarevarianten dagegen erfolgreich
gebaut und auf einem Nicht-Produktionsgerät getestet wurden.
