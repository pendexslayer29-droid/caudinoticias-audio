# -*- coding: utf-8 -*-
"""Agrega la edición del día al sitio «CAUDINOTICIAS en audio» (GitHub Pages) y al canal de pódcast.

Uso (desde la raíz del repositorio):
  python3 herramientas/sitio.py AAAA-MM-DD "Lunes 9 de noviembre de 2026" capitulos.json audio_del_dia.mp3 [dominical]
Copia el MP3 a audio/AAAA-MM-DD.mp3, actualiza dias.json, index.html y feed.xml, y borra los audios de más de 7 días.
"""
import json, os, shutil, subprocess, sys
from datetime import date, datetime, timezone, timedelta
from email.utils import format_datetime
from xml.sax.saxutils import escape

BASE = "https://pendexslayer29-droid.github.io/caudinoticias-audio/"
DIAS = ["Lun", "Mar", "Mié", "Jue", "Vie", "Sáb", "Dom"]
MESES = ["ene", "feb", "mar", "abr", "may", "jun", "jul", "ago", "set", "oct", "nov", "dic"]
RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LIMA = timezone(timedelta(hours=-5))


def main(fecha, fecha_texto, ruta_cap, ruta_mp3, tipo="diaria"):
    os.chdir(RAIZ)
    cap = json.load(open(ruta_cap, encoding="utf-8"))
    os.makedirs("audio", exist_ok=True)
    shutil.copyfile(ruta_mp3, f"audio/{fecha}.mp3")
    dias = json.load(open("dias.json", encoding="utf-8")) if os.path.exists("dias.json") else {}
    d = date.fromisoformat(fecha)
    dias[fecha] = {"fecha": fecha_texto, "corta": f"{DIAS[d.weekday()]} {d.day} {MESES[d.month - 1]}",
                   "audio": f"audio/{fecha}.mp3?v={int(datetime.now().timestamp())}", "duracion": cap["duracion"],
                   "capitulos": cap["capitulos"], "tipo": tipo, "bytes": os.path.getsize(f"audio/{fecha}.mp3")}
    for k in sorted(dias)[:-7]:                       # solo la última semana
        dias.pop(k)
        if os.path.exists(f"audio/{k}.mp3"): os.remove(f"audio/{k}.mp3")
    json.dump(dias, open("dias.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1)

    tpl = open("herramientas/plantilla.html", encoding="utf-8").read()
    open("index.html", "w", encoding="utf-8").write(
        tpl.replace("__DATOS__", json.dumps({"dias": dias}, ensure_ascii=False).replace("</", "<\\/")))

    items = []
    for k in sorted(dias, reverse=True):
        e = dias[k]; dd = date.fromisoformat(k)
        pub = format_datetime(datetime(dd.year, dd.month, dd.day, 8, 30, tzinfo=LIMA))
        titulos = "\n".join(f"{int(c['inicio'] // 60)}:{int(c['inicio'] % 60):02d} {c['titulo']}" for c in e["capitulos"])
        nombre = f"CAUDINOTICIAS – {e['fecha'].replace(' de 2026', '')}" + (" (edición dominical)" if e.get("tipo") == "dominical" else "")
        items.append(f"""  <item>
   <title>{escape(nombre)}</title>
   <description>{escape(titulos)}</description>
   <enclosure url="{BASE}audio/{k}.mp3" length="{e['bytes']}" type="audio/mpeg"/>
   <guid isPermaLink="false">caudinoticias-{k}</guid>
   <pubDate>{pub}</pubDate>
   <itunes:duration>{int(e['duracion'])}</itunes:duration>
   <itunes:explicit>false</itunes:explicit>
  </item>""")
    feed = f"""<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0" xmlns:itunes="http://www.itunes.com/dtds/podcast-1.0.dtd" xmlns:atom="http://www.w3.org/2005/Atom">
 <channel>
  <title>CAUDINOTICIAS en audio</title>
  <link>{BASE}</link>
  <atom:link href="{BASE}feed.xml" rel="self" type="application/rss+xml"/>
  <language>es-pe</language>
  <description>Boletín diario de noticias de fuentes abiertas: corrupción, seguridad y coyuntura nacional, para escuchar. SIMFA · Uso referencial.</description>
  <itunes:author>SIMFA – My. PNP Jorge Luis Jiménez Aguilar</itunes:author>
  <itunes:image href="{BASE}portada.jpg"/>
  <itunes:category text="News"><itunes:category text="Daily News"/></itunes:category>
  <itunes:explicit>false</itunes:explicit>
  <itunes:type>episodic</itunes:type>
{chr(10).join(items)}
 </channel>
</rss>
"""
    open("feed.xml", "w", encoding="utf-8").write(feed)
    print(f"Sitio actualizado: {len(dias)} ediciones; {BASE}#d{fecha}")


if __name__ == "__main__":
    main(*sys.argv[1:6])
