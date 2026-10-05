---
name: estandar-bd-wincoreh
description: >
  Cómo se aplica el estándar de base de datos de WIN (skill `estandar-bd`) dentro de WincoreH:
  prefijo de app en el nombre de tabla, de dónde salen los valores de auditoría en `$body`,
  precedentes del esquema que no hay que copiar, dónde se documenta el modelo y la relación con
  `paquete-bd`. Úsalo junto con `estandar-bd` siempre que en WincoreH se cree o modifique una
  tabla, columna, índice o rutina, o se toque el `schema.dbml` de un proyecto.
---

# Estándar de BD en WincoreH

Carga primero **`estandar-bd`**: tiene las reglas. Aquí solo va lo que cambia o se concreta en
este repo. La transcripción del estándar también está versionada en
`docs/05-database/estandares-base-de-datos.md`.

| Skill | Qué fija |
|---|---|
| `estandar-bd` | Nombres, tipos, auditoría, constraints y calidad del SQL |
| **estandar-bd-wincoreh** (este) | Su aplicación concreta en WincoreH |
| `paquete-bd` | Carpetas, numeración, cabecera en caja, validaciones y rollback del paquete |
| `estandar-codigo` | El PHP de `class/` que lanza las consultas |

## 1. Nombre de tabla

Todo vive en el esquema principal (MySQL), así que se usa la forma `<x>_<prefix>_<nombre>`, donde
`<prefix>` es el de `co_aplicaciones` (`pext`, `pint`…). Ejemplos conformes ya en el repo:
`t_pext_enlace`, `t_pext_recorrido`, `m_pext_config_tipos`, `m_permisos_grupo` (transversal, sin
prefix de app).

Las otras bases del mismo servidor (`opticore_datamart.`, `opticore_tickets.`…) hacen de esquema
en la consulta; no se repite su nombre dentro del nombre de la tabla.

## 2. Tablas heredadas

`co_*`, `ta_*`, `tl_*`, `taun_*`, `op_*`, `tic_*` son anteriores al estándar: **no se renombran**
(las consultan `main.php` y `php/index.php`, que están fuera de PHPCS y PHPStan; un rename
rompe en silencio). Columnas nuevas en ellas sí siguen el estándar.

## 3. Precedentes que no son plantilla

- **Plurales:** `t_pint_nodo_dispositivos`, `t_pint_nodo_dispositivos_puertos`. Las nuevas, en
  singular.
- **Auditoría de PRY-2026-0001:** `id_usuario_crea` / `fec_usuario_crea` / `id_user_mod` /
  `fec_mod`. No es la del estándar. Una tabla nueva lleva los ocho campos literales; si necesita
  el id numérico del usuario, lo añade como columna de negocio además de ellos.
- **Índices `idx_…`** (`idx_nodo_dispositivo`): los nuevos van con `ix_<tabla>_<definición>`.
- **Columnas sin prefijo de uso** (`nombre_dispositivo`, `tipo_evento`, `ip_usuario`): en
  columnas nuevas, `desc_dispositivo`, `tip_evento`, `desc_host_…`.

## 4. Valores de auditoría

`php/index.php` inyecta en `$body` los datos del usuario autenticado. El `class/` los recibe del
logic y los escribe en cada `INSERT` y `UPDATE`:

| Campo | Origen |
|---|---|
| `desc_usuario_crea` / `desc_usuario_modf` | `USER_EMAIL` (o `USER_NAME`) |
| `desc_host_crea` / `desc_host_mdf` | `IPSOURCE` |
| `nom_app` / `nom_app_modf` | `'wincoreh-<prefix>'`, p. ej. `'wincoreh-pext'` |
| `fec_creacion` / `fec_modf` | El motor (`default` / `on update current_timestamp`) |

## 5. SQL desde `class/`

La arquitectura vigente construye las consultas en `php/apps/<prefix>/class/` con
`dbSelect`/`dbExecute` (solo `class/` habla con la BD). Es la desviación conocida frente a §8.2
del estándar: no la cambies; para procesos multi-tabla pesados propón un SP `spp_…`. Los SP
existentes de `datanet_db` (`spl_listar_detalle_tooltip_sitio`) ya siguen el prefijo `sp<x>_`.

## 6. Dónde queda documentado

- Cada tabla nueva o tocada por un proyecto entra en
  `docs/05-database/proyectos/<pry-…>/schema.dbml` (con `Note` y relaciones lógicas cuando no hay
  FK real) y en su `catalogo-tablas-diagrama.md`.
- El DDL y su rollback van en el paquete de `docs/99-workspace/sql/<PRY…>/BD/` con el formato de
  `paquete-bd` (`01_CREATE_TABLES`, `06+ ALTER_<tabla>`).
- Cabecera de rutinas: `Creado por : Juan Kuga` y `Ticket/Proyecto : PRY-2026-0004 · RFxx` en
  código nuevo de ese proyecto (ver `documentar` §4).
