---
name: endpoint-bruno
description: >
  Registra en la colección Bruno de `docs/04-api/bruno/` todo método API nuevo o modificado de
  WincoreH, con su body de ejemplo, sus variables y su documentación (RF, parámetros, códigos de
  error, fila de co_portlet_events). Úsalo SIEMPRE que se cree, renombre o cambie la firma de un
  `log<nombre>.<accion>`, y cuando el usuario diga "registra el endpoint", "añádelo a Bruno",
  "actualiza la colección", "documenta el endpoint", "quiero probar el endpoint" o pregunte qué
  endpoints tiene el proyecto. También cubre poner a punto la colección para usarla (entorno,
  credenciales, token de sesión).
---

# Registrar un endpoint en la colección Bruno

La colección vive en **`docs/04-api/bruno/`** y se abre con *Open Collection* en Bruno.app. Está
versionada: es el registro de la API que sí sobrevive al worktree, a diferencia de
`docs/99-workspace/`.

Un endpoint no está terminado hasta que está en la colección. El código dice cómo se llama; la
colección dice **cómo se invoca y qué devuelve**, que es lo que no se puede deducir leyendo el PHP.

## Estructura

```
docs/04-api/bruno/
  bruno.json                    identidad de la colección
  collection.bru                headers comunes + contrato del endpoint único
  .env                          credenciales (NO versionado)
  .env.example                  plantilla versionada
  environments/Local.bru        baseUrl, deviceId, ticked, datos de prueba
  00-sesion/                    cadena de login: createtickedtodevice → login
  <prefix>-<logic>/             una carpeta por módulo: pext-logcontrolcambios/, pint-…
    <accion>.bru                una petición por método
```

Carpeta por **app + logic** (`pext-logcontrolcambios`), archivo por **acción** (`buscarTerminal.bru`).
El nombre del archivo es la acción tal cual aparece en `method`, sin prefijo.

## Plantilla de una petición

```
meta {
  name: <accion>
  type: http
  seq: <orden dentro de la carpeta>
}

post {
  url: {{baseUrl}}/php/
  body: json
  auth: none
}

body:json {
  {
    "method": "log<nombre>.<accion>",
    "params": {
      "ticked": "{{ticked}}",
      "<parametro>": "<valor de ejemplo que funcione>"
    }
  }
}

assert {
  res.status: eq 200
}

docs {
  **RF-NN — <título>.** <proyecto>.

  | Parámetro | Obligatorio | Reglas |
  |---|---|---|

  <forma de la respuesta, casos límite, fila de co_portlet_events>
}
```

## Peticiones que prueban un criterio: `tests` y casos de rechazo

El `assert` dice que la petición respondió; un bloque `tests` dice que **cumple un CA**. Es la
única evidencia ejecutable que tiene el repo, así que todo método que implemente un CA con reglas
—validaciones, rechazos, códigos— lleva:

1. **La petición feliz** (`<accion>.bru`) con `tests` sobre `status` y la forma de `datos`.
2. **Una petición por código de rechazo** que se pueda provocar sin preparar datos a mano:
   `<accion>-rechazo-<motivo>.bru` (`guardarRecorridoCable-rechazo-huella.bru`). Si un rechazo
   necesita datos preparados (un elemento dado de baja), se documenta en `docs` del feliz como
   «caso manual» en vez de crear una petición que no se puede repetir.
3. El **nombre de cada test empieza por el ID** del criterio que prueba, para que el resultado
   sirva de evidencia en la matriz (`/spec-rf` §6):

```
tests {
  test("RT02.CA09 · huella vieja → RECORRIDO_CAMBIO", function() {
    expect(res.getStatus()).to.equal(400);
    expect(res.getBody().status).to.equal(-1);
    expect(res.getBody().codigo).to.equal("RECORRIDO_CAMBIO");
  });
}
```

Una petición de rechazo **nunca escribe**: elige el motivo de modo que la validación corte antes
de la primera escritura. Si no es posible, no se crea.

Cuatro reglas que no se negocian, porque son las que hacen fallar la petición:

1. **`{{baseUrl}}/php/` con barra final.** Sin ella el servidor redirige y la redirección degrada
   el POST a GET: el body se pierde.
2. **`"ticked": "{{ticked}}"`** en todo método cuyo `tx_grupos` no sea `todos`. Sin él,
   `php/index.php` responde `-1 "informacion no convincente"`.
3. **Valores de ejemplo que funcionen de verdad**, no `"string"`. Quien abra la colección dentro
   de tres meses tiene que poder pulsar *Send* y ver datos.
4. **Nada de credenciales ni tokens en el `.bru`.** Van en `.env` (`{{process.env.…}}`) o en el
   entorno. Los `.bru` se versionan.

## Qué escribir en el bloque `docs`

Es la mitad del valor de la colección. Como mínimo:

- **RF y CA** que implementa el método, para poder volver al requerimiento.
- **Tabla de parámetros**: obligatoriedad y reglas de validación reales (longitudes, juego de
  caracteres, tipos), copiadas de la validación del logic, no inventadas.
- **Forma de la respuesta** y qué significa el caso vacío (`data: []` frente a `data: null`).
- **Casos límite que conviene probar**: el que no devuelve nada, el que es lento, el que dispara
  la validación.
- **La fila de `co_portlet_events`** que el método necesita y el SQL donde está.

### Cuidado con los ejemplos de código dentro de `docs`

Bruno le quita 2 espacios de indentación a todo el bloque `docs`. Si tras ese recorte una línea
queda en columna 0 con **forma de bloque `bru`** —`identificador: {`— Bruno no lista la petición:
la carpeta se ve, pero ese `.bru` desaparece de la barra lateral **sin ningún mensaje de error**.

Pasó con `getPermisos.bru`: un ejemplo de Vue con `  computed: {` lo hizo invisible. Engaña
porque el archivo es válido —`bruToJsonV2` lo parsea sin quejarse en todas las versiones del
parser— así que buscar un fallo de sintaxis no lleva a ningún sitio.

**Regla:** indenta el contenido de los bloques de código con **4 espacios** (2 del bloque + 2
propios), de modo que nada caiga en columna 0 tras el recorte. Para comprobarlo:

```bash
cd docs/04-api/bruno/<carpeta>
for f in *.bru; do
  ini=$(grep -n '^docs {' "$f" | cut -d: -f1); [ -z "$ini" ] && continue
  awk -v i="$ini" 'NR>i { l=$0; sub(/^  /,"",l);
    if (l ~ /^[A-Za-z_][A-Za-z0-9_:.-]*[[:space:]]*\{[[:space:]]*$/)
      printf "%s:%d  %s\n", FILENAME, NR, $0 }' "$f"
done
```

Sin salida = correcto. Si una petición no aparece en Bruno, este es el primer sitio donde mirar,
antes que el vigilante de archivos o la caché.

## Variables

| Variable | Origen |
|---|---|
| `baseUrl` | `http://localhost:${WEB_PORT}` — cambia por worktree (`.env` de la raíz) |
| `deviceId` | constante del entorno; identificador libre |
| `tickedDispositivo` | lo rellena `00-sesion/01` vía `vars:post-response` |
| `ticked` | lo rellena `00-sesion/02` con `res.body.controlkey` |
| datos de prueba | uno por endpoint que lo necesite (`idSitioPrueba`, …), vacíos en el repo |

Para capturar un valor de una respuesta y encadenarlo, usa `vars:post-response` (declarativo y
visible en la UI) antes que un `script:post-response`.

## Al crear un endpoint nuevo — orden de trabajo

1. Escribe el método en `logic/log<nombre>.php` con su validación de inputs.
2. Deja el SQL de `co_portlet_events` en `docs/99-workspace/sql/`, idempotente.
3. **Añade el `.bru`** siguiendo la plantilla.
4. Añade los `tests` y las peticiones de rechazo (sección anterior).
5. Ejecútalo en Bruno y pega el resultado real en el bloque `docs` si aporta (forma de la
   respuesta, tiempos). Si no puedes ejecutarlo —BD caída, sin sesión—, **dilo**; no dejes un
   `.bru` sin verificar haciéndolo pasar por probado. Un test que nunca se ejecutó no es
   evidencia: el CA sigue en 🔵.
6. Si cambias la firma de un método existente, actualiza su `.bru` en el mismo commit. Un ejemplo
   que ya no funciona es peor que no tener ejemplo.

## Puesta a punto (primera vez o token caducado)

1. `make up` y comprobar que el contenedor responde en `baseUrl`.
2. `cp docs/04-api/bruno/.env.example docs/04-api/bruno/.env` y rellenar usuario y contraseña.
3. En Bruno: *Open Collection* → `docs/04-api/bruno`, y seleccionar el entorno **Local**.
4. Correr `00-sesion/01` y `00-sesion/02`. A partir de ahí, `{{ticked}}` está resuelto.

Si aparece `-1 "informacion no convincente"` a mitad de sesión, el token caducó: repetir el paso 4.
Ojo: `createtickedtodevice` invalida el token anterior de ese `deviceId`, así que si compartes
`deviceId` con tu sesión del navegador, la cierras.

## Límites

- La colección **no viaja a producción**: está excluida en `deploy-export.ignore`.
- No hay CLI (`bru`) instalado en este equipo; las peticiones se ejecutan desde Bruno.app. Para
  verificación automatizable sigue estando el smoke de `docs/99-workspace/smoke/`.
- `formulario` devuelve **JavaScript**, no JSON: no le pongas asserts sobre `res.body.status`.
