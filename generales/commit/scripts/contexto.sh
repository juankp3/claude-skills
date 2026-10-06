#!/usr/bin/env bash
# Reúne lo que el mensaje de commit necesita y que no hay que adivinar:
# rama, issue de GitHub y su jerarquía, proyecto, bloque, RF, ticket,
# archivos preparados con su ámbito y códigos RF/CA/RN del diff.
# Uso: contexto.sh [NUMERO_DE_ISSUE]   (con o sin #; por defecto, el de la rama)
set -u

dirSkill=$(cd "$(dirname "$0")/.." && pwd)
issueArg=${1:-}
issueArg=${issueArg#\#}

rama=$(git branch --show-current)
echo "RAMA: $rama"

# El nombre de rama varía (WINET-PRY-2026-0004-…, 164-winet-pry-2026-0003-…,
# WINET---PRY---2026---0020-…, 849-rf-01-…): se normaliza antes de buscar.
normal=$(printf '%s' "$rama" | tr '[:lower:]' '[:upper:]' | tr -s '_ -' '-')

proyecto=$(printf '%s' "$normal" | grep -oE 'PRY-[0-9]{4}-[0-9]{4}' | head -1)
origenProyecto=${proyecto:+rama}
bloque=$(printf '%s' "$normal" | grep -oE 'BLOQUE-[0-9]+' | head -1 | grep -oE '[0-9]+')
ticket=$(printf '%s' "$normal" | grep -oE '(TICKET|TK)-[0-9]+' | head -1 | grep -oE '[0-9]+')
rfRama=$(printf '%s' "$normal" | grep -oE '(^|[-/])RF-?[0-9]{2}([-/]|$)' | head -1 | grep -oE '[0-9]{2}')
issueRama=$(printf '%s' "$rama" | grep -oE '(^|/)[0-9]+-' | head -1 | tr -dc '0-9')
issue=${issueArg:-$issueRama}

# Jerarquía en GitHub: Task → User Story → Feature (RF-NN) → Epic.
rfIssue=""
epica=""
if [ -n "$issue" ]; then
	if command -v gh >/dev/null 2>&1 && gh auth status >/dev/null 2>&1; then
		echo "ISSUE: #$issue"
		echo "CADENA:"
		actual=$issue
		nivel=0
		while [ -n "$actual" ] && [ "$nivel" -lt 6 ]; do
			fila=$(gh api "repos/{owner}/{repo}/issues/$actual" \
				-q '[.number, (.labels | map(.name) | join(",")), .title] | @tsv' 2>/dev/null) || break
			numero=$(printf '%s' "$fila" | cut -f1)
			etiquetas=$(printf '%s' "$fila" | cut -f2)
			titulo=$(printf '%s' "$fila" | cut -f3-)
			echo "  #$numero [$etiquetas] $titulo"
			if [ -z "$rfIssue" ]; then
				rfIssue=$(printf '%s' "$titulo" | grep -oE 'RF-?[0-9]{2}' | head -1 | tr -d '-')
			fi
			epica=$numero
			actual=$(gh api "repos/{owner}/{repo}/issues/$actual/parent" -q '.number' 2>/dev/null) || actual=""
			nivel=$((nivel + 1))
		done

		# Proyecto desde el título del tablero (requiere el permiso read:project).
		if [ -z "$proyecto" ]; then
			repo=$(gh repo view --json owner,name -q '.owner.login + " " + .name' 2>/dev/null)
			tablero=$(gh api graphql \
				-f query='query($o:String!,$r:String!,$n:Int!){repository(owner:$o,name:$r){
					issue(number:$n){projectItems(first:10){nodes{project{title}}}}}}' \
				-F o="${repo%% *}" -F r="${repo##* }" -F n="$issue" \
				-q '.data.repository.issue.projectItems.nodes[].project.title' 2>/dev/null)
			proyecto=$(printf '%s' "$tablero" | tr '[:lower:]' '[:upper:]' | grep -oE 'PRY-[0-9]{4}-[0-9]{4}' | head -1)
			origenProyecto=${proyecto:+tablero}
		fi
	else
		echo "ISSUE: #$issue (GitHub no disponible: gh sin instalar o sin sesión)"
	fi
fi

# Respaldo local: proyectos.conf asocia cada épica con su proyecto y bloque.
conf="$dirSkill/proyectos.conf"
if [ -n "$epica" ] && [ -f "$conf" ]; then
	linea=$(grep -E "^$epica[[:space:]]" "$conf" | head -1)
	if [ -n "$linea" ]; then
		if [ -z "$proyecto" ]; then
			proyecto=$(printf '%s' "$linea" | awk '{ print $2 }')
			origenProyecto="proyectos.conf"
		fi
		if [ -z "$bloque" ]; then
			bloque=$(printf '%s' "$linea" | awk '{ print $3 }')
		fi
	fi
fi

[ -n "$epica" ] && echo "EPICA: #$epica"
echo "PROYECTO: ${proyecto:-}${origenProyecto:+ (de $origenProyecto)}"
echo "BLOQUE: ${bloque:-}"
echo "TICKET: ${ticket:-}"
echo "RF_DE_ISSUE: ${rfIssue:-}"
echo "RF_DE_RAMA: ${rfRama:+RF$rfRama}"
if [ "$rama" = "comun/base" ]; then
	echo "COMUN_BASE: si (el pie lleva Origen:, no Proyecto:)"
fi

archivos=$(git diff --cached --name-only)
if [ -z "$archivos" ]; then
	echo "PREPARADOS: ninguno"
	exit 0
fi

echo "PREPARADOS:"
printf '%s\n' "$archivos" | while IFS= read -r ruta; do
	case "$ruta" in
		php/apps/*) ambito=$(printf '%s' "$ruta" | cut -d/ -f3) ;;
		php/comun/*) ambito="comun" ;;
		js/googlemaps-loader.js) ambito="maps" ;;
		main.php | js/* | styles/*) ambito="main" ;;
		php/index.php | docs/04-api/*) ambito="api" ;;
		docs/05-database/* | *.sql) ambito="bd" ;;
		phpcs.xml.dist | phpstan.neon | eslint.config.js | .eslintrc.json) ambito="lint" ;;
		deploy-export.ignore | worktree.js) ambito="deploy" ;;
		Makefile | compose.yaml | docker/* | composer.* | package*.json) ambito="(tipo build)" ;;
		.github/*) ambito="(tipo ci)" ;;
		docs/*) ambito="(tipo docs)" ;;
		*) ambito="?" ;;
	esac
	echo "  $ambito	$ruta"
done

if printf '%s\n' "$archivos" | grep -qx 'php/database.php'; then
	echo "AVISO: php/database.php está preparado; es específico del entorno."
fi

echo "RF_EN_DIFF:"
git diff --cached -U0 | grep -E '^\+[^+]' \
	| grep -oE 'R[FT]-?[0-9]{2}([.-](CA|RN)[0-9]{2})?' | sed -E 's/^(R[FT])-/\1/' | sort -u | sed 's/^/  /'

echo "ESTADISTICAS:"
git diff --cached --stat | tail -1
