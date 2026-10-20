---
name: spec-rf
description: >
  Flujo spec-driven de un RF de WincoreH entre la transcripción del DFT y el cierre: ciclo de
  vida con puertas (Transcrito → Analizado → Listo → En curso → Implementado → Verificado →
  Cerrado), registro único de preguntas y decisiones (DECISIONES.md), matriz de trazabilidad con
  evidencia, puerta de fase, smoke por RF y protocolo de cambio de spec. Subcomandos: `preparar`
  (comprueba la Definition of Ready), `plan`, `fase`, `verificar`, `revision`, `preguntas` y
  `estado`. Úsalo cuando el usuario diga "prepara el RF", "¿está listo para empezar?", "planifica
  el RF", "empieza la fase", "terminé la fase", "verifica el RF", "llegó una nueva versión del
  DFT", "qué le pregunto a la analista", "paquete de preguntas", "en qué estado está el bloque" o
  "spec-driven". La puerta final antes del MR sigue siendo /cerrar-rf.
---

# Spec-driven development de un RF

La **spec** es el DFT transcrito en `docs/99-workspace/rf/RF-NN.md`. El código se escribe para
cumplirla, se verifica contra ella y, cuando el código se aparta, la desviación vuelve a la spec
como decisión registrada, no queda en la cabeza de nadie.

Cuatro reglas sostienen todo lo demás:

1. **Una cosa, un sitio.** El estado de un CA vive en la columna *Estado* de su tabla en
   `RF-NN.md`. Las preguntas y decisiones viven en `rf/DECISIONES.md`. El resultado de las
   pruebas vive en `smoke/RF-NN.md`. Los demás documentos **remiten**, no copian.
2. **✅ significa verificado, no escrito.** Sin evidencia (punto 4) el máximo es 🔵.
3. **Ningún supuesto silencioso.** Si el código decide algo que la spec no dice o contradice, hay
   una fila en `DECISIONES.md` con el supuesto que aplica el código.
4. **El incremento es la fase del plan.** Cada fase termina en su puerta (§5) y en su commit.

Rutas relativas a `docs/99-workspace/` salvo que se diga otra cosa. Recuerda: ese árbol no está
versionado en el repo del proyecto (tiene su propio git local) y **nada versionado lo cita**
(`/documentar` §2.1).

## 1. Ciclo de vida y puertas

La etapa de cada RF va en la columna *Etapa* de `rf/INDEX.md`. Solo se avanza cuando se cumple
la puerta; si se avanza sin cumplirla, se escribe por qué en la misma celda.

| Etapa | Qué hay | Puerta para pasar a la siguiente |
|---|---|---|
| **Transcrito** | `RF-NN.md` literal del DFT | Revisión del DFT y anexos citados son los vigentes (si no: fila en DECISIONES) |
| **Analizado** | `notas/rfNN-analisis-preparacion.md` contrastado con el código; preguntas en DECISIONES | Toda pregunta tiene supuesto y marca *bloquea* sí/no |
| **Listo** (DoR) | Plan con fases, trazabilidad CA → tarea y verificación por CA | `preparar` sin bloqueantes (§3) |
| **En curso · F*n*** | Código de la fase *n* | Puerta de fase (§5) |
| **Implementado** | Todas las fases dentro del alcance commiteadas | Todos los CA del alcance en 🔵 o mejor |
| **Verificado** | `smoke/RF-NN.md` ejecutado | Todos los CA del alcance en ✅, ➖ o con ⛔/🟡 justificado |
| **Cerrado** | MR abierto | `/cerrar-rf` en verde |

Un RF puede estar *Implementado* con una fase fuera de alcance (p. ej. RF-02 sin la reserva): la
celda lo dice — `Implementado (F1–F3) · F4 ⛔ P2-05`.

## 2. Estados de un CA, RN o RT

| Estado | Significa | Requisito |
|---|---|---|
| ✅ | Verificado | Evidencia en la matriz: paso de `smoke/RF-NN.md` con fecha, o petición Bruno con `tests` ejecutada |
| 🔵 | Implementado, sin verificar | Commit hecho (o diff listo), lint y `make test` en verde. Las pruebas fuera de la aplicación (unitarias de `tests/`, transacción revertida, arnés) se anotan como evidencia previa, pero no dan ✅ |
| 🟡 | Parcial | Se dice qué parte falta y de quién depende (otro RF, una decisión) |
| 🕐 | Pendiente | — |
| ⛔ | Bloqueado | Remite a la fila de DECISIONES que lo bloquea |
| ➖ | Sin código | Regla de proceso o de alcance; se dice por qué |

**Reapertura.** Un CA en ✅ o 🔵 vuelve a 🟡 cuando: cambia su texto en una revisión del DFT
(§7), llega una respuesta que contradice el supuesto que aplicó el código (§4), o una fase
posterior toca su código sin repetir su paso de smoke.

## 3. `preparar RF-NN` — Definition of Ready

Lee `RF-NN.md`, su análisis, su plan, `DECISIONES.md` y `INDEX.md`, y responde con una tabla
`Comprobación · Estado · Qué falta`:

1. **Spec vigente** — la revisión transcrita es la última recibida; los anexos que cita el RF son
   los vigentes. Un anexo pendiente de recibir solo bloquea si el RF usa el caso que cambió.
2. **Análisis contra el código** — existe y es posterior al último cambio de la spec.
3. **Preguntas** — todas en DECISIONES con supuesto. Las que tienen `Bloquea: sí` y siguen
   abiertas **bloquean**; el resto se acepta con el supuesto y lo dice.
4. **Dependencias** — los RF de los que depende están al menos en *Implementado*. Si están en 🔵
   sin verificar, avisa: se construye sobre algo sin probar (no bloquea, pero va al riesgo).
5. **Plan** — tiene fases, cada una entregable sola; tabla de trazabilidad con **todos** los CA,
   RN y RT del RF (o su motivo de exclusión); verificación con al menos un paso por CA; y en cada
   fase, la tarea `Tn.P` con las reglas que llevarán prueba unitaria (`/pruebas-unitarias` §1), o
   «ninguna» con su motivo.
6. **Modelo de datos y endpoints** — objetos de BD nuevos con `/estandar-bd`; métodos nuevos con su
   fila de `co_portlet_events` prevista.

Veredicto: `Listo` o `No listo: <lo mínimo que falta>`. Si está listo, actualiza la *Etapa* en
INDEX. Si no, no empieces a escribir código: propón resolver lo que falta.

Si el issue del RF sigue en Backlog en el tablero de GitHub, pásalo a **Análisis** con
`/tablero-github` (también al empezar `plan`).

## 4. `rf/DECISIONES.md` — registro único

Plantilla en `plantillas/decisiones.md`. Una fila por pregunta o decisión, con estas columnas:

| Columna | Contenido |
|---|---|
| ID | Se conservan los existentes: `P-NN` (RF-01), `PN-NN` (preguntas del RF N), `DN-NN` (decisiones técnicas del RF N), `R-NN` (reserva) |
| Para | `analista` · `arquitecto` · `interna` |
| Afecta | CA/RN/RT concretos |
| Pregunta | Una frase |
| Supuesto aplicado | **Lo que hace el código hoy**, no lo que se propuso en su día. Si el código cambió, se corrige aquí |
| Bloquea | `sí` / `no` |
| Estado | 🟠 abierta · 📤 enviada DD/MM (a quién) · ✅ respondida DD/MM · 🔒 asumida DD/MM (decisión interna aceptada) · ❌ descartada |
| Respuesta / si cambia | La respuesta literal, o qué habría que tocar si la respuesta difiere del supuesto |

Al registrar una **respuesta**:

- Si coincide con el supuesto → estado ✅ y nada más.
- Si difiere → estado ✅, los CA de *Afecta* pasan a 🟡 en `RF-NN.md`, y se añade la tarea al
  plan. Nunca se cambia el código sin pasar por aquí.

Los documentos de análisis y los planes pueden seguir explicando una pregunta en detalle, pero su
estado y su supuesto vigente están **solo** aquí.

## 5. `fase RF-NN Fn` — implementar una fase y cerrar su puerta

Antes de escribir: confirma que el RF está *Listo* o *En curso*, que la rama se llama
`feature/<issue>-rf-NN-<descripcion>` (minúsculas, sin acentos, guiones; `/cerrar-rf` §0 — el
pipeline rechaza el PR si no) y carga `/estandar-codigo` y `/pruebas-unitarias`. Si la fase
añade o cambia un método API, `/endpoint-bruno`; si toca BD, `/estandar-bd` y `/paquete-bd`.
En la primera fase, pasa el issue a **Desarrollo** con `/tablero-github` antes de escribir.

Al terminar la fase, **puerta de fase**, en este orden:

1. `make lint` (o `make lint-file`) y ESLint sobre lo tocado: sin errores nuevos.
2. **Pruebas unitarias** de las reglas críticas de la fase (`/pruebas-unitarias` §5): escritas,
   comprobado que fallan al romper la regla, y `make test` en verde — todo, no solo lo nuevo: una
   prueba de un RF anterior en rojo es una regresión de esta fase.
3. Los pasos de `smoke/RF-NN.md` de esa fase. Si no se pueden ejecutar en la aplicación, se
   anota la evidencia previa (pruebas unitarias, transacción revertida) y el CA queda en 🔵.
4. Estados en `RF-NN.md`: los CA de la fase a 🔵 o ✅; matriz con *Dónde* y *Evidencia*.
5. Supuestos nuevos aparecidos al implementar → filas en DECISIONES.
6. **Commit de la fase** con `/commit`, citando en `RF:` los CA de la fase (no el RF entero). Las
   pruebas unitarias de la fase van en ese mismo commit; una fase con cambios ajenos (tooling,
   docs generales) va en commits separados.
7. *Etapa* en INDEX: `En curso · F(n+1)` o `Implementado`.

No se empieza la fase siguiente con la anterior sin commitear.

## 6. `verificar RF-NN` — smoke y evidencia

`smoke/RF-NN.md` (plantilla `plantillas/smoke.md`) se genera desde la sección de verificación del
plan: una fila por paso con su CA, y una columna por ejecución (`DD/MM`). Cada paso se marca ✅ ❌
o ⏭ (no ejecutado, con motivo).

- Un CA pasa a ✅ cuando **todos** sus pasos están en ✅ en la misma ejecución, o su petición
  Bruno con `tests` pasa. En la columna *Evidencia* de la matriz: `smoke #12 07/10` o
  `bruno guardarRecorridoCable-rechazo-huella 07/10`.
- Un paso ❌ abre una tarea y deja el CA en 🟡; no se corrige "por encima" sin repetir el paso.
- Los pasos de regresión de RF anteriores se repiten en cada ejecución.

## 7. `revision` — llegó una nueva versión del DFT o de un anexo

1. Transcribe la revisión nueva conservando la anterior en el git del workspace (commit antes y
   después, para que el diff sea la revisión).
2. Lista los CA/RN/RT cuyo **texto** cambió, los nuevos y los retirados.
3. Los que cambiaron y estaban en ✅/🔵 → 🟡 con nota «texto cambiado en la revisión DD/MM».
4. Contrasta con DECISIONES: ¿la revisión responde alguna pregunta? Regístrala (§4).
5. Resume en la sección «Qué trae la revisión» de INDEX y actualiza la cabecera de los RF.

## 8. `preguntas` — paquete para la analista y el arquitecto

Genera `notas/paquete-preguntas-AAAAMMDD.md`: un documento **corto**, que la analista pueda
responder de una sentada. No es un volcado de DECISIONES.

**Qué entra: lo que importa, no todo lo 🟠.** Una pregunta va al paquete solo si cumple al menos
una de estas condiciones:

- bloquea algo (una fase, o dar un CA por ✅);
- el DFT se contradice (CA frente a RT, DFT frente a mockup) en algo que el usuario ve o que se
  guarda;
- una respuesta distinta del supuesto obligaría a rehacer código o datos.

Lo demás —supuestos de bajo impacto, o que siguen al DFT o al mockup— no se pregunta: pasa a
`🔒 asumida DD/MM` en DECISIONES con la nota «fuera del paquete; se valida en la demo». Se
reabre si la analista objeta. Objetivo orientativo: **unas 10 preguntas en total**; si salen más
de 12, vuelve a filtrar.

**Agrupar.** Si una sola respuesta resuelve varios CA, RN o RT (o varias filas de DECISIONES),
van en **una** pregunta que los cita a todos. Una pregunta, una duda: nada de listas de
subpreguntas.

**Formato de cada pregunta** (sin intro larga, sin rutas del repo, sin jerga de código; los
nombres de tabla o columna solo si el propio DFT los usa):

```markdown
### N. <título corto> · **bloquea <qué>**     ← la marca solo si bloquea

> **RF02.CA14** — «<texto del DFT tal cual; si es largo, solo el fragmento que importa, con […]>»
>
> **RT02.CA14** — «<otro texto citado, si la misma pregunta lo resuelve>»

**Pregunta:** <una o dos frases: qué no cuadra y qué hay que decidir>

*Mientras tanto:* <lo que el código aplica hoy, en una frase>
```

Orden: primero **Para la analista** y después **Para el arquitecto**; dentro de cada parte, las
que bloquean primero y luego por RF. Numeración continua en todo el documento. Cabecera de dos
líneas: proyecto, revisión del DFT, fecha y autor, y que «OK» basta si están de acuerdo con el
supuesto.

**En DECISIONES**, cada fila que cubre el paquete lleva en *Respuesta / si cambia* «Paquete
DD/MM, pregunta N». El paquete nuevo sustituye al anterior sin enviar (se borra; queda en el git
del workspace). Cuando el usuario confirme que lo envió, marca esas filas 📤 con fecha y
destinatario.

## 9. `estado` — foto del bloque

Tabla por RF desde INDEX y las tablas de cada RF: etapa, CA por estado (✅ 🔵 🟡 🕐 ⛔ ➖),
preguntas abiertas que lo bloquean y siguiente paso. Úsala también para detectar incoherencias:
un RF *Verificado* con CA en 🔵, un CA ⛔ sin fila en DECISIONES, un plan que cita un estado.

## 10. Dónde va cada cosa

| Qué | Dónde | Plantilla |
|---|---|---|
| Spec (DFT transcrito) | `rf/RF-NN.md` | — |
| Etapa del RF | columna *Etapa* de `rf/INDEX.md` | — |
| Estado de cada CA/RN/RT | columna *Estado* de sus tablas en `RF-NN.md` | — |
| Cómo se cumple, dónde, evidencia | sección *Trazabilidad e implementación* de `RF-NN.md` | `plantillas/matriz.md` |
| Preguntas y decisiones | `rf/DECISIONES.md` | `plantillas/decisiones.md` |
| Análisis contra el código | `notas/rfNN-analisis-preparacion.md` — **foto fechada**, no se mantiene | — |
| Plan: fases, CA → tarea, verificación | `planes/plan-rfNN-….md` — **sin estados** | `plantillas/plan.md` |
| Resultado de las pruebas | `smoke/RF-NN.md` | `plantillas/smoke.md` |
| Paquete de preguntas | `notas/paquete-preguntas-AAAAMMDD.md` | — |

Un análisis o un plan que necesite decir "esto ya está hecho" lo dice con un aviso arriba
(«Foto al DD/MM; estado vigente en RF-NN.md») en lugar de mantener una tabla de estados propia.

## 11. Relación con los demás skills

- `/documentar` — enruta documentos y la promoción a `docs/`. Este skill dice **qué** documentos
  tiene un RF y en qué etapa; aquel, dónde vive cada uno y cuándo se promueve.
- `/estandar-codigo`, `/endpoint-bruno`, `/estandar-bd`, `/paquete-bd` — durante la fase.
- `/pruebas-unitarias` — qué reglas de la fase llevan prueba y cómo; también `retro RF-NN` para
  un RF que se implementó sin ellas.
- `/commit` — al cerrar cada fase (§5.6).
- `/tablero-github` — estado del issue en el Project: Análisis en `preparar`/`plan`, Desarrollo
  en la primera `fase`; Code Review y Aprobado los marca el PR (`/cerrar-rf` §8).
- `/cerrar-rf` — puerta final: exige el RF en *Verificado* o los pendientes explícitos.
