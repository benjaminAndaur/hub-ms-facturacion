# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Flujo de Git (GitFlow)

Este repo (y los otros del Hub: `hub-infra`, `hub-backends`, `hub-ms-operacion`, `hub-frontends`) usa **GitFlow**. Reglas:

- `main` — solo recibe merges desde `develop` o `release/*`. Representa lo desplegable/estable. **Nunca commitear directo aquí.**
- `develop` — rama de integración. Todo el trabajo nuevo (fixes, features) se commitea o mergea aquí primero.
- `feature/*`, `fix/*` — ramas de trabajo creadas desde `develop`, mergeadas de vuelta a `develop`.
- `release/*` — ramas de preparación de release creadas desde `develop`, mergeadas a `main` y de vuelta a `develop`.
- `hotfix/*` — para bugs urgentes en producción: se crean desde `main`, se mergean a **ambos** `main` y `develop`.

Antes de empezar a trabajar, verificar en qué rama se está parado (`git branch --show-current`). Si hay cambios sin commitear directo en `main`, moverlos a `develop` (o a una rama `fix/*`/`feature/*` desde `develop`) antes de commitear.

## Resumen del proyecto

Microservicio de Facturación del Hub Empresarial (Python/Quart, async). Antes vivía como `modulo_facturacion` dentro del monorepo `hub-backends`; se extrajo a este repositorio propio para implementar **Database per Service** de forma completa (código + infraestructura + persistencia, cada uno en su propio repo). Ver `README.md` para arquitectura por capas, autenticación JWT y cómo ejecutar/probar el módulo.

Repos relacionados:
- [`hub-infra`](https://github.com/benjaminAndaur/hub-infra) — nginx, `docker-compose.yml`, contenedor de base de datos `db-facturacion`.
- [`hub-backends`](https://github.com/benjaminAndaur/hub-backends) — resto de microservicios del Hub (siguen en monorepo, comparten `asdf_db`).
- [`hub-ms-operacion`](https://github.com/benjaminAndaur/hub-ms-operacion) — microservicio hermano, también con base de datos propia.
- [`hub-frontends`](https://github.com/benjaminAndaur/hub-frontends) — frontends React/Vite.
