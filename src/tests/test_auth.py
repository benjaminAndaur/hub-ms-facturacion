import jwt
import pytest
from datetime import datetime, timedelta
from quart import Quart
from src.utils.auth import login_required, require_permission, SECRET_KEY, ALGORITHM


def make_app():
    app = Quart(__name__)

    @app.route('/protegido')
    @login_required
    async def protegido():
        return {"ok": True}

    @app.route('/solo-edit')
    @login_required
    @require_permission('facturacion', 'edit')
    async def solo_edit():
        return {"ok": True}

    return app


@pytest.fixture
def app():
    return make_app()


def make_token(permisos=None, expired=False):
    payload = {
        "sub": "1",
        "email": "user@asdf.cl",
        "permisos": permisos or {},
        "exp": datetime.utcnow() + (timedelta(minutes=-5) if expired else timedelta(minutes=5)),
    }
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)


@pytest.mark.asyncio
async def test_login_required_without_token_returns_401(app):
    # Arrange
    client = app.test_client()

    # Act
    response = await client.get('/protegido')

    # Assert
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_login_required_with_malformed_header_returns_401(app):
    # Arrange
    client = app.test_client()

    # Act
    response = await client.get('/protegido', headers={"Authorization": "Bearer"})

    # Assert
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_login_required_with_valid_token_allows_access(app):
    # Arrange
    client = app.test_client()
    token = make_token()

    # Act
    response = await client.get('/protegido', headers={"Authorization": f"Bearer {token}"})

    # Assert
    assert response.status_code == 200


@pytest.mark.asyncio
async def test_login_required_with_expired_token_returns_401(app):
    # Arrange
    client = app.test_client()
    token = make_token(expired=True)

    # Act
    response = await client.get('/protegido', headers={"Authorization": f"Bearer {token}"})

    # Assert
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_login_required_with_invalid_token_returns_401(app):
    # Arrange
    client = app.test_client()

    # Act
    response = await client.get('/protegido', headers={"Authorization": "Bearer not-a-real-token"})

    # Assert
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_require_permission_with_edit_allows_access(app):
    # Arrange
    client = app.test_client()
    token = make_token(permisos={"facturacion": "edit"})

    # Act
    response = await client.get('/solo-edit', headers={"Authorization": f"Bearer {token}"})

    # Assert
    assert response.status_code == 200


@pytest.mark.asyncio
async def test_require_permission_with_view_only_returns_403(app):
    # Arrange
    client = app.test_client()
    token = make_token(permisos={"facturacion": "view"})

    # Act
    response = await client.get('/solo-edit', headers={"Authorization": f"Bearer {token}"})

    # Assert
    assert response.status_code == 403


@pytest.mark.asyncio
async def test_require_permission_without_module_permission_returns_403(app):
    # Arrange
    client = app.test_client()
    token = make_token(permisos={})

    # Act
    response = await client.get('/solo-edit', headers={"Authorization": f"Bearer {token}"})

    # Assert
    assert response.status_code == 403
