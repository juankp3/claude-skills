---
name: tablero-github
description: >
  Mantiene el estado de los issues en el tablero de GitHub Projects de los proyectos de WIN
  (Status, Tipo, fechas Plan y Real, issue padre) con el flujo Backlog → Análisis → Desarrollo →
  Code Review → Aprobado, sin saltos ni retrocesos, y arrastra al RF padre. Úsalo cuando el
  usuario diga "actualiza el tablero", "pasa #NNN a desarrollo / code review / aprobado",
  "mueve el issue", "ponle las fechas en el Project", "da de alta el issue en el Project",
  "cuélgalo del RF", "sincroniza el tablero", y SIEMPRE en los puntos de enganche: al empezar
  el análisis de un issue o RF, al escribir su primer código, al abrir su PR a la rama de
  integración y al ver ese PR fusionado.
---

# Tablero de GitHub — estados, fechas y padre

`$DIR_SKILL` es la carpeta de este `SKILL.md` (suele ser `~/.claude/skills/tablero-github`).
Todo pasa por `scripts/tablero.py`, ejecutado **desde la raíz del repositorio del issue**. El
script valida las transiciones; no edites el tablero a mano con `gh project item-edit`, que se
salta las reglas.

```bash
python3 $DIR_SKILL/scripts/tablero.py ver 1170            # estado, tipo, fechas, padre
python3 $DIR_SKILL/scripts/tablero.py sincronizar 1170    # qué dicen la rama y el PR
python3 $DIR_SKILL/scripts/tablero.py mover 1170 "Code Review"
python3 $DIR_SKILL/scripts/tablero.py alta 1170 --padre 850 --inicio 2026-10-19 --fin 2026-10-21
```

Requiere el permiso `project` en `gh`. Si falta, pide al usuario
`! gh auth refresh -h github.com -s project` y espera.

## 1. El flujo

| Estado | Cuándo se entra | Quién lo dispara |
|---|---|---|
| Backlog | Al crear el issue | `alta` |
| Análisis | Se empieza a estudiar: leer la spec, reproducir el fallo, planificar | `/spec-rf preparar` o `plan`; en un fix, al empezar a investigar |
| Desarrollo | Se escribe la primera línea de código del issue | `/spec-rf fase`; en un fix, la primera edición. `/commit` comprueba que ya esté aquí |
| Code Review | Se abre el PR de `feature/` o `fix/` hacia la rama de integración | Después de `gh pr create` |
| Aprobado | Ese PR está fusionado en la rama de integración | `sincronizar` lo detecta |

Reglas que el script hace cumplir (sale con código 2 y no toca nada):

- **Nunca se salta un estado.** De Backlog solo se pasa a Análisis, de Análisis a Desarrollo, y
  así sucesivamente. Si la realidad ya va por delante (p. ej. el PR se fusionó con el issue aún en
  Backlog), **no saltes ni recorras los pasos por tu cuenta**: muestra la salida de `sincronizar`,
  explica el salto y pregunta. Solo con un sí explícito usa `--forzar`; dejar en el historial
  pasos con fecha de hoy que no ocurrieron es peor que un salto visible.
- **Nunca se retrocede.** Si hay que volver atrás, lo decide el usuario.
- **Blocked** se usa desde Análisis, Desarrollo o Code Review. Al desbloquear, pregunta a cuál
  de los tres vuelve.
- **El skill llega hasta Aprobado.** QA, Ready Release, Producción y Cerrado los mueven QA o
  gestión; el script no entra ni sale de ellos.

## 2. Fechas

| Campo | Se escribe | Valor |
|---|---|---|
| Fecha Inicio Real | Al salir de Backlog, si está vacía | Hoy (America/Lima) o `--fecha` |
| Fecha Fin Real | Al pasar a Aprobado, si está vacía | Día del merge: pásalo con `--fecha` (lo da `sincronizar`) |
| Fecha Inicio / Fin Plan | Solo si están vacías, con la Real correspondiente | — |

Una fecha ya escrita no se sobrescribe. Para corregirla, pide confirmación y usa
`gh project item-edit` solo para ese campo.

## 3. El issue padre (RF)

Tras cada `mover`, el script recalcula el padre directo (el RF, no la épica):

- pasa a **Análisis** o **Desarrollo** en cuanto un hijo lo alcanza;
- pasa a **Code Review** o **Aprobado** solo cuando **todos** sus hijos del tablero lo han
  alcanzado. Un hijo posterior a Aprobado cuenta como aprobado y uno Blocked, como en Análisis;
- **nunca retrocede**, y si alcanzarlo exigiera un salto imprime `DESALINEADO`: pregunta.

Informa siempre la línea `PADRE:` al usuario.

## 4. Alta de un issue de trabajo

Al crear un issue (un fix, una tarea suelta), antes de empezarlo:

1. Decide el RF padre por la regla o el CA que cita (`RT02.CA03` → RF-02). Si dudas entre dos,
   pregunta. Nunca lo cuelgues de la épica.
2. Pide al usuario las fechas **Plan** de inicio y fin; no las inventes.
3. `alta ISSUE --padre N --inicio … --fin …` con `--tipo Bug` si es un defecto reportado por QA y
   `Task` en otro caso. Esto añade el issue al tablero del padre, lo cuelga del padre, te lo
   asigna, fija Tipo y fechas Plan, y lo deja en Backlog.

## 5. Puntos de enganche

Los demás skills llaman a este en estos momentos; si trabajas sin ellos, aplícalo igual:

| Momento | Acción |
|---|---|
| `/spec-rf preparar` o `plan`, o empiezas a investigar un fix | `mover N Análisis` |
| Primera edición de código del issue (`/spec-rf fase`, o la primera de un fix) | `mover N Desarrollo` |
| `/commit` con el issue todavía en Backlog o Análisis | Avisa y propone moverlo antes de commitear |
| Abres el PR hacia `integration/…` | `mover N "Code Review"` |
| Ves el PR fusionado (o el usuario lo dice) | `sincronizar N` y luego `mover N Aprobado --fecha <día del merge>` |

## 6. Reporte

Cierra con una línea por issue movido (`#N Estado → Estado · fechas escritas`), la línea
`PADRE:` del script y cualquier `NO PERMITIDO` o `DESALINEADO` pendiente de decisión.
