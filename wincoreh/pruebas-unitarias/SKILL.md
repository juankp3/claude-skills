---
name: pruebas-unitarias
description: >
  Pruebas unitarias de WincoreH: qué lógica de negocio merece prueba y cuál no, cómo se escriben
  en tests/ (PHPUnit 9.6 para helpers PHP, node:test para el core JS de los módulos Vue3-CDN),
  cómo se comprueba que una prueba puede fallar y cómo se enlazan con los criterios del RF. Dos
  modos: `fase` (pruebas de lo que una fase de /spec-rf acaba de escribir) y `retro RF-NN` (pruebas
  de un RF ya implementado). Úsalo cuando el usuario diga "pruebas unitarias", "unit test",
  "escribe los tests", "agrega pruebas", "make test", "qué hay que probar" o al cerrar una fase de
  /spec-rf que añada o cambie reglas de negocio.
---

# Pruebas unitarias en WincoreH

`make test` es la tercera puerta, junto a `make lint` y el smoke: el lint dice que el código está
bien escrito, el smoke dice que la pantalla se comporta, y **las pruebas unitarias dicen que las
reglas de negocio hacen lo que pide el DFT**, en menos de un segundo y sin base de datos.

Convenciones del repo (estructura, cargadores, dobles): `tests/README.md`. Léelo antes de escribir
la primera prueba de la sesión.

## 1. Qué se prueba — el filtro

No se prueba todo. Una función o un método lleva prueba si cumple **al menos uno**:

| # | Criterio | Ejemplos (Bloque 3) |
|---|---|---|
| 1 | Decide **qué se graba** | `ControlcambiosGuardado::planificar`, `filaTramo` |
| 2 | Decide **quién puede** hacer algo | `ControlcambiosReservaEdicion::esDeOtroVigente`, `CcReservaCables` |
| 3 | Es una **regla del DFT con casos límite** que se puede romper sin que se note en pantalla | V2–V8 del guardado, `CcRecorridoEdicion.incorporar` |
| 4 | Es un **contrato front/back**: lo que publica un `perfilWeb()` y el JS consume | tipos incorporables, espera del guardado |

**No** llevan prueba unitaria — se verifican con Bruno o el smoke, y está bien así:

- `class/` (SQL) y `logic/` (transporte): Bruno, con sus peticiones `-rechazo-`.
- Componentes Vue y el visor de Google Maps: smoke en el navegador.
- Validaciones de entrada simples (tipo, longitud): las peticiones `-rechazo-` de Bruno.
- Textos, getters, mapeos sin decisión.

Si una regla crítica vive dentro de un componente (`mapa.js`) y no se puede cargar en Node,
**sácala a una función pura de `core/`** y pruébala ahí. Es la misma separación que pide el
estándar (`core/` sin DOM) y es lo que hizo RF-07 con `idsInfraestructuraEnRecorrido`.

## 2. Cómo se escribe

### PHP — `tests/php/<ruta espejo de php/>/<Clase>Test.php`

- `require_once` con la ruta relativa a `php/` (`'apps/pext/helpers/X.php'`): el bootstrap pone
  `php/` en el include_path y carga `comun/autoload.php`. Cargar `class/` está permitido para sus
  constantes y funciones puras (`ControlcambiosRecorrido::huella`); llamar a sus consultas no.
- `dbSelect`/`dbExecute` existen en el bootstrap **solo para fallar**. Si una prueba los alcanza,
  lo probado no es puro: prueba la parte pura o déjalo para Bruno.
- Métodos **privados puros** de un helper: `MetodoPrivado::invocar(Clase::class, 'metodo', $args)`.
  No los hagas públicos para probarlos.
- Cada prueba con `@testdox <ID> · <qué comprueba>` **y** un `@group RFNN` por cada RF que cubre:
  `make test FILTRO=RF08` filtra PHP por grupo, no por el testdox. El método en camelCase estricto
  (sin dos mayúsculas seguidas: `IdY…` falla PHPCS).
- Datos literales y mínimos, construidos con métodos privados de la clase de prueba (`tramo()`,
  `fila()`), no con fixtures en archivos.

### JS — `tests/js/apps/<app>/<modulo>/<ruta>/<archivo>.test.js`

- `node:test` (`describe`, `test`, `beforeEach`) y `node:assert/strict`. Sin dependencias npm.
- `cargarModulo({ archivos, globales })` de `tests/js/soporte/modulo.js` ejecuta los `.js` reales
  en el orden del manifest. `CC_CONFIG` sale de PHP en cada ejecución (`perfil.php`): si añades un
  `perfilWeb()` que el JS consume, añádelo también ahí.
- El servidor se sustituye con `crearServicios()` de `soporte/servicios.js`; cada prueba cambia
  la función que necesita que falle (`servicios.renovarReserva = async () => { throw … }`).
- La sesión no devuelve sus promesas: `await esperarPromesas()` antes de afirmar.
- Cada prueba abre con su ID: `test('RF03-RN06 · …', …)`; sin ID, `FILTRO` no la encuentra. Prepara su estado en `beforeEach` o al
  principio; ninguna depende de que otra haya corrido antes.

### Para las dos

- **Cabecera de auditoría** como cualquier archivo (punto 29 del IC): qué RF cubre el archivo y
  **por qué** importa que no falle, en una o dos frases.
- **Lint:** `make lint-file FILE=tests/php/…` (PHPCS no mira `tests/` por defecto) y `make eslint`
  (ya incluye `tests/js`).

## 3. Cómo se ejecutan

```bash
make test               # todas, en silencio: solo fallos y resumen
make test FILTRO=RF08   # las del RF en curso, una por línea (evidencia)
```

- **Mientras se desarrolla**, `FILTRO` del RF: feedback rápido y la lista con nombres.
- **En las puertas** (fase de `/spec-rf`, `/cerrar-rf`, antes de un PR): **sin filtro**. Corren las
  de todos los RF y proyectos; un fallo ajeno es una regresión del cambio en curso. O se corrige el
  código, o —si el cambio de comportamiento es intencional— se actualiza esa prueba diciéndolo en el
  commit. Nunca se borra ni se salta.
- `ninguna prueba coincide con el filtro` / `No tests executed!`: el RF no tiene pruebas todavía, o
  les falta el ID o el `@group`.

## 4. Toda prueba nueva tiene que poder fallar

Una prueba que pasa a la primera no demuestra nada hasta que la ves fallar. Antes de dar por buena
una batería, **rompe a propósito cada regla crítica** que prueba y comprueba que se pone en rojo:

```bash
F=php/apps/pext/helpers/ControlcambiosGuardado.php
git diff --quiet -- "$F" || { echo "con cambios sin commitear: no mutar"; exit 1; }
sed -i '' 's/&& $vistas\[$clave\] > 1/\&\& false/' "$F"   # desactiva V8
make test-php                                              # debe fallar
git checkout -- "$F"                                       # restaurar SIEMPRE
```

- Solo sobre archivos **sin cambios pendientes**: el `git checkout` los restaura del commit.
- Si una mutación sobrevive, falta un caso: escríbelo (pasó con el tope de `idQueCabe`).
- En el reporte, di qué reglas mutaste y que todas se detectaron.

## 5. Modo `fase` — dentro de `/spec-rf`

Al cerrar una fase (`/spec-rf` §5), **antes del commit**:

1. Lista las funciones nuevas o cambiadas de la fase en `helpers/`, `validaciones/` y `core/` y pasa
   cada una por el filtro del §1. Di cuáles llevan prueba y, de las que no, por qué en una frase.
2. Escribe las pruebas; si una regla no se puede cargar en Node, sácala a `core/` (§1).
3. `make test` en verde y mutación de cada regla nueva (§4).
4. Van en el **mismo commit de la fase** (el `RF:` del pie ya cita los criterios). Un archivo de
   prueba sin su código, o al revés, rompe la trazabilidad.
5. En la matriz de `RF-NN.md`, columna *Evidencia*: `unit <archivo>` como evidencia previa.

El plan de cada RF (`plantillas/plan.md`) lleva una tarea `Tn.P · pruebas unitarias` por fase y una
columna *Prueba unitaria* en la trazabilidad: `/spec-rf preparar` comprueba que esté.

## 6. Modo `retro RF-NN` — un RF ya implementado

1. Lee la matriz de trazabilidad de `RF-NN.md`: la columna *Dónde* dice qué archivos implementan
   cada CA.
2. Pasa cada archivo de `helpers/`, `validaciones/` y `core/` por el filtro del §1 y presenta al
   usuario una tabla `Regla · Archivo · Criterio del filtro · ¿Prueba?` antes de escribir.
3. Si el RF tiene pruebas de Node en `docs/99-workspace/smoke/node/`, **mígralas** a `tests/js`: ya
   están validadas contra el smoke. Después pueden borrarse del workspace.
4. Escribe, muta (§4), `make test` en verde.
5. Commit aparte, tipo `test`, con los criterios en el pie (`/commit`): no es código de una fase.

## 7. Qué cuenta como evidencia

Una prueba unitaria es **evidencia previa** en la escala de `/spec-rf` §2: sube un CA a 🔵, no a ✅.
Prueba la regla, no que la pantalla la respete; el ✅ sigue saliendo del smoke o de Bruno. Lo que sí
cambia: una regla con prueba unitaria **ya no se reabre en silencio**. Si una fase posterior la
rompe, `make test` lo dice antes del commit.

## 8. Reporte

```
Pruebas unitarias — <RF / fase>
| Archivo de prueba | Pruebas | Criterios | Mutaciones detectadas |
make test: PHP N/N · JS N/N
Sin prueba, a propósito: <función> — <motivo>
```
