# -*- coding: utf-8 -*-
"""CAUDINOTICIAS en audio: genera el MP3 de la edición con dos voces de Supertonic 3 que se turnan por noticia.

Uso: python3 locutor.py pistas.json carpeta_modelo salida.mp3 capitulos.json
  pistas.json: lista [{"sec", "titulo", "voz"}] (la arma audio.py)
Escribe el MP3 (mono, 64 kbps) y capitulos.json con el segundo de inicio de cada pista.
"""
import json, os, re, subprocess, sys, tempfile
import numpy as np, soundfile as sf, sherpa_onnx as so

VOZ_A, VOZ_B = 1, 5          # voz 7 (femenina B) y voz 8 (masculina A)
PAUSA_FRASE, PAUSA_PISTA = 0.22, 0.9


def motor(d):
    cfg = so.OfflineTtsConfig(model=so.OfflineTtsModelConfig(supertonic=so.OfflineTtsSupertonicModelConfig(
        duration_predictor=f"{d}/duration_predictor.int8.onnx", text_encoder=f"{d}/text_encoder.int8.onnx",
        vector_estimator=f"{d}/vector_estimator.int8.onnx", vocoder=f"{d}/vocoder.int8.onnx", tts_json=f"{d}/tts.json",
        unicode_indexer=f"{d}/unicode_indexer.bin", voice_style=f"{d}/voice.bin"), num_threads=os.cpu_count() or 4))
    return so.OfflineTts(cfg)


def frases(t):
    out = []
    for p in re.split(r"(?<=[.;:!?])\s+", t):
        p = p.strip()
        if not p: continue
        if out and len(out[-1]) + len(p) < 120: out[-1] += " " + p
        else: out.append(p)
    return out


def main(ruta_pistas, d, salida, ruta_cap):
    pistas = json.load(open(ruta_pistas, encoding="utf-8"))
    tts = motor(d); sr = tts.sample_rate
    audio, caps, t = [], [], 0.0
    for i, p in enumerate(pistas):
        sid = VOZ_A if i % 2 == 0 else VOZ_B
        caps.append({"inicio": round(t, 2), "sec": p["sec"], "titulo": p["titulo"]})
        for f in frases(p["voz"]):
            g = so.GenerationConfig(); g.sid = sid; g.speed = 1.0; g.num_steps = 8; g.extra = {"lang": "es"}
            a = np.array(tts.generate(f, g).samples, dtype=np.float32)
            audio += [a, np.zeros(int(sr * PAUSA_FRASE), dtype=np.float32)]
            t += len(a) / sr + PAUSA_FRASE
        audio.append(np.zeros(int(sr * PAUSA_PISTA), dtype=np.float32)); t += PAUSA_PISTA
        print(f"{i + 1}/{len(pistas)} {p['titulo'][:50]}", flush=True)
    x = np.concatenate(audio); x = x / max(1e-6, np.abs(x).max()) * 0.92
    with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
        sf.write(tmp.name, x, sr)
        subprocess.run(["ffmpeg", "-loglevel", "error", "-y", "-i", tmp.name, "-ac", "1", "-ar", "24000", "-b:a", "64k", salida], check=True)
    os.unlink(tmp.name)
    json.dump({"duracion": round(t, 1), "capitulos": caps}, open(ruta_cap, "w", encoding="utf-8"), ensure_ascii=False)
    print(f"{salida}: {t / 60:.1f} min")


if __name__ == "__main__":
    main(*sys.argv[1:5])
