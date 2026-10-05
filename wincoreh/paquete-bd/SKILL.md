---
name: paquete-bd
description: >
  Formato de los paquetes de scripts SQL de WincoreH que se pasan a producción: estructura de
  carpetas, numeración, cabecera en caja, estilo de escritura, script de validaciones aparte y
  rollback. Úsalo SIEMPRE que crees o modifiques un `.sql` bajo `docs/99-workspace/sql/<PRY…>/BD/`,
  y cuando el usuario diga "crea el script de permisos", "haz el SQL del pase", "prepara el
  paquete de BD", "arma el rollback", "script para producción" o pida tocar `co_portlet_events`,
  `co_portlets`, `co_grupos_user`, `m_permisos_grupo` o `users.groups`. Recoge además las trampas
  del esquema que ya nos han costado una regresión.
---

# Paquetes de BD de WincoreH

La referencia visual y estructural es **PRY-2026-0001 (Planta Interna)**:
`docs/PRY2026_0001_PI_WINCOREH/BD/`. Un paquete nuevo se parece a ese, no inventa forma propia.

## 1. Estructura

```
docs/99-workspace/sql/<PRY…>/BD/
  01_<base>/          una carpeta por base de datos destino (01_opticore, 02_datanet, …)
    NN_<PASO>.sql     scripts numerados en orden de ejecución
  rollback/
    01_ROLLBACK_<base>.sql
  README.md
```

### La numeración se hereda, no se renumera

| Nº | Paso |
|:--:|---|
| 01 | `CREATE_TABLES` |
| 02 | `PERMISOS` — app, portlet, grupos, matriz, usuarios |
| 03 | `IMPORT_<algo>` |
| 04 | `DATAPROVIDERS` — los eventos de `co_portlet_events` de los métodos de API |
| 05 | `SP` / `VALIDACIONES` |
| 06+ | `ALTER_<tabla>` |

**Un proyecto que no necesita un paso simplemente no tiene ese archivo, y el número se salta.**
RF-06 de PEXT tiene `02_PERMISOS.sql`, `04_DATAPROVIDERS.sql` y `05_VALIDACIONES.sql`, sin 01 ni
03. Así el lector que conoce Planta Interna sabe qué es cada archivo sin abrirlo.

## 2. La cabecera en caja

Interior de **77 caracteres**, cuatro campos, etiqueta a 14 y `:` alineado:

```sql
-- ┌─────────────────────────────────────────────────────────────────────────────┐
-- │ EJECUTAR EN   : OPTICORE                                                    │
-- │ Carpeta deploy: 01_opticore — paso 02/04 en esta carpeta                    │
-- │ Orden global  : paso 01/02                                                  │
-- │ Rollback      : rollback/01_ROLLBACK_opticore.sql                           │
-- └─────────────────────────────────────────────────────────────────────────────┘
```

El rollback cambia `Carpeta deploy`/`Orden global` por `Revierte` y `Nota`.

## 3. Estilo del cuerpo

Terso. El ejemplo de Planta Interna casi no tiene comentarios, y eso es deliberado: un script de
pase se lee a las dos de la mañana con el ticket abierto al lado.

- **Comentarios de una línea** encima del bloque: `-- Perfiles del módulo (co_grupos_user)`,
  `-- Visor: solo consulta`, `-- Perfil Editor (11 usuarios)`. **Nada de párrafos de prosa**: si
  algo necesita explicación larga, va al `README.md` del paquete o al RF.
- **`SET` → línea en blanco → `SELECT @var;`** por cada variable resuelta. Ese `SELECT` no es
  decorativo: es cómo el operador ve que el script tiene a qué aplicarse.
- **`INSERT INTO tabla (cols)` en una línea, `VALUES` en la siguiente.**
- **Listas de valores alineadas en columnas**, con la segunda columna a ancho fijo:

```sql
INSERT INTO m_permisos_grupo (id_grpu, desc_dominio, desc_accion) VALUES
(@visor, 'MODULO',   'VER'),
(@visor, 'TERMINAL', 'CONSULTAR'),
(@visor, 'VISOR',    'CONSULTAR_POLIGONO')
ON DUPLICATE KEY UPDATE flg_estado = 0;
```

- **Cadenas largas en línea**, sin partir. Un `tx_grupos` de 200 caracteres se escribe entero.
- **Sin `USE`**: el operador se conecta al esquema. Indicar en el README cuál es.
- **`SET NAMES latin1`** cuando se toque `co_portlet_events`, `co_portlets` o `users`: son
  `CHARSET=latin1` y hay valores con eñe (`diseño` en el `tx_grupos` de
  `logcodatossitio.getbyidAll`). Un cliente que fuerce utf8 los corrompe.

### El orden de las secciones de un `02_PERMISOS.sql`

Siempre el mismo, y es el de Planta Interna. De lo general a lo concreto:

```sql
-- Aplicación y portlet
--   co_aplicaciones → co_grupos_app → co_portlets → co_portlet_events ('-INTERFACE-')
--   Cada nivel: INSERT (o resolución si ya existe), SET @id_…, línea en blanco, SELECT @id_…;

-- Perfiles del módulo (co_grupos_user)

-- Permisos por grupo (m_permisos_grupo)
--   Un bloque por grupo, y el SET de ESE grupo justo encima de SU INSERT:
--
--   -- Visor: solo consulta
--   SET @visor = (SELECT id_grpu FROM co_grupos_user WHERE de_grpu = '…' LIMIT 1);
--
--   INSERT INTO m_permisos_grupo (…) VALUES

-- Configuración inicial de usuarios

-- Validaciones: 05_VALIDACIONES.sql
```

**Las variables de grupo no se resuelven todas juntas al principio.** Cada una vive pegada a su
`INSERT`, precedida del comentario que nombra el perfil y su alcance. Así se añade o se quita un
perfil moviendo un bloque, sin tocar nada más.

**La entrada del menú se INSERTA, no se actualiza.** Es `tx_event = '-INTERFACE-'` con
`id_portlet = @id_portlet`; los métodos de datos van en `04_DATAPROVIDERS.sql` con
`id_portlet = 0`. Un script que solo hace `UPDATE` sobre esa fila deja el módulo **sin menú** en
una instalación limpia, que es justo el caso de producción.

## 4. Las comprobaciones van en su propio script

Los scripts que modifican **no llevan `SELECT` de verificación** — solo los `SELECT @var;`.
Todo lo que sirve para comprobar va a `05_VALIDACIONES.sql`: solo `SELECT`, repetible, sin efectos.

Cada consulta lleva encima su número, qué comprueba y **el resultado esperado**:

```sql
-- 2. Recuento de la matriz
-- Esperado: gestor_pext_visor 8 · gestor_pext_editor 13
SELECT gu.de_grpu, COUNT(*) AS acciones
...
```

Una validación sin resultado esperado no sirve: el operador no sabe si lo que ve está bien.

## 5. Obligatorio: idempotencia y resolución por nombre

- **Reejecutable siempre.** `INSERT … ON DUPLICATE KEY UPDATE` cuando hay clave única;
  `INSERT … SELECT … FROM DUAL WHERE NOT EXISTS (…)` cuando no la hay; `REPLACE` para retirar un
  token antes de añadirlo.
- **Nunca un id a pelo.** `id_app`, `id_portlet` e `id_grpu` cambian entre esquemas: `pext` es 19
  en `opticore_db_14072026` y 20 en `opticore_db`. Resuélvelos con un `SET @var = (SELECT … WHERE
  prefix = 'pext')`.
- **Cubrir los estados intermedios.** Un script se ejecuta en esquemas a medias, ya pasados o
  limpios. Si algo se renombró antes, el script nuevo normaliza los tres estados posibles.

## 5.b Lo que corrige un entorno concreto no va en el pase

Producción suele ser una **instalación limpia**: si el objeto se crea por primera vez, el script
del pase solo tiene `INSERT`. Los `UPDATE` que renombran, traducen o limpian restos existen porque
**desarrollo** acumuló pases anteriores, y no tienen sentido en producción — donde además son
ruido que el revisor del ticket tiene que descartar.

Sepáralos en una carpeta `desarrollo/`, fuera de la secuencia numerada:

```
BD/
  01_<base>/     el pase: solo lo que hay que hacer en produccion
  desarrollo/    correcciones de un entorno concreto; NO viaja al pase
  rollback/
```

El README dice entonces dos órdenes de ejecución, uno por entorno, y **advierte si el paso de
desarrollo tiene que ir antes**. Suele tenerlo: un `INSERT … WHERE NOT EXISTS` que busca el nombre
nuevo no reconoce la fila con el nombre viejo y crea un duplicado, dejando huérfano lo que
colgaba del id antiguo.

## 6. Trampas del esquema, ya pagadas

**`users.groups` guarda el grupo por NOMBRE, no por id.** Renombrar en `co_grupos_user` sin
arrastrar el cambio a `users.groups` deja a los usuarios sin acceso, en silencio.

**El dispatcher no consulta `co_grupos_user`.** `php/index.php` compara token contra token entre
`users.groups` y `tx_grupos`. Un grupo puede "funcionar" sin existir como fila — así vivieron
`gestor-cambios-*` hasta que un renombrado los rompió. Al retirar un nombre, hay que barrer las
cuatro tablas: `co_grupos_user`, `users.groups`, `co_portlets` y `co_portlet_events`.

**El menú se filtra por el `tx_grupos` del EVENTO, no por el del portlet.**
`USER::getfullprofileapp` (`php/apps/default/class/user.php`) une por `c.id_portlet = d.id_portlet`
y filtra por `d.tx_grupos`. La columna `co_portlets.tx_grupos` no la lee esa consulta.

**La lista de métodos sale del código, no del prefijo del logic.** Un módulo llama también a
métodos de otros logic; si su `tx_grupos` no lista el perfil, el usuario recibe
`-98 "Permisos insuficientes"` aunque el botón se vea:

```bash
grep -rhoE "'log[a-zA-Z]+\.[a-zA-Z]+'" php/apps/<prefix>/interface/<modulo>/ | sort -u
```

**Los eventos de otros módulos se AMPLÍAN, nunca se reemplazan.** Sobrescribir el `tx_grupos` de
`logcodatossitio.getbyidAll` deja sin API a `catastro_registro`, `tac_user` y `provisiones`.

**`_` es comodín de `LIKE`.** `LIKE '%gestor_pext_%'` casa también con `gestorXpextX`. Con nombres
que lleven guion bajo, usar `=` y `LOCATE()`.

**`m_permisos_grupo.flg_estado` está invertido:** 0 = ACTIVO.

**Los `SELECT` de veredicto no abortan.** El cliente de MySQL no se detiene por el resultado de un
`SELECT`; el operador tiene que mirarlo. Dilo en el README.

## 7. El rollback

**Va en orden inverso al pase**, de lo concreto a lo general — es el orden de Planta Interna:

```
APIs (04_DATAPROVIDERS)  →  entrada -INTERFACE- (02)  →  portlet  →  grupo de menu
    →  aplicacion  →  permisos por grupo  →  usuarios y grupos  →  objetos (DROP)
```

Su caja lleva tres campos, no cuatro: `EJECUTAR EN`, `Rollback` (paso X/Y y qué revierte) y
`Nota` para lo que NO deshace.

Separa siempre los dos DELETE sobre `co_portlet_events` con el criterio de Planta Interna:
`WHERE tx_event <> '-INTERFACE-'` para las APIs, y la condición contraria para la entrada de
menú. Son cosas distintas y se revierten en momentos distintos.

- **Cada sentencia del pase tiene un inverso, y el inverso de un `INSERT` es un `DELETE`.** Si el
  rollback de una fila insertada es un `UPDATE`, o el objeto no era tuyo o el pase está mal
  planteado. Revísalo antes de escribirlo:

  | El pase hizo | El rollback hace | Cuándo |
  |---|---|---|
  | `INSERT` | `DELETE` | la fila es del paquete |
  | `UPDATE` que añade un token | `UPDATE` que lo quita | la fila es de otro módulo y solo la amplías |
  | `UPDATE` que cambia un valor | `UPDATE` al valor literal anterior | la fila es de otro módulo |

- **Decide la propiedad de cada objeto antes de escribir nada**, y que el pase y el rollback digan
  lo mismo. Mezclar criterios —borrar una fila y restaurar la de al lado sin decir por qué— es el
  error que hace irreversible un rollback.
- Lo que existía antes se devuelve a su valor **literal** anterior, aunque fuera "feo" (grupos
  repetidos, nombres que no existen): el objetivo es el estado exacto previo, no uno mejorado.
- No renombres hacia atrás a un nombre que nunca existió — comprueba antes si la fila la creó el
  paquete.
- **Orden:** primero las columnas que referencian por nombre (`users.groups`), después las filas
  referenciadas (`co_grupos_user`).
- **No toques tablas de otros proyectos.** `m_permisos_grupo` la creó PRY-2026-0001: se retiran
  sus filas, no la tabla.

## 8. El README del paquete

Orden de ejecución, prerrequisitos, orden respecto al pase de código, qué toca cada bloque y qué
revisar antes de producción. Es donde va la prosa que no cabe en los `.sql`.

## 9. Antes de entregar

```
[ ] ¿Numeración heredada de Planta Interna?
[ ] ¿Cabeceras en caja, con el mismo ancho en todos los archivos?
[ ] ¿Comentarios de una línea, sin párrafos?
[ ] ¿Los SELECT de comprobación, en 05_VALIDACIONES.sql y con resultado esperado?
[ ] ¿Reejecutable? ¿Ids resueltos por nombre?
[ ] ¿Rollback que revierte esto y solo esto?
[ ] ¿README con orden de ejecución y avisos de producción?
[ ] ¿Comillas y paréntesis balanceados?
[ ] Si no lo has ejecutado, DILO. No des por probado un script que nadie ha corrido.
```
