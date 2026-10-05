---
name: estandar-bd
description: >
  Aplica el estándar corporativo de base de datos de WIN (v2.0) al diseñar o revisar objetos de BD:
  nombres de tablas, columnas, llaves, índices, vistas, SP, triggers y funciones, campos de
  auditoría obligatorios, tipos de datos, cabecera de rutinas y buenas prácticas OLTP. Úsalo
  SIEMPRE antes de escribir un `CREATE TABLE`, `ALTER TABLE … ADD`, `CREATE INDEX`,
  `CREATE PROCEDURE/FUNCTION/VIEW/TRIGGER` o de añadir una tabla a un diagrama/DBML, y cuando el
  usuario diga "crea la tabla", "agrega una columna", "diseña el modelo", "qué nombre le pongo a la
  tabla", "haz el DDL", "revisa el modelo de datos" o "cumple el estándar de BD". Si el proyecto
  tiene un skill `estandar-bd-<proyecto>`, cárgalo también: concreta cómo se aplica allí.
---

# Estándar de base de datos de WIN (v2.0)

El texto íntegro del estándar está en `estandar-v2.md`, en esta misma carpeta. Léelo cuando una
duda no la resuelva este resumen. Este archivo dice **cómo aplicarlo** en proyectos PHP con MySQL
(y PostgreSQL cuando aplique).

Si el proyecto tiene un skill `estandar-bd-<proyecto>`, sus reglas concretas (prefijo de módulo,
de dónde salen los valores de auditoría, dónde se documenta el modelo) mandan sobre los ejemplos
genéricos de aquí.

## 1. Alcance: solo objetos nuevos

El estándar §4 lo dice explícito: **se aplica a los objetos nuevos**.

- **No renombres** tablas ni columnas existentes que no lo cumplan: un rename rompe todo lo que
  las consulta, a menudo en archivos sin análisis estático.
- **Columna nueva en tabla heredada** → la columna sí cumple el estándar (prefijo de uso, tipo,
  snake case), aunque sus vecinas no lo hagan.
- **Tabla nueva** → cumple todo: nombre, PK, FK, auditoría, índices.
- Si el usuario pide copiar el patrón de una tabla heredada que lo incumple, avísalo antes de
  escribir y propone la variante conforme.

## 2. Tablas

### 2.1 Esquema según el motor

El estándar escribe `<esquema>.x_<nombre>` (`crm.m_planilla`), con esquema de máximo 3 caracteres.

- **PostgreSQL / SQL Server:** úsalo tal cual, con esquemas reales.
- **MySQL:** esquema = base de datos (§7.2). Cuando todas las tablas de la aplicación viven en una
  sola base, el esquema pasa a ser un **segmento del nombre** que identifica el módulo:

  ```
  <x>_<modulo>_<nombre>          t_pext_enlace · m_pint_dispositivo
  ```

  El segmento de módulo se omite solo si la tabla es transversal de verdad (`m_permisos_grupo`).

| Letra `x` | Tipo |
|---|---|
| `t` | transaccional |
| `m` | maestra |
| `p` | paramétrica |

### 2.2 Reglas

- Minúsculas, snake case, **sustantivo en singular**: `t_pext_tramo`, no `t_pext_tramos`.
- **Máximo 30 caracteres** el nombre completo. Cuéntalo; si se pasa, abrevia con los acrónimos
  de §3, no con siglas inventadas.
- Solo `a-z`, `0-9` y `_`. **Sin tildes, ñ ni diéresis** (`anio`, no `año`). Evita números.
- **PK única y no nula**, primera columna, autoincremental siempre que se pueda.
- **Una FK por relación**. Si no puede declararse (otra base, tabla heredada con tipo distinto),
  documenta la relación lógica en el diagrama del proyecto.
- §8.7: toda tabla nueva debe decir **con qué tabla se relaciona**. Binarios o texto grande
  (`text`, `blob`, imágenes) van en una tabla hija. Nada de un `varchar` gigante con
  observaciones concatenadas: tabla de detalle con una fila por entrada.
- Tablas grandes con historia → prever partición por fecha o período.

## 3. Columnas

Forma: `<prefijo de uso>_<nombre>`, minúsculas, snake case.

| Prefijo | Uso | Tipo MySQL orientativo |
|---|---|---|
| `id_` | Identificador numérico (PK y FK) | `int` / `int unsigned` (igual al de la PK referida) |
| `cod_` | Código de negocio | `varchar(n)` o `int` |
| `mnt_` / `imp_` | Monto o importe con decimales | `decimal(p,s)`, **nunca `float`** |
| `cant_` | Cantidad | `int` |
| `cat_` | Categoría | `varchar(n)` corto |
| `num_` | Número entero (secuencia, orden) | `int` / `smallint` |
| `fec_` | Fecha (`date` o `datetime`) | `date` / `datetime` |
| `hrs_` | Hora | `time` |
| `desc_` | Nombre o descripción | `varchar(n)` ajustado |
| `flg_` | Lógico | **`bit(1)`** |
| `tip_` | Tipo | `varchar(n)` corto, o `id_tip_…` si va a catálogo |

- Una columna que no encaja en ningún prefijo es señal de que el nombre no dice qué guarda
  (`nombre_dispositivo` → `desc_dispositivo`). No inventes prefijos.
- **Evita `NULL`**: `NOT NULL` con `DEFAULT` salvo que la ausencia de valor signifique algo.
- Longitud: la mínima suficiente. `varchar(255)` "por si acaso" no vale.
- Tipos consistentes con la columna referida (si la PK es unsigned, la FK también).
- Orden natural: PK, FK, datos de negocio, `flg_` de estado y, al final, la auditoría.

## 4. Campos de auditoría (obligatorios en toda tabla nueva)

§8.1 los exige con estos nombres y tipos; sin ellos el pase no se aprueba:

```sql
	desc_usuario_crea	varchar(50)	not null,
	desc_host_crea		varchar(50)	not null,
	fec_creacion		datetime	not null default current_timestamp,
	nom_app			varchar(50)	not null,
	desc_usuario_modf	varchar(50)	null,
	desc_host_mdf		varchar(50)	null,
	fec_modf		datetime	null on update current_timestamp,
	nom_app_modf		varchar(50)	null
```

- Los nombres son **literales del estándar**, incluida la asimetría `desc_host_mdf` /
  `desc_usuario_modf`. No los "corrijas": Ingeniería de Datos valida contra esa lista.
- El orden y los `null` de los campos de modificación son propuesta de este skill; el estándar
  solo fija nombre y tipo.
- Valores: `desc_usuario_*` ← usuario autenticado; `desc_host_*` ← IP o host del cliente;
  `nom_app*` ← nombre de la aplicación y módulo. La aplicación los escribe en cada `INSERT` y
  `UPDATE` (§10.h exige actualizarlos en cada modificación).
- Si además hace falta el id numérico del usuario para hacer JOIN, añádelo como columna de negocio
  (`id_usuario_crea`) **sin sustituir** los ocho campos.

## 5. Constraints e índices

| Objeto | Forma | Ejemplo |
|---|---|---|
| PK | `pk_<tabla>` | `pk_t_pext_tramo` |
| FK | `fk_<tabla referencia>_<tabla origen>` | `fk_t_pext_tramo_t_pext_enlace` |
| Índice | `ix_<tabla>_<definición>` | `ix_t_pext_tramo_id_enlace` |
| Default (opcional) | `df_<tabla>_<campo>` | — |
| Check (opcional) | `ck_<tabla>_<campo>` | `ck_t_pext_tramo_num_orden` |

- **MySQL ignora el nombre de la PK** (siempre `PRIMARY`). Escríbelo igual
  (`constraint pk_… primary key (…)`): documenta la intención y vale si la tabla cambia de motor.
- Índices nuevos con `ix_`, no `idx_`. Dos índices sobre el mismo campo → sufijo numérico.
- Indexa solo lo necesario (§8.5): no columnas casi nunca filtradas, ni de baja cardinalidad
  (`flg_`), ni `text`. Antes de crear uno, mira si ya hay otro que lo cubra.

## 6. Rutinas y vistas

| Objeto | Forma | Notas |
|---|---|---|
| Procedimiento | `sp<x>_<tabla>_<opcional>` | `x`: `s` select por llave · `i` insert · `u` update · `d` delete · `p` proceso multi-tabla · `a` todos · `l` listado · `c` combo · `t` árbol · `h` árbol en combo · `r` reporte. Nunca `sp_`. Opcional ≤20 caracteres |
| Función | `fn_<nombre>` (escalar) · `ft_<nombre>` (tabla) | ≤20 caracteres |
| Vista | `<esquema o módulo>_v_<nombre>` | Sobre una sola tabla, toma el nombre de la tabla |
| Trigger | `trg_<i\|u\|d…>_<tabla>_<opcional>` | Con control de errores y rollback ante fallo |

Toda rutina abre con la cabecera del estándar (§7.3.3 / §7.3.6); en funciones, `Nombre FUN`:

```sql
/****************************************************************
* Nombre SP          : spl_t_pext_tramo_por_enlace
* Propósito          : Lista los tramos de un enlace en orden de recorrido.
* Input              : p_id_enlace - enlace a consultar
* Output             : id_tramo, num_orden, desc_tramo
* Creado por         : <Responsable>
* Fec Creación       : DD/MM/AAAA
* Fec Actualización  :
* Actualizado por    :
* Ticket/Proyecto    : <ticket o código de proyecto>
* Incluir detalle de cambios
****************************************************************/
```

Al modificar una rutina existente se **añaden** líneas de cambio; la descripción original no se
toca (§7.1).

## 7. SQL que se escribe (DDL, scripts y consultas desde PHP)

Checklist §9 adaptado a MySQL:

- Sin `SELECT *`: columnas explícitas. `COUNT(1)`, no `COUNT(*)`.
- Alias en toda consulta de más de una tabla; sin productos cartesianos.
- `UNION ALL` salvo que haga falta deduplicar.
- Sin funciones ni conversiones sobre la columna filtrada (`WHERE date(fec_x) = …` → rango).
- `LIKE 'xxx%'` sí; `LIKE '%xxx'` solo con justificación.
- `IS NULL`, nunca `= NULL`.
- Sin cursores: operaciones por conjunto.
- No actualizar columnas de PK.
- Id insertado: `LAST_INSERT_ID()` / `PDO::lastInsertId()` de la misma conexión (el equivalente
  MySQL del `OUTPUT` que pide el estándar).
- Scripts de pase con **más de 100 sentencias DML** → carga masiva (`INSERT … SELECT`,
  `LOAD DATA`), no cientos de `INSERT` sueltos.
- Indentación con TAB; comentarios multilínea `/* */`, en línea `--`.
- Variables de rutina en snake case equivalentes a la columna (`p_id_enlace`, `v_cant_hilos`);
  contadores `i`, `j`, `k`.
- Todo pase lleva su **script de rollback** (§8.1): DML inverso, `DROP` de objetos nuevos,
  recálculo de autonuméricos y contadores.

**§8.2 "evitar SQL desde la aplicación".** Muchos proyectos PHP construyen sus consultas en la
capa de acceso a datos. No cambies esa arquitectura por tu cuenta: para lógica multi-tabla pesada
o procesos (cálculos, cierres) propón un SP `spp_…`; para el CRUD normal sigue el patrón del
proyecto y, si te piden una inspección, señálalo como desviación conocida.

## 8. Antes de entregar un DDL

Recorre la lista y **reporta** lo que no cumpla en vez de corregirlo en silencio:

- [ ] Nombre `<t|m|p>_<módulo>_<sustantivo_singular>` (o `<esquema>.<t|m|p>_…`), ≤30 caracteres, sin tildes ni ñ
- [ ] PK primera columna, `not null`, autoincremental, `constraint pk_<tabla>`
- [ ] Cada relación con su `fk_<ref>_<origen>` (o relación lógica documentada)
- [ ] Toda columna con prefijo de §3 y tipo/longitud ajustados; `flg_` en `bit(1)`; montos en `decimal`
- [ ] `NOT NULL` por defecto; cada `NULL` tiene motivo
- [ ] Los 8 campos de auditoría con sus nombres literales
- [ ] Índices `ix_` solo donde hay consulta que los use
- [ ] Rutinas con cabecera del estándar y prefijo `sp<x>_` / `fn_` / `ft_` / `trg_`
- [ ] Script de rollback del objeto
- [ ] Tabla añadida al diagrama o DBML del proyecto
