---
name: commit
description: >
  Redacta y crea el commit de los cambios preparados (staged) con Conventional Commits
  1.0.0-beta.4: tipo(ámbito): descripción, cuerpo a 72 columnas y pie con Proyecto, Bloque,
  RF, Ticket y Refs al issue de GitHub. Autocontenido: todas las reglas están en el skill.
  Úsalo cuando el usuario diga "commitea", "haz el commit" o "genera el mensaje de commit",
  o invoque el skill commit. Acepta el número del issue (#899), códigos de RF/CA
  (RF02.CA04) y una pista del motivo.
---

# Commit con Conventional Commits por proyecto y RF

Todas las reglas del formato están en este archivo y en `scripts/validar.sh`; no dependas de
ningún documento del repositorio, que puede no existir o estar desactualizado en la rama.

`$DIR_SKILL` es la carpeta donde está este `SKILL.md` (en Claude Code, la *Base directory*
que se muestra al cargar el skill; suele ser `~/.claude/skills/commit`). Ejecuta todos los
comandos desde la raíz del repositorio. Sigue los pasos en orden y no te
saltes la validación.

## 1. Reúne el contexto

```bash
bash "$DIR_SKILL/scripts/contexto.sh" [NUMERO_DE_ISSUE]
git diff --cached
```

Pasa el número de issue si el usuario lo dio (`#899` → `899`); normalmente es una Task. Sin
él, el script usa el número con que empieza la rama (`849-rf-01-…` → `#849`). El script
recorre en GitHub la jerarquía Task → User Story → Feature → Épica e imprime `CADENA`.

- Si `PREPARADOS: ninguno` → **detente** y di: "No hay cambios preparados. Usa `git add` con
  los archivos que quieras incluir." **Nunca** ejecutes `git add`: el usuario decide qué entra.
- Si sale `AVISO: php/database.php` → **detente** y pregunta si de verdad quiere commitearlo.
- Si los archivos tienen cambios de dos motivos distintos → dilo y sugiere dos commits.
- Si `CADENA` no tiene nada que ver con los archivos (rama antigua cuyo número no es un
  issue de GitHub) → ignora `ISSUE`, `CADENA` y `RF_DE_ISSUE`.

## 2. Elige tipo y ámbito

**Tipo** (uno solo):

| El cambio… | Tipo |
|---|---|
| añade algo que no existía | `feat` |
| corrige algo que funcionaba mal | `fix` |
| hace lo mismo más rápido | `perf` |
| reordena código sin cambiar el comportamiento | `refactor` |
| solo documentación o colección Bruno | `docs` |
| solo formato (espacios, phpcbf) | `style` |
| Docker, Composer, npm, Makefile | `build` |
| `.github/` | `ci` |
| deshace otro commit | `revert` |
| nada de lo anterior | `chore` |

**Ámbito:** la columna de `PREPARADOS`. Si todos los archivos tienen el mismo, úsalo. Si hay
varios, usa el del archivo con más cambios. Si dice `(tipo build)`, `(tipo ci)` o `(tipo docs)`,
usa ese tipo y **no** pongas ámbito. Si dice `?`, usa el nombre de la carpeta principal del
archivo, en minúscula. Valen las carpetas de `php/apps/` (el nombre de la app) más `comun main
maps bd api lint deploy`; en un repositorio sin `php/apps/`, un sustantivo corto en minúscula.
Nunca uses como ámbito un portlet, un archivo, una clase, un RF ni un proyecto.

## 3. Redacta

```
tipo(ámbito): descripción

Cuerpo: por qué y cómo.

Proyecto: PRY-AAAA-NNNN
Bloque: N
RF: RF02.CA04, RF03
Ticket: NNNNN
Refs: #899
```

**Asunto** (≤ 72 caracteres):
- Español, minúscula inicial, sin punto final.
- Presente, 3.ª persona: "agrega", "corrige", "muestra", "valida". Nunca "agregar" ni "agregué".
- Dice el efecto que se ve desde fuera, no la tarea: "el popup cierra el aviso aunque la
  consulta falle", no "arreglo del popup".
- Prohibido: "ajustes", "cambios", "avance", "wip", "fixed", porcentajes.

**Cuerpo** (opcional; obligatorio en `fix`): 1-3 frases sobre **por qué** y qué hacía mal
antes. Corta cada línea a 72 columnas como máximo. Sin rutas locales.

**Pie** — solo los datos que tengas, uno por línea, en este orden:
- `Proyecto:` si `PROYECTO` no está vacío.
- `Bloque:` si `BLOQUE` no está vacío.
- `RF:` con el primero que exista: los códigos que dio el usuario, `RF_EN_DIFF`,
  `RF_DE_ISSUE`, `RF_DE_RAMA`. Formato `RF02.CA04, RF03`. **No inventes RF.** Si no hay,
  omite la línea.
- `Ticket:` si `TICKET` no está vacío.
- `Refs: #NNN` con el número de `ISSUE`, si existe. Solo `Refs`, nunca `Closes` ni `Fixes`:
  el cierre del issue se declara en la descripción del PR.
- `Origen: PRY-… RFnn` en vez de `Proyecto:` si `COMUN_BASE: si` (pregunta el proyecto si no
  lo sabes).
- Si el cambio rompe a quien usa el código: añade `!` antes de los dos puntos del asunto y
  termina el pie con `BREAKING CHANGE: <qué debe cambiar quien lo usa>`.

El `#` solo aparece en `Refs:`, delante de un número de issue. Nunca para RF ni tickets.

## 4. Valida

Escribe el mensaje en el archivo `$(git rev-parse --git-dir)/MENSAJE_COMMIT` y ejecuta:

```bash
bash "$DIR_SKILL/scripts/validar.sh" "$(git rev-parse --git-dir)/MENSAJE_COMMIT" "<PROYECTO>"
```

(el segundo argumento vacío si no hay proyecto). Si imprime `ERROR`, corrige el mensaje y vuelve
a validar hasta que imprima `OK`.

## 5. Crea el commit

```bash
git commit -F "$(git rev-parse --git-dir)/MENSAJE_COMMIT"
git log -1 --format='%h %s'
```

No uses `--no-verify`, `--amend` ni `git push`. Responde con el hash y el mensaje completo.

## Ejemplos

Rama `WINET-PRY-2026-0004-BLOQUE-3`, archivos en `php/apps/pext/`, argumento `RF02.CA09`:

```
fix(pext): el panel de edición conserva el cable al cambiar de capa

Al activar otra capa se recargaba el panel y se perdía la selección.
Ahora la selección vive en el estado del visor.

Proyecto: PRY-2026-0004
Bloque: 3
RF: RF02.CA09
```

Rama `164-winet-pry-2026-0003-descarga…`, archivos en `php/apps/pext/`, sin argumento y
`RF_EN_DIFF` vacío:

```
feat(pext): descarga el plano del proyecto en KMZ

Proyecto: PRY-2026-0003
```

Rama `849-rf-01-estructura-de-la-operación-edición-de-cables`, argumento `#899`, archivos en
`php/apps/pext/`; `CADENA` va de #899 a la épica #848, `PROYECTO: PRY-2026-0004`,
`BLOQUE: 3`, `RF_DE_ISSUE: RF01`:

```
feat(pext): muestra el panel de edición con los tramos del cable

Proyecto: PRY-2026-0004
Bloque: 3
RF: RF01
Refs: #899
```

Rama `Ticket-28022-FALLA-CON-EL-BUSCADOR`, archivos en `php/apps/win/`:

```
fix(win): el buscador de clientes acepta nombres con tilde

La búsqueda comparaba sin normalizar acentos y no encontraba a
clientes registrados con tilde.

Ticket: 28022
```

Rama `comun/base`, archivos en `php/comun/`, cambio rompedor:

```
refactor(comun)!: getPermisos devuelve una matriz por módulo

Origen: PRY-2026-0004 RF06
BREAKING CHANGE: quien use logpermisos.getPermisos debe leer
permisos[modulo][accion] en lugar de perfil.permisos.
```

Solo cambios en `Makefile`:

```
build: separa phpstan del objetivo lint
```
