#!/usr/bin/env python3
"""Mueve issues por el tablero (GitHub Projects v2) de los proyectos de WIN.

Flujo que se gestiona: Backlog -> Análisis -> Desarrollo -> Code Review -> Aprobado,
más Blocked. Lo posterior a Aprobado (QA, Ready Release, Producción, Cerrado) no se toca.

Uso (desde la raíz del repositorio del issue):
  tablero.py ver ISSUE
  tablero.py sincronizar ISSUE
  tablero.py mover ISSUE ESTADO [--fecha AAAA-MM-DD] [--forzar]
  tablero.py alta ISSUE --padre N --inicio AAAA-MM-DD --fin AAAA-MM-DD [--tipo Task|Bug]

Salida 0 = hecho; 2 = transición no permitida (no se tocó nada); 1 = error.
"""
import argparse
import datetime
import json
import os
import re
import subprocess
import sys
import time

FLUJO = ["Backlog", "Análisis", "Desarrollo", "Code Review", "Aprobado"]
POSTERIORES = ["QA", "Ready Release", "Producción", "Cerrado"]
BLOQUEADO = "Blocked"
ACTIVOS = ["Análisis", "Desarrollo", "Code Review"]
ZONA = "America/Lima"

CONSULTA_ISSUE = """
query($o:String!,$r:String!,$n:Int!){repository(owner:$o,name:$r){issue(number:$n){
  id number title url assignees(first:10){nodes{login}} parent{number}
  subIssues(first:100){nodes{number}}
  projectItems(first:10){nodes{id project{id number title owner{... on Organization{login}
    ... on User{login}}
    fields(first:60){nodes{... on ProjectV2FieldCommon{id name dataType}
      ... on ProjectV2SingleSelectField{options{id name}}}}}
    fieldValues(first:60){nodes{
      ... on ProjectV2ItemFieldSingleSelectValue{name field{... on ProjectV2FieldCommon{name}}}
      ... on ProjectV2ItemFieldDateValue{date field{... on ProjectV2FieldCommon{name}}}}}}}}}}
"""


class NoPermitido(Exception):
	pass


def gh(*args, entrada=None):
	proceso = subprocess.run(["gh", *args], input=entrada, capture_output=True, text=True)
	if proceso.returncode != 0:
		mensaje = proceso.stderr.strip()
		if "read:project" in mensaje or "scopes" in mensaje:
			mensaje += "\nConcede el permiso con: ! gh auth refresh -h github.com -s project"
		raise RuntimeError("gh " + " ".join(args[:3]) + ": " + mensaje)
	return proceso.stdout


def hoy():
	os.environ["TZ"] = ZONA
	time.tzset()
	return datetime.date.today().isoformat()


def repositorio():
	salida = gh("repo", "view", "--json", "owner,name", "-q", '.owner.login + " " + .name')
	dueno, nombre = salida.split()
	return dueno, nombre


def leer_issue(numero):
	dueno, nombre = repositorio()
	salida = gh("api", "graphql", "-f", "query=" + CONSULTA_ISSUE,
		"-F", "o=" + dueno, "-F", "r=" + nombre, "-F", "n=" + str(numero))
	issue = json.loads(salida)["data"]["repository"]["issue"]
	if issue is None:
		raise RuntimeError("No existe el issue #%s en %s/%s" % (numero, dueno, nombre))
	return issue


def es_tablero_de_flujo(proyecto):
	campos = {c.get("name"): c for c in proyecto["fields"]["nodes"] if c}
	estado = campos.get("Status")
	if not estado or "Fecha Inicio Real" not in campos:
		return False
	opciones = {o["name"] for o in estado.get("options", [])}
	return set(FLUJO).issubset(opciones)


def elemento(issue, numero_tablero=None):
	"""Devuelve el ítem del issue en el tablero de flujo, o None si no está en ninguno."""
	candidatos = [i for i in issue["projectItems"]["nodes"] if es_tablero_de_flujo(i["project"])]
	if numero_tablero is not None:
		candidatos = [i for i in candidatos if i["project"]["number"] == numero_tablero]
	if len(candidatos) > 1:
		titulos = ", ".join("%d" % i["project"]["number"] for i in candidatos)
		raise RuntimeError("#%s está en varios tableros (%s); indica cuál" % (issue["number"], titulos))
	return candidatos[0] if candidatos else None


def valores(item):
	resultado = {}
	for nodo in item["fieldValues"]["nodes"]:
		if nodo and "field" in nodo:
			resultado[nodo["field"]["name"]] = nodo.get("name") or nodo.get("date")
	return resultado


def campo(item, nombre):
	for nodo in item["project"]["fields"]["nodes"]:
		if nodo and nodo.get("name") == nombre:
			return nodo
	raise RuntimeError("El tablero no tiene el campo «%s»" % nombre)


def escribir(item, nombre, valor):
	definicion = campo(item, nombre)
	argumentos = ["project", "item-edit", "--project-id", item["project"]["id"], "--id", item["id"],
		"--field-id", definicion["id"]]
	if "options" in definicion:
		opcion = [o["id"] for o in definicion["options"] if o["name"] == valor]
		if not opcion:
			raise RuntimeError("«%s» no es una opción de %s" % (valor, nombre))
		argumentos += ["--single-select-option-id", opcion[0]]
	else:
		argumentos += ["--date", valor]
	gh(*argumentos)


def posicion(estado):
	return FLUJO.index(estado) if estado in FLUJO else None


def estado_de(item):
	return valores(item).get("Status") or "Backlog"


def comprobar_transicion(actual, destino):
	if destino not in FLUJO and destino != BLOQUEADO:
		raise NoPermitido("«%s» queda fuera de este flujo (se gestiona hasta Aprobado)" % destino)
	if actual in POSTERIORES:
		raise NoPermitido("está en «%s», posterior a Aprobado: lo mueve QA o gestión" % actual)
	if actual == destino:
		raise NoPermitido("ya está en «%s»" % actual)
	if destino == BLOQUEADO:
		if actual not in ACTIVOS:
			raise NoPermitido("solo se bloquea desde Análisis, Desarrollo o Code Review")
		return
	if actual == BLOQUEADO:
		if destino not in ACTIVOS:
			raise NoPermitido("de Blocked se vuelve a Análisis, Desarrollo o Code Review")
		return
	salto = posicion(destino) - posicion(actual)
	if salto < 0:
		raise NoPermitido("retrocede de «%s» a «%s»" % (actual, destino))
	if salto > 1:
		intermedios = FLUJO[posicion(actual) + 1:posicion(destino)]
		raise NoPermitido("salta de «%s» a «%s» sin pasar por %s" % (
			actual, destino, ", ".join("«%s»" % e for e in intermedios)))


def fechas_del_paso(item, destino, fecha):
	"""Inicio Real al entrar al flujo activo; Fin Real al aprobar; Plan solo si está vacío."""
	actuales = valores(item)
	escritas = []
	pos = posicion(destino)
	if pos is not None and pos >= 1:
		for nombre in ("Fecha Inicio Real", "Fecha Inicio Plan"):
			if not actuales.get(nombre):
				escribir(item, nombre, actuales.get("Fecha Inicio Real") or fecha)
				escritas.append(nombre)
	if destino == "Aprobado":
		for nombre in ("Fecha Fin Real", "Fecha Fin Plan"):
			if not actuales.get(nombre):
				escribir(item, nombre, actuales.get("Fecha Fin Real") or fecha)
				escritas.append(nombre)
	return escritas


def mover_item(item, numero, destino, fecha, forzar):
	actual = estado_de(item)
	try:
		comprobar_transicion(actual, destino)
	except NoPermitido:
		if not forzar or actual == destino:
			raise
	escribir(item, "Status", destino)
	escritas = fechas_del_paso(item, destino, fecha)
	extra = (" · " + ", ".join(escritas) + " = " + fecha) if escritas else ""
	print("MOVIDO: #%s %s -> %s%s" % (numero, actual, destino, extra))


def objetivo_del_padre(estados_hijos):
	"""Análisis/Desarrollo con el primer hijo; Code Review/Aprobado cuando todos llegan."""
	def nivel(estado):
		if estado in POSTERIORES:
			return len(FLUJO)
		if estado == BLOQUEADO:
			return 1
		return posicion(estado)
	niveles = [nivel(e) for e in estados_hijos]
	if not niveles:
		return None
	minimo = min(niveles)
	if minimo >= 4:
		return "Aprobado"
	if minimo >= 3:
		return "Code Review"
	maximo = max(niveles)
	if maximo >= 2:
		return "Desarrollo"
	if maximo >= 1:
		return "Análisis"
	return None


def arrastrar_padre(issue, numero_tablero, fecha):
	if not issue.get("parent"):
		return
	padre = leer_issue(issue["parent"]["number"])
	item_padre = elemento(padre, numero_tablero)
	if item_padre is None:
		print("PADRE: #%s no está en el tablero; no se toca" % padre["number"])
		return
	estados = []
	for hijo in padre["subIssues"]["nodes"]:
		item_hijo = elemento(leer_issue(hijo["number"]), numero_tablero)
		if item_hijo is not None:
			estados.append(estado_de(item_hijo))
	actual = estado_de(item_padre)
	destino = objetivo_del_padre(estados)
	resumen = "PADRE: #%s «%s» está en %s; sus hijos piden %s" % (
		padre["number"], padre["title"], actual, destino or "nada")
	if destino is None or actual not in FLUJO or posicion(destino) <= posicion(actual):
		print(resumen + " -> sin cambio")
		return
	if posicion(destino) - posicion(actual) > 1:
		print(resumen + " -> DESALINEADO: el salto no se hace solo, pregunta al usuario")
		return
	mover_item(item_padre, padre["number"], destino, fecha, False)


def cmd_ver(args):
	issue = leer_issue(args.issue)
	item = elemento(issue, args.tablero)
	print("ISSUE: #%s %s" % (issue["number"], issue["title"]))
	print("PADRE: #%s" % issue["parent"]["number"] if issue.get("parent") else "PADRE: ninguno")
	print("ASIGNADOS: " + (", ".join(a["login"] for a in issue["assignees"]["nodes"]) or "nadie"))
	if item is None:
		print("TABLERO: ninguno con el flujo Backlog→Aprobado")
		return
	print("TABLERO: %s · %s" % (item["project"]["number"], item["project"]["title"]))
	actuales = valores(item)
	for nombre in ("Status", "Tipo", "Fecha Inicio Plan", "Fecha Fin Plan",
			"Fecha Inicio Real", "Fecha Fin Real"):
		print("%s: %s" % (nombre.upper(), actuales.get(nombre) or "—"))


def ramas_del_issue(numero):
	patron = re.compile(r"^(feature|fix|hotfix)/%s-" % numero)
	salida = gh("pr", "list", "--state", "all", "--limit", "300",
		"--json", "number,headRefName,baseRefName,state,mergedAt")
	return [p for p in json.loads(salida) if patron.match(p["headRefName"])]


def cmd_sincronizar(args):
	issue = leer_issue(args.issue)
	item = elemento(issue, args.tablero)
	actual = estado_de(item) if item else "(fuera del tablero)"
	prs = ramas_del_issue(args.issue)
	for pr in prs:
		print("PR: #%s %s %s -> %s%s" % (pr["number"], pr["state"], pr["headRefName"],
			pr["baseRefName"], " · fusionado " + pr["mergedAt"][:10] if pr["mergedAt"] else ""))
	destinos = re.compile(r"^(integration/|main$|master$)")
	fusionados = [p for p in prs if p["state"] == "MERGED" and destinos.match(p["baseRefName"])]
	abiertos = [p for p in prs if p["state"] == "OPEN"]
	if fusionados:
		evidencia = "Aprobado"
	elif abiertos:
		evidencia = "Code Review"
	else:
		remotas = gh("api", "repos/{owner}/{repo}/branches", "--paginate", "-q", ".[].name")
		propias = [r for r in remotas.split() if re.match(r"^(feature|fix|hotfix)/%s-" % args.issue, r)]
		evidencia = "Desarrollo" if propias else None
		for rama in propias:
			print("RAMA: " + rama)
	print("ESTADO: " + actual)
	print("EVIDENCIA: " + (evidencia or "ninguna (sin rama ni PR)"))
	if evidencia and actual in FLUJO and posicion(evidencia) > posicion(actual):
		pasos = FLUJO[posicion(actual) + 1:posicion(evidencia) + 1]
		print("PROPUESTA: " + " -> ".join(pasos))


def cmd_mover(args):
	issue = leer_issue(args.issue)
	item = elemento(issue, args.tablero)
	if item is None:
		raise RuntimeError("#%s no está en ningún tablero con este flujo; usa «alta»" % args.issue)
	fecha = args.fecha or hoy()
	try:
		mover_item(item, issue["number"], args.estado, fecha, args.forzar)
	except NoPermitido as motivo:
		print("NO PERMITIDO: #%s %s" % (args.issue, motivo))
		return 2
	arrastrar_padre(issue, item["project"]["number"], fecha)
	return 0


def cmd_alta(args):
	padre = leer_issue(args.padre)
	item_padre = elemento(padre, args.tablero)
	if item_padre is None:
		raise RuntimeError("El padre #%s no está en un tablero con este flujo" % args.padre)
	proyecto = item_padre["project"]
	issue = leer_issue(args.issue)
	if elemento(issue, proyecto["number"]) is None:
		gh("project", "item-add", str(proyecto["number"]), "--owner", proyecto["owner"]["login"],
			"--url", issue["url"])
	sub_id = gh("api", "repos/{owner}/{repo}/issues/%s" % args.issue, "-q", ".id").strip()
	gh("api", "-X", "POST", "repos/{owner}/{repo}/issues/%s/sub_issues" % args.padre,
		"-F", "sub_issue_id=" + sub_id, "-F", "replace_parent=true")
	gh("issue", "edit", str(args.issue), "--add-assignee", "@me")
	item = elemento(leer_issue(args.issue), proyecto["number"])
	escribir(item, "Tipo", args.tipo)
	escribir(item, "Fecha Inicio Plan", args.inicio)
	escribir(item, "Fecha Fin Plan", args.fin)
	if not valores(item).get("Status"):
		escribir(item, "Status", "Backlog")
	print("ALTA: #%s en tablero %s · padre #%s · %s · plan %s → %s · %s" % (
		args.issue, proyecto["number"], args.padre, args.tipo, args.inicio, args.fin,
		valores(item).get("Status") or "Backlog"))
	return 0


def main():
	parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
	parser.add_argument("--tablero", type=int, help="número del tablero si el issue está en varios")
	sub = parser.add_subparsers(dest="orden", required=True)
	ver = sub.add_parser("ver")
	ver.add_argument("issue", type=int)
	sincronizar = sub.add_parser("sincronizar")
	sincronizar.add_argument("issue", type=int)
	mover = sub.add_parser("mover")
	mover.add_argument("issue", type=int)
	mover.add_argument("estado")
	mover.add_argument("--fecha", help="AAAA-MM-DD; por defecto hoy en " + ZONA)
	mover.add_argument("--forzar", action="store_true", help="solo con la aprobación explícita del usuario")
	alta = sub.add_parser("alta")
	alta.add_argument("issue", type=int)
	alta.add_argument("--padre", type=int, required=True)
	alta.add_argument("--inicio", required=True)
	alta.add_argument("--fin", required=True)
	alta.add_argument("--tipo", default="Task", choices=["Task", "Bug"])
	args = parser.parse_args()
	for nombre in ("issue", "padre"):
		if getattr(args, nombre, None) is not None:
			setattr(args, nombre, int(str(getattr(args, nombre)).lstrip("#")))
	ordenes = {"ver": cmd_ver, "sincronizar": cmd_sincronizar, "mover": cmd_mover, "alta": cmd_alta}
	try:
		return ordenes[args.orden](args) or 0
	except RuntimeError as error:
		print("ERROR: %s" % error, file=sys.stderr)
		return 1


if __name__ == "__main__":
	sys.exit(main())
