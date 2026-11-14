# -*- coding: utf-8 -*-
"""CAUDINOTICIAS en audio: arma la página de escucha a partir de una edición (diaria o dominical).

Uso: python3 herramientas/guion.py ediciones/AAAA-MM-DD.validada.json --json pistas.json
Solo se leen las noticias (y, al final, el dólar y los cortes): nada de encabezados, pies de página ni enlaces.
"""
import json, re, sys, html

SECS = [("corrupcion", "Corrupción de funcionarios"), ("criminalidad", "Criminalidad y operativos policiales"),
        ("interior", "Sector Interior e institucional"), ("carrera", "Carrera policial y bienestar"),
        ("normativa", "Normativa con incidencia policial"), ("orden_interno", "Orden interno y coyuntura política"),
        ("internacional", "Internacional"), ("clima", "Clima")]

SIGLAS = {"PNP": "pe ene pe", "UIF": "u i efe", "BCRP": "be ce erre pe", "COEN": "coen", "SBS": "ese be ese",
          "JNE": "jota ene e", "ONPE": "onpe", "EFICCOP": "eficcop", "DIRCOCOR": "dircocor", "TID": "te i de",
          "ENFEN": "enfen", "PCM": "pe ce eme", "MTC": "eme te ce", "ATU": "a te u", "INPE": "inpe", "SUCAMEC": "sucamec",
          "DIRINCRI": "dirincri", "DEPINCRI": "depincri", "DIVINCRI": "divincri", "EE. UU.": "Estados Unidos", "EE.UU.": "Estados Unidos", "FF. AA.": "Fuerzas Armadas", "FF.AA.": "Fuerzas Armadas", "FF.AA": "Fuerzas Armadas", "FF. OO.": "Fuerzas del Orden", "FF.OO.": "Fuerzas del Orden", "MP": "Ministerio Público", "PJ": "Poder Judicial"}
ABREV = [(r"\bN\.\s?°\s?", "número "), (r"\bAv\.\s?", "avenida "), (r"\bav\.\s?", "avenida "), (r"\bJr\.\s?", "jirón "),
         (r"\bA\.\s?H\.\s?", "asentamiento humano "), (r"\bC\.\s?P\.\s?", "centro poblado "), (r"\bUrb\.\s?", "urbanización "),
         (r"\bAsoc\.\s?", "asociación "), (r"\bcdras?\.\s?", "cuadras "), (r"\bMz\.\s?", "manzana "), (r"\bkm\b", "kilómetros"),
         (r"\bS\.\s?A\.\s?C\.", "S A C"), (r"\bart\.\s?", "artículo "), (r"\bp\.\s?ej\.", "por ejemplo"), (r"\bmm\b", "milímetros")]


def hora_es(h, m=0):
    """13:30 -> «1 y 30 de la tarde»."""
    h, m = int(h), int(m)
    parte = "de la mañana" if h < 12 else "del mediodía" if h == 12 and m == 0 else "de la tarde" if h < 19 else "de la noche"
    h12 = h if h <= 12 else h - 12
    return f"{h12}{'' if m == 0 else f' y {m:02d}' if m >= 10 else f' y {m}'} {parte}"


MESES_N = ["enero", "febrero", "marzo", "abril", "mayo", "junio", "julio", "agosto", "septiembre", "octubre", "noviembre", "diciembre"]


def numeros_es(t):
    """Escribe en palabras (español) todas las cifras: la voz no lee bien los dígitos."""
    from num2words import num2words as n2w
    w = lambda n: n2w(int(n), lang="es")
    # fechas 06/11/2026 y 6/11
    t = re.sub(r"\b(\d{1,2})/(\d{1,2})/(\d{4})\b",
               lambda m: f"{int(m.group(1))} de {MESES_N[int(m.group(2)) - 1]} de {m.group(3)}" if 1 <= int(m.group(2)) <= 12 else m.group(0), t)
    t = re.sub(r"\b(\d{1,2})/(\d{1,2})\b",
               lambda m: f"{int(m.group(1))} de {MESES_N[int(m.group(2)) - 1]}" if 1 <= int(m.group(2)) <= 12 else m.group(0), t)
    t = re.sub(r"\b(\d{1,3}(?:\.\d{3})+)\b", lambda m: m.group(1).replace(".", ""), t)      # 18.300 -> 18300
    t = re.sub(r"(\d)\s?°\s?C\b", r"\1 grados", t)                                           # 36 °C
    t = re.sub(r"\b(\d+)\.?\s?[°º]\s?(?=[a-záéíóúñ])",                                      # 82.° aniversario
               lambda m: n2w(int(m.group(1)), lang="es", to="ordinal") + " ", t)
    t = re.sub(r"\b(\d{1,2}):(\d{2})\b", lambda m: f"{m.group(1)} y {m.group(2)}" if m.group(2) != "00" else m.group(1), t)
    t = re.sub(r"(\d)\s?%", r"\1 por ciento", t)
    t = re.sub(r"(\d)\.(\d)", r"\1 coma \2", t)                                              # 3.5 -> 3 coma 5
    # «coma» con decimales: 3 coma 425 -> tres coma cuatrocientos veinticinco
    t = re.sub(r"\b(\d+)(?=\s*(?:[^\W\d_]|$))", lambda m: w(m.group(1)), t)
    t = re.sub(r"\b(\d+)\b", lambda m: w(m.group(1)), t)
    # «uno» delante de un sustantivo: «veintiuno muertos» -> «veintiún muertos», «uno herido» -> «un herido»
    t = re.sub(r"\b(\w*)uno(?= (?!(?:del|que|los|las|por|para|con|sus|más|menos|solo|sola|año)\b)[a-záéíóúñ]{3,})",
               lambda m: (m.group(1) + "ún") if m.group(1) else "un", t)
    return t


def hablar(t):
    """Texto preparado para la voz: sin marcas, con siglas, abreviaturas, monedas y horas legibles."""
    t = html.unescape(re.sub(r"<[^>]+>", " ", str(t)))
    t = t.replace("«", "").replace("»", "").replace("“", "").replace("”", "").replace('"', "")
    t = re.sub(r"(\d)\s(\d{3})\b", r"\1\2", t)                                   # 20 000 -> 20000
    t = re.sub(r"\bS/\s?(\d+)\.(\d{2,3})\b", r"\1 coma \2 soles", t)             # S/ 3.425
    t = re.sub(r"\bS/\s?([\d.,]+)", lambda m: m.group(1).replace(".", "") + " soles", t)
    t = re.sub(r"\bUS\$\s?([\d.,]+)", lambda m: m.group(1).replace(".", "") + " dólares", t)
    t = re.sub(r"\b(\d{1,2}):(\d{2})\s?h\b", lambda m: hora_es(m.group(1), m.group(2)), t)
    t = re.sub(r"(\d),(\d)", r"\1 coma \2", t)
    for a, b in ABREV:
        t = re.sub(a, b, t)
    for s, v in sorted(SIGLAS.items(), key=lambda x: -len(x[0])):
        t = re.sub(r"(?<![\wÁÉÍÓÚÑ])" + re.escape(s) + r"(?![\wÁÉÍÓÚÑ])", v, t)
    t = numeros_es(t)
    t = re.sub(r"\s+", " ", t).strip()
    return t


def limpio(t):
    return re.sub(r"\s+", " ", html.unescape(re.sub(r"<[^>]+>", " ", str(t)))).strip()


def guion(ed):
    dom = ed.get("tipo_edicion") == "dominical" or "hechos" in ed
    pistas = []
    intro = (f"CAUDINOTICIAS, {'edición dominical, ' if dom else ''}{re.sub(r' de \d{4}$', '', ed['fecha_texto']).lower()}. "
             "La actualidad en síntesis, en fuentes abiertas.")
    if ed.get("patron"):
        intro += f" {'La semana en una línea' if dom else 'El patrón del día'}: {limpio(ed['patron'])}"
    pistas.append({"sec": "Inicio", "titulo": "Presentación", "voz": hablar(intro)})
    if dom:
        grupos = [("Lo último del fin de semana", ed.get("fichas", []))]
    else:
        grupos = [(tit, [f for f in ed["fichas"] if f["seccion"] == k]) for k, tit in SECS]
    for tit, fichas in grupos:
        for i, f in enumerate(fichas):
            entrada = f"{tit}. " if i == 0 else ""
            pistas.append({"sec": tit, "titulo": limpio(f["titular"]),
                           "voz": hablar(f"{entrada}{f['titular']}. {f['cuerpo']}")})
    if dom and ed.get("hechos"):
        txt = "Lo más saltante de la semana. " + " ".join(f"{h['titulo']}. {h['resumen']}" for h in ed["hechos"])
        pistas.append({"sec": "La semana", "titulo": "Lo más saltante de la semana", "voz": hablar(txt)})
    d = ed.get("dolar")
    if d and d.get("cierre"):
        dv = round((float(d["cierre"]) - float(d["cierre_anterior"])) * 1000) / 10
        var = "sin variación" if abs(dv) < 0.05 else f"{'bajó' if dv < 0 else 'subió'} {abs(dv):g} céntimos".replace(".", " coma ")
        txt = (f"El dólar. Cierre del {d['fecha_cierre'].split()[0]}: S/ {float(d['cierre']):.3f}; {var} frente al {d['fecha_anterior'].split()[0]}.")
        if d.get("sunat"):
            txt += f" Tipo de cambio Sunat para hoy: compra S/ {float(d['sunat']['compra']):.3f}, venta S/ {float(d['sunat']['venta']):.3f}."
        if d.get("nota_dia"):
            txt += " " + d["nota_dia"][0].upper() + d["nota_dia"][1:]
        pistas.append({"sec": "Indicadores", "titulo": "El dólar", "voz": hablar(txt)})
    c = ed.get("cortes")
    if c and (c.get("luz") or c.get("agua")):
        partes = []
        for tipo, nom in (("luz", "luz"), ("agua", "agua")):
            filas = sorted(c.get(tipo) or [], key=lambda r: [int(x) for x in r["inicio"].split(":")])
            if filas:
                partes.append(f"Corte de {nom}: " + "; ".join(f"{r['distrito']}, de {hora_es(*r['inicio'].split(':'))} a {hora_es(*r['fin'].split(':'))}" for r in filas) + ".")
        txt = "Cortes programados de hoy. " + " ".join(partes) + " Los sectores afectados están en el boletín en PDF."
        pistas.append({"sec": "Servicios", "titulo": "Cortes programados de luz y agua", "voz": hablar(txt)})
    pistas.append({"sec": "Cierre", "titulo": "Despedida",
                   "voz": hablar("Eso es todo por hoy en CAUDINOTICIAS. Los enlaces a cada fuente están en el boletín en PDF. "
                                 "CAUDINOTICIAS es un producto del Sistema de Monitoreo de Fuentes Abiertas, SIMFA, "
                                 "desarrollado por el Mayor PNP Jorge Luis Jiménez Aguilar, con asistencia de inteligencia artificial. "
                                 "Buen servicio.")})
    return pistas


def main(ruta, plantilla, salida):
    ed = json.load(open(ruta, encoding="utf-8"))
    pistas = guion(ed)
    datos = {"fecha": ed["fecha_texto"], "dominical": ed.get("tipo_edicion") == "dominical", "pistas": pistas}
    tpl = open(plantilla, encoding="utf-8").read()
    out = tpl.replace("__DATOS__", json.dumps(datos, ensure_ascii=False).replace("</", "<\\/"))
    open(salida, "w", encoding="utf-8").write(out)
    palabras = sum(len(p["voz"].split()) for p in pistas)
    print(f"{salida}: {len(pistas)} pistas, {palabras} palabras (~{round(palabras / 150)} min)")


if __name__ == "__main__":
    if sys.argv[2] == "--json":
        ed = json.load(open(sys.argv[1], encoding="utf-8"))
        pistas = guion(ed)
        json.dump(pistas, open(sys.argv[3], "w", encoding="utf-8"), ensure_ascii=False)
        print(f"{len(pistas)} pistas, {sum(len(p['voz'].split()) for p in pistas)} palabras")
    else:
        main(*sys.argv[1:4])
