---
name: cerrar-rf
description: >
  Puerta de calidad y cierre de un RF de WincoreH antes del MR a master. Ejecuta la batería
  completa —PHPCS, PHPStan, ESLint, smoke del bundle—, separa el ruido preexistente del error
  nuevo, aplica el checklist IC de 30 puntos sobre el diff, verifica la cabecera de auditoría y
  cierra la documentación del RF (estado en RF-NN.md e INDEX.md, SQL pendiente de ticket).
  Úsalo cuando el usuario diga "cierra el RF", "ya terminé", "revisa antes de commitear",
  "listo para MR", "pasa la inspección", "haz el IC", "está listo?" o pida revisar el trabajo
  de una rama de proyecto antes de entregarlo.
---

# Cerrar un RF — puerta de calidad y cierre documental

El repo **no tiene suite de tests**: PHPCS + PHPStan + ESLint son la única puerta automática, y
todo lo demás lo sostiene esta revisión. Nada de lo que sigue es opcional; lo que no se pueda
ejecutar se reporta como **pendiente explícito**, nunca como aprobado.

## 0. Delimitar el alcance

Todo se mide contra el **merge-base con master**, igual que `make lint` y `make deploy`:

```bash
BASE=$(git merge-base HEAD "$(git rev-parse --verify origin/master >/dev/null 2>&1 && echo origin/master || echo master)")
git diff --name-only "$BASE"          # el alcance real de la revisión
git diff "$BASE"                      # lo que hay que leer, no solo listar
```

Identifica **qué RF** se cierra (rama `WINET-PRY-2026-NNNN-RF-NN`) y abre su ficha en
`docs/99-workspace/rf/RF-NN.md`. Si el diff toca RF distintos del de la rama, dilo: es una señal
de que el MR mezcla alcances.

## 1. Puerta automática

```bash
make lint                             # phpcs + phpstan + eslint (los tres, en ese orden)
make lint-file FILE=php/ruta/x.php    # iterar sobre un archivo concreto
make lint-fix                         # SOLO estilo (phpcbf); nunca lo uses para "arreglar" lógica
```

**El objetivo no es cero errores: es no añadir errores nuevos.** El repo arrastra ruido conocido
que NO debe perseguirse ni reportarse como fallo del RF:

| Ruido esperado | Por qué |
|---|---|
| `Expected 1 blank line after function; 0 found` en el cierre de clase | Conflicto irresoluble entre PSR2 y `Squiz.WhiteSpace.FunctionSpacing`. Convención del repo: cerrar con `    }\n}` sin línea en blanco, como el resto de clases |
| PHPStan: `dbSelect`, `dbExecute`, `TOKEN_*`, `GOOGLE_MAPS_*` sin definir | Viven en `php/database.php`, excluido del análisis |
| Archivos sin analizar: `php/assets/*`, `php/functions.php`, `php/database.php`, `php/index.php`, `php/apps/win/class/partidas.php`, `main.php` | Excluidos en `phpcs.xml.dist` / `phpstan.neon`. **Si el diff los toca, revísalos a mano y dilo en el reporte** — ahí el lint no protege nada |

Contrasta siempre contra la base: si dudas de si un error es nuevo, corre el mismo comando sobre
`$BASE` y compara. Un error preexistente no bloquea; uno introducido por el RF, sí.

### 1.1 Contratos que el lint no ve

Tres invariantes de arquitectura que ninguna herramienta comprueba y que sí son greppables. Las
tres deben salir **vacías**:

```bash
# Separación de capas: solo class/ habla con la base de datos.
grep -rn "dbSelect\|dbExecute\|getDb()" php/apps/*/helpers/ php/apps/*/validaciones/

# El workspace no está versionado: nada versionado puede apuntar a él (§6).
# Se excluye .gitignore, que es justo donde la ruta debe aparecer.
git diff $BASE...HEAD -- . ':!.gitignore' | grep -nE "^\+.*99-workspace"

# La respuesta de un logic sale por RespuestaApi, no montada a mano ni por fin()/jsonout() (§1.2).
git diff $BASE...HEAD -- 'php/apps/*/logic/*.php' \
  | grep -nE "^\+.*(die|echo|print|return)\s*\(?\s*(json_encode|fin|jsonout)\("

# Todo dbSelect de un logic nuevo se comprueba antes de leer `data`: si no, un fallo de base
# de datos se le enseña al usuario como "sin resultados" (§1.2).
git diff $BASE...HEAD -- 'php/apps/*/logic/*.php' | grep -nE "^\+.*\['data'\] \?\?"
```

La primera es la que sostiene la estructura de `pext` (`helpers/` y `validaciones/` componen y
validan, `class/` consulta) y la dirección de dependencia `helpers/ → class/`, nunca al revés. Un
`dbSelect` en `helpers/` la rompe en silencio.

### 1.2 Un contrato que no se puede ejecutar no es un contrato

Toda regla que el front y el back deban compartir se **publica desde PHP** y se consume en JS; no
se escribe dos veces. El patrón del repo es un `perfilWeb()` estático cuyo array se antepone al
bundle en `window.<MODULO>_CONFIG` (`ControlcambiosValidador::perfilWeb()` →
`CC_CONFIG.validaciones`, `EstadoApi::perfilWeb()` → `CC_CONFIG.estados`).

Si en el diff ves un número, un límite o un código repetido a los dos lados, es un fallo de
contrato aunque el lint pase: uno de los dos se quedará atrás. En JS se admite un valor de
respaldo por si `CC_CONFIG` llegara incompleto, nunca como fuente.

**La salida de un método API también es contrato.** Un logic nuevo termina por
`RespuestaApi::emitir*()`, con los códigos de `EstadoApi`, y llama a
`RespuestaApi::abortarSiConsultaFallo($resultado)` después de cada consulta y antes de leer
`data`. Montar el `json_encode` a mano se salta el cuerpo estándar, la traza y el mapeo HTTP.
El estándar completo, en `docs/04-api/README.md`.

## 2. Smoke de runtime (si el RF toca un bundle Vue3-CDN)

PHPCS y PHPStan no ven un `ReferenceError` ni un orden de carga mal armado en el manifest. Si el
diff toca `php/apps/*/interface/*/`, ejecuta el smoke:

```bash
docker compose exec -T web php -r '
chdir("/var/www/html/php");
$s = require "apps/pext/interface/logcontrolcambios/manifest.php";
$b=""; foreach($s as $p){ $b .= file_get_contents($p)."\n"; }
file_put_contents("/tmp/bundle.js",$b);'
docker compose exec -T web cat /tmp/bundle.js > /tmp/bundle.js
node docs/99-workspace/smoke/smoke-bundle-controlcambios.js /tmp/bundle.js
```

Sale con 0 si pasa. Detalle en `docs/99-workspace/smoke/README.md`. Para un módulo nuevo, adapta
la ruta del `manifest.php` y deja el script correspondiente en `docs/99-workspace/smoke/`.

## 3. Método API nuevo — la comprobación que el código no delata

Si el RF añade un `log<nombre>.<accion>`, **verifica que existe su fila en `co_portlet_events`**
(`id_event` = `log<nombre>.<accion>`, `id_app` de la app). Sin ella el dispatcher responde
`-1 "metodo no encontrado"` aunque el PHP sea perfecto. El SQL debe estar en
`docs/99-workspace/sql/` y ser idempotente. Comprueba también que la lógica termina en
`die(fin(...))` / `die(jsonout(...))` y que valida sus inputs (punto 26 del IC).

## 4. Checklist IC — 30 puntos sobre el diff

Aplica el checklist IC completo (está en el `CLAUDE.md` global del usuario) leyendo el diff, no el
archivo entero. El lint ya cubre estilo e indentación; **concéntrate en lo que ningún linter ve**:

- **1, 2** — nada de credenciales, IPs ni nombres de BD fuera de `php/database.php`. En el front,
  la config va inyectada como `window.<MODULO>_CONFIG` desde PHP, nunca hardcodeada en el `.js`.
- **3, 27** — nombres que digan lo que contienen; ninguna variable reutilizada para dos cosas.
- **10, 11, 12** — una responsabilidad por función; PHP ≤100 líneas, JS 60-80; máx. 3-4 parámetros.
- **13, 30** — código comentado = error (`Squiz.PHP.CommentedOutCode`); revísalo también en los `.js`.
- **18, 28** — try/catch en toda operación asíncrona y en el acceso a BD; ningún catch vacío ni mudo.
- **22, 25** — todo `switch` con `default` y mínimo 2 `case`.
- **26** — validación de inputs en cada método API nuevo.
- **29** — cabecera de auditoría (ver §5).

Reporta en la tabla IC estándar con ✅ / ❌ / ⚠️ / N/A, resumen `N/30`, y separa **críticos** de
**recomendados**. Un punto solo es ✅ si lo comprobaste: no rellenes la tabla por inercia.

## 5. Cabecera de auditoría (punto 29)

Todo fragmento nuevo o modificado la lleva. En **PRY-2026-0004** el autor es **`Juan Kuga` solo**
(Diego Ordoñez salió del proyecto el 12/08/2026):

```php
/*
 * Juan Kuga - PRY-2026-0004-WINET - Bloque 2
 * Descripción: <qué hace y a qué RF/CA responde>
 */
```

O en línea: `// Juan Kuga - PRY-2026-0004-WINET - Bloque 2 - DD/MM/AAAA - <detalle>`

**No añadas a Diego a código nuevo y no lo borres de las cabeceras existentes**: son registro
histórico. Detalle en `/documentar`.

## 6. Cierre documental

No está cerrado hasta que la documentación lo refleja:

- `docs/99-workspace/rf/RF-NN.md` — `Estado` y `PR` al día; si la implementación se desvió del
  DFT, la desviación queda escrita en la ficha, no en la cabeza de nadie.
- `docs/99-workspace/rf/INDEX.md` — la fila del RF, con el mismo estado.
- El plan en `docs/99-workspace/planes/` — qué quedó fuera y por qué.
- **Los `.sql` de `docs/99-workspace/sql/` no están versionados**: recuerda adjuntarlos al ticket
  del pase a producción (`docs/03-development/pases-a-produccion.md`) o al repositorio de BD. Si no,
  no queda rastro de qué se ejecutó en la base.
- Si el RF ya está verificado y camino de `master`, ofrece promover un resumen a `docs/` con
  `/documentar`. No promuevas por iniciativa propia.

**El workspace se queda en tu máquina.** Ninguna ruta de `docs/99-workspace/` puede aparecer en el
**código, los comentarios de auditoría, los mensajes de commit ni la descripción del MR**: no está
versionado, así que para el revisor es una referencia rota. Compruébalo antes de commitear:

```bash
git diff --cached | grep -n "99-workspace"          # debe salir vacío
git log --format=%B origin/master..HEAD | grep -n "99-workspace"
```

Lo que el revisor necesite saber va **en el propio comentario o en el cuerpo del commit**, resumido;
si no cabe, se promueve a `docs/00-start-here` … `docs/05-database` y se cita esa ruta. Criterio
completo en `/estandar-codigo` §5.1.

## 7. Verificación funcional

El lint verde no dice que la pantalla funcione. Si no se probó en el navegador
(`http://localhost:${WEB_PORT}/`), dilo como **pendiente**, con la ruta exacta y el caso a probar.
Nunca lo des por hecho.

## 8. Reporte final

Cierra con esta forma, en este orden:

1. **Veredicto** — `Listo para MR` / `Bloqueado: <motivo en una línea>`.
2. **Puerta automática** — resultado de PHPCS / PHPStan / ESLint / smoke, distinguiendo errores
   nuevos del ruido preexistente.
3. **Tabla IC** — con el resumen `N/30`, críticos y recomendados.
4. **Pendientes** — verificación en navegador, SQL por adjuntar, decisiones del analista abiertas.

Con hallazgos: enúncialos y **espera decisión** antes de arreglar nada que no sea estilo. Si el
usuario pide arreglar, arregla y **vuelve a correr §1** — no reportes verde sobre una corrección
sin comprobar.
