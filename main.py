import asyncio
import os
from quart import Quart, g
from quart_cors import cors
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from src.repository.factura_repository import FacturaRepository
from src.service.factura_service import FacturaService
from src.controller.factura_controller import create_factura_blueprint

app = Quart(__name__)
app = cors(app, allow_origin="*", allow_headers=["Content-Type", "Authorization"], allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"])

# Configuración Postgres Async (asyncpg)
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql+asyncpg://admin:admin123@localhost:5432/asdf_db")


_engine = None
_async_session = None
_loop = None

def get_async_session():
    global _engine, _async_session, _loop
    current_loop = asyncio.get_running_loop()
    if _async_session is None or _loop != current_loop:
        _engine = create_async_engine(DATABASE_URL, pool_size=10, max_overflow=20, pool_pre_ping=True, echo=False)
        _async_session = async_sessionmaker(_engine, expire_on_commit=False)
        _loop = current_loop
    return _async_session()


async def ensure_database_exists():
    """Crea la base de datos si no existe, conectando primero a 'operacion_db'."""
    import re
    # Extraer nombre de la BD objetivo y construir URL a operacion_db
    db_name = re.search(r'/(\w+)$', DATABASE_URL)
    if not db_name:
        return
    target_db = db_name.group(1)
    base_url = DATABASE_URL[:DATABASE_URL.rfind('/')] + '/operacion_db'
    try:
        import asyncpg
        dsn = base_url.replace('postgresql+asyncpg://', 'postgresql://')
        conn = await asyncpg.connect(dsn=dsn, timeout=10)
        exists = await conn.fetchval("SELECT 1 FROM pg_database WHERE datname=$1", target_db)
        if not exists:
            await conn.execute(f'CREATE DATABASE "{target_db}"')
            print(f"Base de datos '{target_db}' creada.")
        await conn.close()
    except Exception as e:
        print(f"Advertencia al verificar/crear BD: {e}")


@app.before_serving
async def setup_db():
    global _engine, _async_session, _loop
    current_loop = asyncio.get_running_loop()

    await ensure_database_exists()

    if _engine is None or _loop != current_loop:
        _engine = create_async_engine(DATABASE_URL, pool_size=10, max_overflow=20, pool_pre_ping=True, echo=False)
        _async_session = async_sessionmaker(_engine, expire_on_commit=False)
        _loop = current_loop

        from src.models.factura_db import Base

    retries = 10
    while retries > 0:
        try:
            async with _engine.begin() as conn:
                await conn.run_sync(Base.metadata.create_all)
            print("Successfully connected to database.")
            break
        except Exception as e:
            retries -= 1
            print(f"Database connection failed. Retrying... ({retries} left). Error: {e}")
            if retries == 0:
                raise e
            await asyncio.sleep(5)


@app.before_request
async def inject_dependencies():
    session = get_async_session()
    repo = FacturaRepository(session)
    service = FacturaService(repo)
    g.current_service = service
    g.current_session = session


@app.after_request
async def cleanup(response):
    if hasattr(g, 'current_session'):
        await g.current_session.close()
    return response


# Global Error Handler
@app.errorhandler(Exception)
async def handle_exception(e):
    # Log the error
    app.logger.error(f"Global error: {str(e)}")
    return {"error": "Internal Server Error", "message": str(e)}, 500

# Registrar blueprint
bp = create_factura_blueprint()

app.register_blueprint(bp, url_prefix='/api/v1/facturacion')
