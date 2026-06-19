import pytest
from unittest.mock import AsyncMock
from src.service.factura_service import FacturaService
from src.models.factura_db import FacturaDB
from datetime import datetime


@pytest.fixture
def mock_repo():
    return AsyncMock()


@pytest.fixture
def service(mock_repo):
    return FacturaService(mock_repo)


@pytest.mark.asyncio
async def test_check_db_health_returns_true_when_repo_succeeds(service, mock_repo):
    # Arrange
    mock_repo.check_db_health.return_value = True

    # Act
    result = await service.check_db_health()

    # Assert
    assert result is True


@pytest.mark.asyncio
async def test_check_db_health_returns_false_when_repo_raises(service, mock_repo):
    # Arrange
    mock_repo.check_db_health.side_effect = Exception("db down")

    # Act
    result = await service.check_db_health()

    # Assert
    assert result is False


@pytest.mark.asyncio
async def test_crear_factura_returns_response_dto(service, mock_repo):
    # Arrange
    data = {"cliente": "Minera Los Andes", "total": 1500000}
    mock_repo.create.return_value = FacturaDB(
        id=1, cliente="Minera Los Andes", total=1500000, estado="Emitida", fecha=datetime.utcnow()
    )

    # Act
    result = await service.crear_factura(data)

    # Assert
    assert result.id == 1
    assert result.cliente == "Minera Los Andes"
    assert result.total == 1500000
    mock_repo.create.assert_called_once()


@pytest.mark.asyncio
async def test_obtener_todas_returns_dtos(service, mock_repo):
    # Arrange
    mock_repo.get_all.return_value = [
        FacturaDB(id=1, cliente="A", total=100, estado="Emitida", fecha=datetime.utcnow()),
        FacturaDB(id=2, cliente="B", total=200, estado="Emitida", fecha=datetime.utcnow()),
    ]

    # Act
    result = await service.obtener_todas()

    # Assert
    assert len(result) == 2
    assert result[0].cliente == "A"
    assert result[1].cliente == "B"


@pytest.mark.asyncio
async def test_obtener_por_id_returns_dto_when_found(service, mock_repo):
    # Arrange
    mock_repo.get_by_id.return_value = FacturaDB(
        id=1, cliente="A", total=100, estado="Emitida", fecha=datetime.utcnow()
    )

    # Act
    result = await service.obtener_por_id(1)

    # Assert
    assert result is not None
    assert result.id == 1
    mock_repo.get_by_id.assert_called_once_with(1)


@pytest.mark.asyncio
async def test_obtener_por_id_returns_none_when_missing(service, mock_repo):
    # Arrange
    mock_repo.get_by_id.return_value = None

    # Act
    result = await service.obtener_por_id(999)

    # Assert
    assert result is None


@pytest.mark.asyncio
async def test_actualizar_factura_returns_dto_when_found(service, mock_repo):
    # Arrange
    mock_repo.update.return_value = FacturaDB(
        id=1, cliente="A", total=999, estado="Pagada", fecha=datetime.utcnow()
    )

    # Act
    result = await service.actualizar_factura(1, {"estado": "Pagada"})

    # Assert
    assert result.estado == "Pagada"
    mock_repo.update.assert_called_once_with(1, {"estado": "Pagada"})


@pytest.mark.asyncio
async def test_actualizar_factura_returns_none_when_missing(service, mock_repo):
    # Arrange
    mock_repo.update.return_value = None

    # Act
    result = await service.actualizar_factura(999, {"estado": "Pagada"})

    # Assert
    assert result is None


@pytest.mark.asyncio
async def test_eliminar_factura_delegates_to_repository(service, mock_repo):
    # Arrange
    mock_repo.delete.return_value = True

    # Act
    result = await service.eliminar_factura(1)

    # Assert
    assert result is True
    mock_repo.delete.assert_called_once_with(1)


@pytest.mark.asyncio
async def test_eliminar_factura_returns_false_when_not_found(service, mock_repo):
    # Arrange
    mock_repo.delete.return_value = False

    # Act
    result = await service.eliminar_factura(999)

    # Assert
    assert result is False
