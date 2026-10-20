# claude-skills

Skills personales de Claude Code, versionados para reutilizarlos entre proyectos.

```
generales/     sirven en cualquier proyecto PHP de WIN → se enlazan en ~/.claude/skills/
  commit/        Conventional Commits con pie Proyecto/Bloque/RF/Ticket/Refs (+ scripts)
  estandar-bd/   estándar de BD de WIN v2.0 (texto íntegro en estandar-v2.md)
  tablero-github/ estado del issue en GitHub Projects: Backlog→Análisis→Desarrollo→Code Review→
                  Aprobado sin saltos, fechas Plan/Real y arrastre del RF padre (+ scripts)
wincoreh/      solo WincoreH → se enlazan en <worktree>/.claude/skills/
  cerrar-rf/  documentar/  endpoint-bruno/  estandar-codigo/  paquete-bd/
  estandar-bd-wincoreh/   cómo se aplica estandar-bd en WincoreH
  spec-rf/    flujo spec-driven de un RF: etapas y puertas, DECISIONES.md, smoke, plantillas
  pruebas-unitarias/  qué regla de negocio lleva prueba, cómo se escribe y se muta; make test
agentes/
  wincoreh/    subagentes de WincoreH → se enlazan en <worktree>/.claude/agents/
    qa-funcional.md     QA independiente en el navegador, contra el DFT, sin ver el código
    revisor-ic.md       checklist IC y defectos sobre el diff, antes del PR
    revisor-pruebas.md  cobertura, correspondencia con el ID y mutación de las pruebas
instalar.sh
```

## Instalar

```bash
./instalar.sh                                   # generales en ~/.claude/skills
./instalar.sh wincoreh /ruta/al/worktree        # una vez por worktree de WincoreH
```

Se instalan como enlaces simbólicos: se edita el skill aquí (o a través del enlace) y el cambio
llega a todos los proyectos. Después, `git commit` y `git push` en este repo.

Si el destino ya tenía una carpeta real con ese nombre y su contenido difiere, el script no la
borra: la mueve a `skills-respaldo/`, junto a la carpeta `skills/`.

## Reglas

- **Un nombre, un sitio.** Un skill no puede estar a la vez en `generales/` y en una colección
  de proyecto: compiten. Lo específico de un proyecto va en un skill aparte con sufijo
  (`estandar-bd-wincoreh`) que remite al general.
- **`generales/` no menciona rutas ni tablas de un proyecto concreto.** Si un skill las necesita,
  esa parte va a la colección del proyecto.
- **Proyecto nuevo** → carpeta nueva junto a `wincoreh/` e `./instalar.sh <carpeta> <ruta>`.
