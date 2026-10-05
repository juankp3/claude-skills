#!/usr/bin/env bash
# Enlaza los skills de este repo donde Claude Code los busca.
#
#   ./instalar.sh                      generales/*  → ~/.claude/skills/
#   ./instalar.sh <coleccion> <ruta>   <coleccion>/* → <ruta>/.claude/skills/
#                                      (p. ej. ./instalar.sh wincoreh ~/…/worktrees/mi-rama)
#
# Si el destino ya tiene una carpeta real con el mismo nombre, se compara: si es idéntica se
# sustituye por el enlace; si difiere, se mueve a <destino>/../skills-respaldo/ y se avisa, para
# que no se pierda nada. Volver a ejecutarlo es seguro.
set -euo pipefail

repo=$(cd "$(dirname "$0")" && pwd)
fecha=$(date +%Y%m%d-%H%M%S)

enlazar() {
	local origen=$1 destino=$2
	local nombre respaldo
	nombre=$(basename "$origen")
	respaldo="$(dirname "$destino")/skills-respaldo"

	if [ -L "$destino/$nombre" ]; then
		ln -sfn "$origen" "$destino/$nombre"
		echo "  = $nombre"
		return
	fi

	if [ -e "$destino/$nombre" ]; then
		if diff -rq -x .DS_Store "$origen" "$destino/$nombre" >/dev/null 2>&1; then
			rm -rf "${destino:?}/$nombre"
		else
			mkdir -p "$respaldo"
			mv "$destino/$nombre" "$respaldo/$nombre-$fecha"
			echo "  ! $nombre difería: copia previa en $respaldo/$nombre-$fecha"
		fi
	fi

	ln -s "$origen" "$destino/$nombre"
	echo "  + $nombre"
}

# Un skill de generales/ no puede repetirse dentro del proyecto: dos skills con el mismo nombre
# compiten. Se aparta la copia del proyecto.
apartarDuplicados() {
	local destino=$1
	local skill nombre
	for skill in "$repo"/generales/*/; do
		nombre=$(basename "$skill")
		if [ -e "$destino/$nombre" ] && [ ! -L "$destino/$nombre" ]; then
			mkdir -p "$(dirname "$destino")/skills-respaldo"
			mv "$destino/$nombre" "$(dirname "$destino")/skills-respaldo/$nombre-$fecha"
			echo "  - $nombre del proyecto apartado (ya lo da generales/)"
		fi
	done
}

if [ $# -eq 0 ]; then
	destino="$HOME/.claude/skills"
	mkdir -p "$destino"
	echo "generales → $destino"
	for skill in "$repo"/generales/*/; do
		enlazar "${skill%/}" "$destino"
	done
	exit 0
fi

if [ $# -ne 2 ]; then
	echo "Uso: $0                      (generales en ~/.claude/skills)" >&2
	echo "     $0 <coleccion> <ruta>   (p. ej. wincoreh ~/ruta/al/proyecto)" >&2
	exit 1
fi

coleccion=$1
proyecto=$(cd "$2" && pwd)
if [ ! -d "$repo/$coleccion" ]; then
	echo "No existe la colección '$coleccion' en $repo" >&2
	exit 1
fi

destino="$proyecto/.claude/skills"
mkdir -p "$destino"
echo "$coleccion → $destino"
apartarDuplicados "$destino"
for skill in "$repo/$coleccion"/*/; do
	enlazar "${skill%/}" "$destino"
done

# Cursor y Codex leen .agents/skills/: si el proyecto ya lo usa, se enlazan ahí los generales
# para que todos los agentes lean la misma copia.
if [ -d "$proyecto/.agents/skills" ]; then
	echo "generales → $proyecto/.agents/skills"
	for skill in "$repo"/generales/*/; do
		enlazar "${skill%/}" "$proyecto/.agents/skills"
	done
fi
