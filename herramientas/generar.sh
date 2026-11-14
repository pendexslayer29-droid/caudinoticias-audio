#!/bin/bash
# CAUDINOTICIAS en audio: genera el audio de la edición, lo publica en GitHub Pages y agrega el botón al JSON validado.
# Uso (desde la raíz de este repositorio):
#   bash herramientas/generar.sh /ruta/ediciones/AAAA-MM-DD.validada.json [dominical]
# Deja el MP3 en /tmp/caudinoticias_AAAA-MM-DD.mp3 y escribe en el JSON validado el campo "audio" {url, minutos}.
set -e
ED="$1"; TIPO="${2:-diaria}"
FECHA=$(python3 -c "import json,sys;print(json.load(open(sys.argv[1]))['fecha'])" "$ED")
TEXTO=$(python3 -c "import json,sys;print(json.load(open(sys.argv[1]))['fecha_texto'])" "$ED")
MOD=/tmp/supertonic; T=/tmp/cn_audio_$FECHA; mkdir -p $T
python3 -c "import sherpa_onnx, soundfile, num2words" 2>/dev/null || pip install --break-system-packages -q "sherpa-onnx>=2.0.1" soundfile num2words
if [ ! -f $MOD/voice.bin ]; then
  mkdir -p $MOD
  curl -sL https://github.com/k2-fsa/sherpa-onnx/releases/download/tts-models/sherpa-onnx-supertonic-3-tts-int8-2026-05-11.tar.bz2 | tar xj -C $MOD --strip-components=1
fi
python3 herramientas/guion.py "$ED" --json $T/pistas.json
python3 herramientas/locutor.py $T/pistas.json $MOD /tmp/caudinoticias_$FECHA.mp3 $T/capitulos.json
python3 herramientas/sitio.py "$FECHA" "$TEXTO" $T/capitulos.json /tmp/caudinoticias_$FECHA.mp3 "$TIPO"
bash herramientas/publicar.sh "$FECHA"
python3 - "$ED" "$FECHA" $T/capitulos.json <<'PY'
import json, sys
ed = json.load(open(sys.argv[1], encoding="utf-8")); cap = json.load(open(sys.argv[3], encoding="utf-8"))
ed["audio"] = {"url": f"https://pendexslayer29-droid.github.io/caudinoticias-audio/?d={sys.argv[2]}", "minutos": max(1, round(cap["duracion"] / 60))}
json.dump(ed, open(sys.argv[1], "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print("Botón de audio agregado:", ed["audio"])
PY
