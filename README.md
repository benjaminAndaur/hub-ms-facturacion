# hub-ms-facturacion

Microservicio de Facturación del Hub Empresarial. Expone una API REST (Quart, async) para crear, listar, actualizar y eliminar facturas.

Repos relacionados: [`hub-infra`](https://github.com/benjaminAndaur/hub-infra) (nginx, docker-compose, base de datos), [`hub-backends`](https://github.com/benjaminAndaur/hub-backends) (resto de microservicios), [`hub-ms-operacion`](https://github.com/benjaminAndaur/hub-ms-operacion) (microservicio hermano con BD propia), [`hub-frontends`](https://github.com/benjaminAndaur/hub-frontends).

## Persistencia de datos — Database per Service

A diferencia del resto de los módulos del Hub (que comparten la base de datos `asdf_db`), `modulo_facturacion` tiene **su propia base de datos PostgreSQL aislada** (`facturacion_db`, contenedor `db-facturacion`). Esto implementa el patrón **Database per Service**: este microservicio es el único dueño de su esquema, nadie más puede leer o escribir directamente sobre él.

- Motor: PostgreSQL 15.
- Acceso: exclusivamente vía SQLAlchemy 2.0 async + asyncpg, desde la capa `src/repository`.
- Schema inicial: [`hub-infra/db_facturacion/init.sql`](https://github.com/benjaminAndaur/hub-infra/blob/main/db_facturacion/init.sql) (tabla `facturas` y datos semilla). El ORM además ejecuta `Base.metadata.create_all()` al arrancar como red de seguridad.
- Variable de entorno: `DATABASE_URL=postgresql+asyncpg://admin:admin123@db-facturacion:5432/facturacion_db`.
- Sin FK hacia otros módulos: el campo `cliente` se guarda como texto, sin referencia a la tabla `clientes` de `modulo_acreditacion`. No hay integridad referencial entre microservicios, por diseño, para permitir despliegue e infraestructura de datos independientes.

El endpoint `GET /api/v1/facturacion/health` reporta el estado de la conexión a su propia base de datos (`db_status: "connected" | "error"`), evidenciando que la gestiona de forma independiente.

## Capas

```
main.py                                # entrypoint Quart; inyecta repo/service/sesión en g{}
src/
  models/factura_db.py                 # ORM SQLAlchemy (FacturaDB)
  repository/factura_repository.py     # acceso a datos async, sin lógica de negocio
  service/factura_service.py           # lógica de negocio + DTOs Pydantic
  controller/factura_controller.py     # Blueprint Quart, valida y expone endpoints
  utils/auth.py                        # decoradores @login_required y @require_permission
```

## Cómo ejecutar

**Standalone:**
```bash
git clone https://github.com/benjaminAndaur/hub-ms-facturacion.git
cd hub-ms-facturacion
pip install -r requirements.txt

export DATABASE_URL=postgresql+asyncpg://admin:admin123@localhost:5432/facturacion_db
export JWT_SECRET=super-secret-key-123

uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

**Stack completo:** clonar este repo como hermano de `hub-infra`, `hub-backends` y `hub-frontends` (mismo directorio padre), luego desde `hub-infra` ejecutar `docker-compose up --build` (levanta `db-facturacion` automáticamente).

## Cómo probar

```bash
# Health-check (público)
curl http://localhost:8080/api/v1/facturacion/health

# Con JWT (requiere login previo en /api/v1/administracion/login)
curl -H "Authorization: Bearer <token>" http://localhost:8080/api/v1/facturacion/facturas
```

## Endpoints

| Método | Ruta | Permiso |
|---|---|---|
| GET | `/api/v1/facturacion/health` | público |
| POST | `/api/v1/facturacion/facturas` | `facturacion:edit` |
| GET | `/api/v1/facturacion/facturas` | `facturacion:view` |
| GET | `/api/v1/facturacion/facturas/<id>` | `facturacion:view` |
| PUT | `/api/v1/facturacion/facturas/<id>` | `facturacion:edit` |
| DELETE | `/api/v1/facturacion/facturas/<id>` | `facturacion:edit` |
