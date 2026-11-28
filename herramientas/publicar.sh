#!/bin/bash
# Publica el sitio en GitHub Pages con un solo commit (sin historial), para que el repositorio no crezca con los audios.
# Uso (desde la raíz del repositorio): bash herramientas/publicar.sh AAAA-MM-DD
set -e
git config user.name "SIMFA CAUDINOTICIAS"
git config user.email "caudinoticias@users.noreply.github.com"
git checkout -q --orphan nuevo
git add -A
git commit -q -m "CAUDINOTICIAS en audio – edición $1"
git branch -D main -q 2>/dev/null || true
git branch -m main
git push -q -f origin main
echo "Publicado: https://pendexslayer29-droid.github.io/caudinoticias-audio/#d$1"
