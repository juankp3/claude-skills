---
name: documentar
description: >
  Enruta toda la documentación del proyecto y fija la autoría de las cabeceras de auditoría.
  Úsalo SIEMPRE antes de crear o editar cualquier documento del proyecto: análisis, hallazgo,
  plan de implementación, nota de trabajo, requerimiento funcional, checklist, script SQL de
  apoyo o resumen. Se activa con "documenta esto", "apunta", "guarda esto", "crea un documento",
  "haz un plan", "toma nota", "deja constancia". También cubre el sentido inverso: promover,
  oficializar o versionar documentación ("pasa esto a docs", "ya está sólido", "oficialízalo",
  "que se versione"), que mueve un resumen de docs/99-workspace a docs/00-start-here …
  docs/05-database. Y define quién firma el código nuevo de PRY-2026-0004.
---

# Documentación de WincoreH — dónde va cada cosa

Dos tiempos: **se trabaja en `docs/99-workspace/`** (no versionado) y **se promueve un resumen a
`docs/`** (versionado) cuando algo ya es sólido. Nunca al revés.

## 1. Destino por defecto: `docs/99-workspace/`

Todo documento nuevo nace aquí. **No crees documentos directamente en `docs/00-start-here` …
`docs/05-database`** — la única excepción es una promoción explícita (§3).

| Carpeta | Contenido |
|---|---|
| `rf/` | Requerimientos funcionales del DFT, su `INDEX.md`, anexos normativos |
| `planes/` | Planes de implementación, previos a escribir código |
| `sql/` | Scripts de apoyo (permisos, catálogos) asociados a un RF |
| `notas/` | Análisis, hallazgos, preguntas abiertas al analista, notas de sesión |

Si el documento no encaja en ninguna, va a `notas/`. Crea carpeta nueva solo cuando el tipo se
repita, y entonces actualiza la tabla de `docs/99-workspace/README.md`.

Nombres en kebab-case, con prefijo del RF cuando aplique: `plan-rf16-homologacion-iconografia.md`,
`rf06-permisos-gestion-red.sql`.

## 2. Qué implica que el workspace no esté versionado

`docs/99-workspace/` está en `.gitignore:31`. Consecuencias reales, no teóricas:

- **No hay historial ni respaldo en git.** Un `git clean`, un worktree eliminado o un disco perdido
  se lo lleva entero.
- **No viaja en el MR** — nadie del equipo lo ve.
- **No entra en `make deploy`.**

De ahí tres reglas operativas:

- Lo que deba sobrevivir se **promueve** (§3).
- Los **scripts SQL** hay que adjuntarlos al ticket del pase a producción
  (`docs/03-development/pases-a-produccion.md`) o guardarlos en el repositorio de BD del equipo:
  si no, no queda rastro de qué se ejecutó en la base ni cuándo.
- **Nunca se cita `docs/99-workspace/` desde algo versionado** (§2.1).

### 2.1 Nada versionado apunta al workspace

Un comentario de código o un mensaje de commit que remita a `docs/99-workspace/…` es una
referencia rota para todo el que no seas tú: esa ruta no existe en el clon de nadie más, no viaja
en el MR y no entra en el ZIP del pase. El lector se queda sin la explicación y sin forma de
pedirla.

Aplica a **código, comentarios de auditoría, mensajes de commit, descripciones de MR** y a
`docs/00-start-here` … `docs/05-database`.

- Si el detalle importa para entender el código → **va en el propio comentario**, resumido.
- Si es demasiado largo para un comentario → se **promueve** (§3) y se cita el destino versionado.
- Si no merece ninguna de las dos → no se cita nada; se omite la referencia.

Referencias que sí valen desde código y commits: rutas de `docs/00-start-here` … `docs/05-database`,
códigos de RF y CA (`RF08.CA02`), el código de proyecto y el ticket.

## 3. Promoción a `docs/` versionado

**Cuándo.** Cuando se cumplen las tres: el RF está implementado y verificado, las decisiones ya no
cambian (sin preguntas abiertas bloqueantes), y el MR a `master` está hecho o es inminente.
Mientras el RF esté "en curso", no se promueve.

**Qué es.** Un **resumen reescrito y ordenado**, no un `mv` ni un copiar-pegar. El documento de
trabajo se queda en el workspace como registro; a `docs/` va lo que le sirve a alguien que llega
nuevo al repo dentro de seis meses.

**Dónde:**

| Origen en workspace | Destino versionado |
|---|---|
| RF, criterios de aceptación, reglas de negocio | `docs/01-product/` |
| Decisiones de arquitectura, flujo de petición | `docs/02-architecture/` |
| Plan de implementación, convenciones, guía del módulo | `docs/03-development/proyectos/<pry-…>/` |
| Métodos API nuevos (fila en `co_portlet_events`) | `docs/04-api/` |
| Tablas, DDL, permisos, diagramas | `docs/05-database/proyectos/<pry-…>/` |

**Plantilla: PRY-2026-0001.** Ya está promovido y enseña la forma exacta que debe tener un proyecto
en `docs/` — copia su estructura en vez de inventar una:

- `docs/03-development/proyectos/pry-2026-0001-planta-interna/` → `README.md`, `validaciones.md`,
  `pendientes-qa.md`
- `docs/05-database/proyectos/pry-2026-0001-planta-interna/` → `README.md`, `schema.dbml`,
  `catalogo-tablas-diagrama.md`

**Una promoción no está terminada hasta que se actualizan los índices:** la fila en
`docs/03-development/proyectos/README.md` y/o `docs/05-database/proyectos/README.md`, y el enlace
en `docs/README.md`. Los documentos promovidos llevan navegación entre sí, como los de
PRY-2026-0001.

**Qué no se promueve nunca:** el DFT crudo, notas de sesión, preguntas al analista sin resolver,
planes cuyas desviaciones ya están absorbidas por el código.

## 4. Autoría del código

Las cabeceras de auditoría (punto 29 del checklist IC) de **código nuevo de PRY-2026-0004** llevan
**`Juan Kuga` como único autor**. Diego Ordoñez salió del proyecto el 12/08/2026.

```php
/*
 * Juan Kuga - PRY-2026-0004-WINET - Bloque 2
 * Descripción: <qué hace y a qué RF/CA responde>
 */
```

O en línea: `// Juan Kuga - PRY-2026-0004-WINET - Bloque 2 - DD/MM/AAAA - <detalle>`

- **No añadas `Diego Ordoñez`** a código nuevo de este proyecto.
- **No lo quites de las cabeceras existentes.** Son registro histórico de quién estaba en el
  proyecto cuando se escribieron, y las de **PRY-2026-0001** corresponden a trabajo suyo real:
  borrarlas falsearía la autoría.

## 5. Al terminar

Di siempre **en qué carpeta quedó el documento y si está versionado o no**. Que la decisión sea
visible en el momento, no dos días después cuando toque moverlo.
