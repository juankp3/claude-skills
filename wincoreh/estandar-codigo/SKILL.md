---
name: estandar-codigo
description: >
  Aplica y **corrige** el estándar de código de WincoreH, derivado de `phpcs.xml.dist`,
  `phpstan.neon`, `eslint.config.js` y el checklist IC de `docs/03-development/inspeccion.md`.
  No se limita a reportar: arregla la indentación, el formato, los nombres y los defectos que
  encuentra, y vuelve a pasar las herramientas hasta dejar solo el ruido tolerado. Úsalo ANTES de
  escribir o modificar cualquier `.php` o `.js` del repo, y sobre un archivo concreto para
  dejarlo conforme. Se activa al crear un archivo nuevo, al tocar una clase o un portlet, y
  cuando el usuario diga "que pase el lint", "respeta el estándar", "arregla la indentación",
  "corrige el archivo", "sigue las reglas de inspección" o "sin errores de phpcs". Es la cara
  preventiva de [cerrar-rf], que es la puerta de salida: este skill evita y repara el error,
  aquel lo detecta en la rama entera.
---

# Estándar de código de WincoreH

El objetivo no es llegar a cero errores de lint —el repo arrastra miles de preexistentes— sino
**dejar impecable el archivo que tocas, sin agregar ni un error nuevo**. Todo lo de abajo sale de
la configuración real, verificada con archivos de violaciones deliberadas el 13/08/2026 y
reverificada el 09/09/2026 tras el commit `8677112e` (dos conflictos de `phpcs.xml.dist` que antes
eran irresolubles se corrigieron: ver §0 y §3).

## 0. Modo de trabajo: corregir, no reportar

Cuando te invoquen sobre un archivo o un módulo, **el entregable es el archivo arreglado**, no una
lista de hallazgos. El ciclo es siempre el mismo:

```bash
# PHP — un archivo. Auto-fix de estilo con phpcbf (directo, no `make lint-fix`: ver aviso 🛑),
# el resto se corrige editando.
make lint-file FILE=<ruta>      # 1. detectar
docker compose run --rm web ./vendor/bin/phpcbf --standard=phpcs.xml.dist -d memory_limit=512M <ruta>  # 2. auto-fix de estilo
#                                 3. corregir a mano lo que quede (nombres, límites, §4)
make lint-file FILE=<ruta>      # 4. re-verificar

# JavaScript — un módulo. Aquí el auto-fix sí funciona.
npx eslint <ruta>
npx eslint <ruta> --fix
npx eslint <ruta>
```

1. **Detecta** con las herramientas y lee el archivo entero.
2. **Corrige.** En JS, `eslint --fix` resuelve indentación, espaciado y comillas; comprobado. En
   PHP, `phpcbf` invocado directo (no vía `make lint-fix`) resuelve indentación, espaciado entre
   métodos y el cierre de clase — comprobado el 09/09/2026.
3. **Corrige a mano** todo lo demás — §4 lista qué y cómo.
4. **Re-verifica** hasta que solo quede el ruido tolerado de §6.
5. **Reporta lo que cambiaste**, en dos o tres líneas. Si no había nada que arreglar, dilo y ya.

> ✅ **`phpcbf` ya corrige archivos con clase.** Hasta el 08/09/2026 había un conflicto irresoluble
> entre `Squiz.WhiteSpace.FunctionSpacing` y PSR2 en el cierre de clase: el fixer **oscilaba**, se
> rendía con `FAILED TO FIX` y **descartaba también los arreglos que sí había hecho**. Se resolvió
> fijando `spacingAfterLast="0"` en `phpcs.xml.dist` (commit `8677112e`, 09/09/2026) — el sniff ya
> no exige una línea en blanco antes de la llave de cierre de la clase. Verificado el 09/09/2026:
> un archivo con dos métodos y una propiedad privada corrige de punta a punta (3 arreglos fijados,
> 0 pendientes propios; el único caso que queda sin corregir automático es un nombre de propiedad
> fuera de convención, que nunca fue cosa de phpcbf).
>
> Sigue habiendo edición a mano para lo que ningún sniff detecta (§6) y para lo que phpcbf no
> arregla solo (nombres, extracción de funciones, etc.), pero **ya no evites `phpcbf` por miedo a
> que rompa el archivo** — el problema real que queda es de alcance, no de convergencia (ver el
> aviso 🛑 siguiente).

> 🛑 **`make lint-fix FILE=x` no se limita a `x`.** En el target `phpcbf` del Makefile, el `exit $?`
> vive dentro de un subshell `( … )`, así que solo sale del subshell: la ejecución **continúa** a la
> rama que corrige **todos** los `.php` del diff contra la rama base (`origin/main`/`main`, con
> fallback a `origin/master`/`master`). Comprobado el 13/08/2026, sigue vigente el 09/09/2026:
> invocarlo sobre un archivo de `pext` reescribió tres `manifest.php` de `pint` (normalizó sus
> finales de línea CRLF), archivos ajenos al trabajo en curso.
>
> Si aun así lo lanzas, **revisa `git status` inmediatamente** y revierte lo que no sea tuyo con
> `git checkout -- <archivo>`.
>
> **Para corregir un solo archivo sin ese alcance**, salta el target y llama a phpcbf directo
> (ahora que §"phpcbf ya corrige archivos con clase" aplica, esto es seguro):
> `docker compose run --rm web ./vendor/bin/phpcbf --standard=phpcs.xml.dist -d memory_limit=512M <ruta>`.

**Corriges sin preguntar:** indentación, espaciado, saltos de línea, líneas de más de 120,
código comentado, `empty()`, sintaxis 8.x, `var`, `==`, variables y parámetros sin usar, `switch`
sin `default`, `catch` vacío, cabecera de auditoría ausente, nombres de variables y de métodos
privados.

**Preguntas antes de:** renombrar una clase o un método público con llamadores fuera del módulo
(búscalos primero con `grep -rn`), extraer funciones para cumplir el límite de líneas, cambiar la
semántica de una consulta SQL, y tocar cualquier archivo de la lista de excluidos de §1.

## 1. Antes de tocar: ¿el archivo está analizado?

Excluidos de PHPCS y PHPStan — un error ahí no lo detecta nadie:

```
php/assets/*   ·   vendor/*   ·   php/functions.php   ·   php/database.php
php/index.php  ·   php/apps/win/class/partidas.php    ·   main.php
```

En JavaScript, ESLint solo analiza lo listado en `MODULOS_ANALIZADOS` (`eslint.config.js`).

En esos archivos **aplica igualmente todo lo de abajo, a mano**, y avisa de que el cambio va sin
red.

## 2. Indentación — la regla exacta

**PHP: TABS para indentar, ESPACIOS solo para alinear.**

- Un tab por nivel de bloque. Nunca espacios al principio de una línea de código.
- Los espacios solo aparecen **después** de los tabs, para alinear algo verticalmente: columnas de
  un `SELECT` dentro de un string multilínea, un `=>` de array, un `AS` de SQL.
- Detectar el error real: `grep -n "^ " archivo.php` — cualquier línea que **empiece** por espacio.
  También `grep -n " $"` para espacios al final.

> ⚠️ **Falso positivo del editor.** VS Code y PhpStorm marcan como "mixed indentation" un bloque
> SQL indentado con tabs y alineado con espacios. **Es la forma correcta en este repo** y por eso
> `phpcs.xml.dist` desactiva `Squiz.WhiteSpace.SuperfluousWhitespace` y los tres sniffs de
> *FunctionCallSignature*, que calculan la indentación multilínea en columnas. Antes de "arreglar"
> un bloque así, comprueba la composición real:
>
> ```bash
> awk 'NR>=A && NR<=B { gsub(/\t/,"[TAB]"); print NR": "$0 }' archivo.php
> ```
>
> Si todas las líneas llevan **los mismos tabs** y difieren solo en espacios de alineación, está
> bien: no lo toques. Convertir esos espacios a tabs rompe la alineación con otro `tab_width`.

**JavaScript: 2 espacios, nunca tabs.** `eslint --fix` lo corrige solo, incluida la indentación.

## 3. Reglas por lenguaje

### PHP 7.4

**Formato**

- Máximo **120 caracteres** por línea.
- **Llaves (PSR2):** clases y métodos abren en la **línea siguiente**; `if`, `foreach`, `while`,
  `try` abren en la **misma línea**.
- **Una línea en blanco entre métodos**, ni más ni menos (`FunctionSpacing`, spacing=1). Dos son un
  error, así que el punto 16 del IC —"funciones no relacionadas: 2 líneas"— **no aplica en PHP**.
- **Espacios alrededor de operadores** (`Squiz.WhiteSpace.OperatorSpacing`).
- **Cierre de archivo:** terminar con `\t}\n}`, **sin** línea en blanco antes del `}` de clase.
  Desde el 09/09/2026 `phpcs.xml.dist` fija `FunctionSpacing.spacingAfterLast="0"`: un archivo PHP
  correcto **no tiene ya ningún error de espaciado en el cierre** (antes del commit `8677112e` se
  toleraba uno, `Expected 1 blank line after function; 0 found`; si lo ves ahora, es un error real).

**Nombres**

| Elemento | Convención | Sniff |
|---|---|---|
| Clase | `PascalCase`, sin namespace, con prefijo de módulo (`ControlcambiosTerminal`) | `Squiz.Classes.ValidClassName` |
| Método | `camelCase` estricto — nada de `get_user()` ni `GetUser()` | `Generic.NamingConventions.CamelCapsFunctionName` (strict) |
| Variable | `camelCase` — nada de `$data_params` | `Squiz.NamingConventions.ValidVariableName` |
| Constante | `MAYUSCULAS_CON_GUION_BAJO`, y en este repo **sin** visibilidad explícita (`const X = …`), como el resto de clases | `Generic.NamingConventions.UpperCaseConstantName` |

> Propiedad privada **sin** guion bajo (`$contador`, no `$_contador`). Desde el commit `8677112e`
> (09/09/2026) `phpcs.xml.dist` excluye `Squiz.NamingConventions.ValidVariableName.PrivateNoUnderscore`
> —esa regla exige el guion bajo, la convención Squiz clásica— porque contradice
> `PSR2.Classes.PropertyDeclaration.Underscore`, que exige lo contrario y es la base declarada del
> proyecto. Antes del fix, cualquier propiedad privada disparaba un ERROR con una regla y un
> WARNING con la otra sin forma de pasar ambas; ahora gana PSR2 y **la propiedad privada camelCase
> sin guion bajo es la forma correcta**, sin ruido.

**Sintaxis: 7.4, nada de 8.x**

- Permitido: `??`, `<=>`, tipos de parámetro y retorno, propiedades tipadas.
- **Prohibido:** `?->`, argumentos nombrados, `match`, `enum`, union types, promoción de
  constructor, `readonly`.
- `declare(strict_types=1)` justo después de `<?php` en archivos nuevos. Ojo: con tipos estrictos,
  un método `f(string $x)` revienta si el llamador pasa un `int` — comprueba el llamador.
- Visibilidad explícita en métodos y propiedades.
- **`empty()` está prohibido** por strict-rules: `count($x) === 0`, `$x === ''` o `$x === null`.
- **Código comentado = error** (`Squiz.PHP.CommentedOutCode`). Bórralo, no lo dejes "por si acaso".

**PHPStan solo caza el punto 19 (variable no definida) y el 21 (código inalcanzable).** Comprobado:
variables sin usar, parámetros sin usar, `switch` sin `default`, `switch` de un solo `case` y
contador modificado dentro del `for` **pasan sin una queja**. En PHP esos puntos los revisas tú.

### JavaScript (módulos Vue3-CDN)

- Máximo 120 caracteres (`ignoreTemplateLiterals` activo: el `template` de un componente Vue puede
  pasarse).
- **`const` por defecto, `let` si cambia, nunca `var`.**
- **camelCase**; constantes de módulo en `MAYUSCULAS_CON_GUION_BAJO`.
- **Máximo 80 líneas por función** y **4 parámetros**. Con más, pasar un objeto y desestructurar.
- `default-case` en todo `switch`; sin bloques vacíos, tampoco un `catch` vacío.
- `eqeqeq` smart; `no-shadow` y `no-redeclare` activos.
- `console.log` es warning; solo `console.warn` y `console.error`. Quita las trazas de depuración.
- **`no-undef`** es la regla de mayor retorno. Si usas un global que inyecta la aplicación,
  **decláralo en `GLOBALES_APLICACION`** (`eslint.config.js`); nunca silencies la regla.
- **El punto 5 (métodos camelCase) NO lo cubre ESLint**: `camelcase` va con `properties: 'never'` y
  no mira nombres declarados como propiedad de un objeto — que es como se declaran todos los
  métodos de un componente Vue. Revísalos a mano.

**Módulo nuevo:** añadirlo a `MODULOS_ANALIZADOS` **y** a la negación de `ignores`. Las dos cosas.

**En la raíz del módulo va el entry point y nada más.** Ahí `var` es obligatorio: `main.php:1485`
resuelve el constructor con `eval()` y reinyecta el bundle en cada apertura; con `const`, la
segunda apertura lanzaría `Identifier has already been declared`. Pero la excepción se activa con
`php/apps/*/interface/*/*.js`, que casa con **cualquier** `.js` de la raíz: un helper suelto ahí
perdería `no-var`, `no-unused-vars` y `camelcase` sin que nadie lo note (medido: 4 errores en la
raíz frente a 17 del mismo archivo en `componentes/`). Todo lo demás cuelga de `core/`,
`componentes/`, `adaptadores/` o `css/`.

## 4. Arreglos que las herramientas no hacen

| Defecto | Cómo se corrige |
|---|---|
| Nombre fuera de convención | Renombrar y **actualizar los llamadores** (`grep -rn`). Si es público y sale del módulo, pregunta antes |
| Línea > 120 | Partirla por un operador o un argumento, respetando la alineación |
| Función > 100 líneas (PHP) / > 80 (JS) | Extraer un método privado con nombre propio. Pregunta antes: cambia la forma del archivo |
| Más de 4 parámetros | Agrupar en un array asociativo (PHP) u objeto desestructurado (JS) |
| `empty()` | `count($x) === 0`, `$x === ''` o `$x === null` según el tipo real |
| Sintaxis 8.x | Reescribir a 7.4 (`?->` → `isset()` + acceso; `match` → `switch`) |
| Código comentado | Borrarlo |
| `catch` vacío | Loguear con `console.error` / `error_log`, o explicar en un comentario por qué se ignora |
| Falta cabecera de auditoría | Añadirla según §5 |

## 5. Cabecera de auditoría (punto 29 del IC)

**Al crear** un archivo, cabecera en bloque:

```php
/*
 * Nombre usuario: juan_kuga
 * Cod Proyecto: WINET-PRY-2026-0004 — Bloque 2 (Gestión de Red / Control de cambios)
 * Fecha: DD/MM/AAAA
 * Detalle: qué hace y a qué RF/CA responde.
 */
```

**Al modificar** después, una línea al final del bloque de cabeceras:

```php
// juan_kuga - WINET-PRY-2026-0004 - DD/MM/AAAA - qué cambió y por qué.
```

Nunca una cabecera en bloque por cada cambio. **Las cabeceras ya escritas no se tocan** — son
registro histórico. La autoría del código nuevo de PRY-2026-0004 la fija [documentar].

## 5.1 Qué comentario merece quedarse

El comentario que repite lo que ya dice el código es ruido: envejece, miente antes que el código y
obliga a leer dos veces. **Antes de dejar un comentario, comprueba que responde a un "por qué"**,
no a un "qué".

**Se queda** el que documenta una decisión que alguien podría deshacer sin saberlo:

- Por qué se eligió una forma menos evidente (`UNION` en vez de `OR` por el plan de MySQL).
- Una trampa del entorno (el `UNION` pierde el zerofill; dhtmlx no llama al callback con HTTP ≥ 400).
- Una regla de negocio o un CA que el código no puede expresar (`RF08.CA02`).
- Una contrapartida asumida, con su motivo.

**Se borra** el que describe la mecánica: `/* Pinta la lista */` sobre `mostrarLista()`,
`/* Devuelve X */` sobre un `return X`, o el que repite el nombre de la constante que anota.

**Se unifica** cuando hay dos bloques seguidos que hablan de lo mismo — típicamente la cabecera del
archivo y una nota de auditoría pegada debajo: van en **un** bloque, con la línea de auditoría como
último párrafo. Y si el mismo motivo ya está explicado en el punto donde se usa, no se repite en la
declaración.

**Longitud.** Un comentario de más de 6-8 líneas casi siempre está contando historia en vez de
razón: quédate con la razón. Las mediciones, comparativas y el relato del antes/después son
documentación, no comentario (los enruta [documentar]).

**Nunca cites `docs/99-workspace/` desde el código.** No está versionado: esa ruta no existe en el
clon de nadie más y el lector se queda sin la explicación. Si el detalle hace falta para entender el
código, resúmelo en el propio comentario; si no cabe, promuévelo a `docs/00-start-here` …
`docs/05-database` y cita el destino versionado. Lo mismo aplica a los **mensajes de commit y a las
descripciones de MR**.

## 6. Lo que ninguna herramienta ve

Revísalo tú **mientras corriges**, porque no hay sniff que lo detecte:

- **1 y 2 — nada de hardcode de BD ni de IPs.** Todo `DEFINE` vive en `php/database.php`; en el
  front, la configuración se antepone al bundle como `window.<MODULO>_CONFIG` desde PHP.
- **3 — nombres que digan qué contienen.** `$filas`, no `$data2`.
- **9 — nada de HTML en la lógica de negocio.** Las vistas viven en `interface/`.
- **10 — una función, una responsabilidad.**
- **18 — `try/catch` con sentido**; el `catch` que ignora algo explica por qué.
- **20 — no modificar el contador dentro del `for`.**
- **22, 23, 24 en PHP** — PHPStan no los ve.
- **25 — un `switch` con menos de 2 `case` sobra**; conviértelo en `if`.
- **26 — validar los inputs de todo método API** antes de tocar la BD.
- **27 — no reutilizar un nombre de variable para dos propósitos.**

**Ruido esperado, no lo persigas:**

- `Function dbSelect not found` / `Constant X not found` — `database.php` e `index.php` están en
  `excludePaths`, así que PHPStan no ve lo que definen. Sale en todos los archivos.

Cuando toque revisar la rama entera antes del MR, el skill es [cerrar-rf].
