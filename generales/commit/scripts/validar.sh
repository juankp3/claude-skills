#!/usr/bin/env bash
# Valida un mensaje de commit: Conventional Commits 1.0.0-beta.4 con pie
# de proyecto, bloque y RF. Las reglas viven aquí, sin depender de docs.
# Uso: validar.sh <archivo-con-el-mensaje> [PROYECTO_ESPERADO]
# Sale con 0 si es válido; si no, imprime cada error y sale con 1.
set -u

archivo=$1
proyecto=${2:-}
errores=0

falla() {
	echo "ERROR: $1"
	errores=$((errores + 1))
}

tipos='feat|fix|perf|refactor|docs|style|test|build|ci|chore|revert'
# Ámbitos: las apps que existan en la rama actual más los transversales.
# En un repositorio sin php/apps/ se acepta cualquier sustantivo en minúscula.
raiz=$(git rev-parse --show-toplevel 2>/dev/null || pwd)
if [ -d "$raiz/php/apps" ]; then
	apps=$(find "$raiz/php/apps" -mindepth 1 -maxdepth 1 -type d -exec basename {} \; | tr '\n' '|')
	ambitos="${apps}comun|main|maps|bd|api|lint|deploy"
else
	ambitos='[a-z][a-z0-9-]*'
fi

asunto=$(head -1 "$archivo")

if ! printf '%s' "$asunto" | grep -qE "^($tipos)(\(($ambitos)\))?!?: [^ ]"; then
	falla "asunto sin la forma tipo(ámbito): descripción, o tipo/ámbito fuera del catálogo: $asunto"
fi
if [ "${#asunto}" -gt 72 ]; then
	falla "asunto de ${#asunto} caracteres (máximo 72)"
fi
if printf '%s' "$asunto" | grep -qE '\.$'; then
	falla "el asunto termina en punto"
fi
if printf '%s' "$asunto" | grep -qE ': [A-ZÁÉÍÓÚÑ][a-záéíóúñ]'; then
	falla "la descripción empieza en mayúscula"
fi
# El # solo vale para issues de GitHub y solo en la línea Refs: del pie.
if grep -vE '^Refs: ' "$archivo" | grep -qE '#[0-9A-Za-z]'; then
	falla "# fuera de Refs:; los issues van en 'Refs: #899' y RF o tickets sin #"
fi
if grep -qE '^Refs: ' "$archivo" \
	&& ! grep -qE '^Refs: #[0-9]+(, #[0-9]+)*$' "$archivo"; then
	falla "la línea Refs: no sigue el formato 'Refs: #899, #900'"
fi
if grep -q '99-workspace' "$archivo"; then
	falla "cita docs/99-workspace, que no existe fuera de tu máquina"
fi
if [ "$(sed -n 2p "$archivo")" != "" ] && [ "$(wc -l < "$archivo")" -gt 1 ]; then
	falla "falta la línea en blanco después del asunto"
fi

largas=$(awk 'NR > 1 && length > 72 { print NR }' "$archivo" | tr '\n' ' ')
if [ -n "$largas" ]; then
	falla "líneas del cuerpo o pie de más de 72 columnas: $largas"
fi

if printf '%s' "$asunto" | grep -qE '^[a-z]+(\([a-z]+\))?!:' \
	&& ! grep -qE '^BREAKING CHANGE: ' "$archivo"; then
	falla "el asunto lleva ! pero falta BREAKING CHANGE: en el pie"
fi

if [ -n "$proyecto" ] && ! grep -qx "Proyecto: $proyecto" "$archivo"; then
	falla "falta la línea 'Proyecto: $proyecto' en el pie"
fi

# Un código: RF02 · RF02.CA04 · RF02-RN06 (forma del DFT) · RT02.CA03 · RT02-RN10.
# Un rango de criterios del mismo RF se abrevia con guion y solo los dígitos: RF02.CA02-06.
# Si la lista no cabe en 72 columnas, se repite la línea RF: en vez de partirla.
codigoRf='R[FT][0-9]{2}([.](CA|RN)[0-9]{2}(-[0-9]{2})?|-RN[0-9]{2}(-[0-9]{2})?)?'
if grep -qE '^RF:' "$archivo" \
	&& grep -E '^RF:' "$archivo" | grep -vqE "^RF: ${codigoRf}(, ${codigoRf})*$"; then
	falla "la línea RF: no sigue el formato 'RF: RF02.CA04, RF02-RN06, RT02.CA03, RF02.CA06-09'"
fi
if grep -qE '^ +R[FT][0-9]{2}' "$archivo"; then
	falla "códigos RF en una línea sangrada: repite 'RF:' en cada línea en vez de continuar la anterior"
fi

if [ "$errores" -eq 0 ]; then
	echo "OK"
	exit 0
fi
exit 1
