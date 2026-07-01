# hub-ms-facturacion

Microservicio de Facturación del Hub Empresarial. Expone una API REST (Quart, async) para crear, listar, actualizar y eliminar facturas.

Repos relacionados: [`hub-infra`](https://github.com/benjaminAndaur/hub-infra) (nginx, docker-compose, base de datos), [`hub-backends`](https://github.com/benjaminAndaur/hub-backends) (resto de microservicios), [`hub-ms-operacion`](https://github.com/benjaminAndaur/hub-ms-operacion) (microservicio hermano con BD propia), [`hub-frontends`](https://github.com/benjaminAndaur/hub-frontends), [`hub-bff`](https://github.com/benjaminAndaur/hub-bff) (BFF en NestJS que agrega este microservicio + operación, protegido con Circuit Breaker).

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

---

## Despliegue en AWS — DevOps (ISY1101)

### Arquitectura en producción

```
ALB → /api/v1/bff/* → hub-bff (ECS, :3000) → hub-ms-facturacion (ECS, :5000)
                                                      ↓
                                           RDS facturacion_db (:5432, privado)
```

- **Cluster:** `hub-empresarial-cluster` (AWS ECS Fargate)
- **Imagen:** `720243276279.dkr.ecr.us-east-1.amazonaws.com/hub-ms-facturacion:<sha>`
- **Task Definition:** 256 CPU units / 512 MB RAM, role = `LabRole`
- **Base de datos:** RDS PostgreSQL `hub-empresarial-db`, base `facturacion_db` (aislada)

### Variables de entorno en producción (Task Definition ECS)

| Variable | Descripción |
|---|---|
| `DATABASE_URL` | endpoint RDS privado a `facturacion_db` |
| `JWT_SECRET` | inyectado vía Task Definition (no en código) |

### Pipeline CI/CD (GitHub Actions)

Push a `main` → `.github/workflows/deploy.yml`:
```
checkout → AWS credentials → ECR login → docker build (multietapa) → push ECR → update task-def → deploy ECS
```
- Duración: **~3m 31s**
- **3 imágenes en ECR** (3 pipeline runs): demuestra iteración real de desarrollo
- Tags: SHA del commit (`16a3b800...`) + `latest`

### Problema resuelto en producción

Al primer despliegue, `facturacion_db` no existía en RDS. Se resolvió conectando al motor `postgres` (maintenance DB) del mismo RDS para crear la base antes de que el servicio arranque. El microservicio ya incluye lógica de creación automática al startup (`Base.metadata.create_all()`).

### Verificar despliegue

```bash
curl http://hub-empresarial-alb-1969847223.us-east-1.elb.amazonaws.com/api/v1/facturacion/health
# {"status": "ok", "db_status": "connected"}
```
