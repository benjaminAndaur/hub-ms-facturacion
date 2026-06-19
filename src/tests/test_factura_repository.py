import pytest
from unittest.mock import AsyncMock, MagicMock
from src.repository.factura_repository import FacturaRepository
from src.models.factura_db import FacturaDB
from datetime import datetime


@pytest.fixture
def mock_session():
    return AsyncMock()


@pytest.fixture
def repository(mock_session):
    return FacturaRepository(mock_session)


@pytest.mark.asyncio
async def test_check_db_health_executes_select_1(repository, mock_session):
    # Act
    result = await repository.check_db_health()

    # Assert
    mock_session.execute.assert_called_once()
    assert result is True


@pytest.mark.asyncio
async def test_create_adds_commits_and_refreshes(repository, mock_session):
    # Arrange
    factura = FacturaDB(cliente="A", total=100, estado="Emitida", fecha=datetime.utcnow())

    # Act
    result = await repository.create(factura)

    # Assert
    mock_session.add.assert_called_once_with(factura)
    mock_session.commit.assert_called_once()
    mock_session.refresh.assert_called_once_with(factura)
    assert result is factura


@pytest.mark.asyncio
async def test_get_all_returns_list(repository, mock_session):
    # Arrange
    expected = [FacturaDB(id=1, cliente="A", total=100, estado="Emitida", fecha=datetime.utcnow())]
    scalars_mock = MagicMock()
    scalars_mock.all.return_value = expected
    execute_result = MagicMock()
    execute_result.scalars.return_value = scalars_mock
    mock_session.execute.return_value = execute_result

    # Act
    result = await repository.get_all()

    # Assert
    assert result == expected


@pytest.mark.asyncio
async def test_get_by_id_returns_match(repository, mock_session):
    # Arrange
    expected = FacturaDB(id=1, cliente="A", total=100, estado="Emitida", fecha=datetime.utcnow())
    mock_session.get.return_value = expected

    # Act
    result = await repository.get_by_id(1)

    # Assert
    assert result is expected
    mock_session.get.assert_called_once_with(FacturaDB, 1)


@pytest.mark.asyncio
async def test_get_by_id_returns_none_when_missing(repository, mock_session):
    # Arrange
    mock_session.get.return_value = None

    # Act
    result = await repository.get_by_id(999)

    # Assert
    assert result is None


@pytest.mark.asyncio
async def test_update_sets_attributes_and_commits(repository, mock_session):
    # Arrange
    factura = FacturaDB(id=1, cliente="A", total=100, estado="Emitida", fecha=datetime.utcnow())
    mock_session.get.return_value = factura

    # Act
    result = await repository.update(1, {"estado": "Pagada"})

    # Assert
    assert result.estado == "Pagada"
    mock_session.commit.assert_called_once()
    mock_session.refresh.assert_called_once_with(factura)


@pytest.mark.asyncio
async def test_update_ignores_unknown_attributes(repository, mock_session):
    # Arrange
    factura = FacturaDB(id=1, cliente="A", total=100, estado="Emitida", fecha=datetime.utcnow())
    mock_session.get.return_value = factura

    # Act
    result = await repository.update(1, {"campo_inexistente": "x"})

    # Assert
    assert not hasattr(result, "campo_inexistente") or result.campo_inexistente != "x"
    mock_session.commit.assert_called_once()


@pytest.mark.asyncio
async def test_update_returns_none_when_not_found(repository, mock_session):
    # Arrange
    mock_session.get.return_value = None

    # Act
    result = await repository.update(999, {"estado": "Pagada"})

    # Assert
    assert result is None
    mock_session.commit.assert_not_called()


@pytest.mark.asyncio
async def test_delete_returns_true_when_found(repository, mock_session):
    # Arrange
    factura = FacturaDB(id=1, cliente="A", total=100, estado="Emitida", fecha=datetime.utcnow())
    mock_session.get.return_value = factura

    # Act
    result = await repository.delete(1)

    # Assert
    mock_session.delete.assert_called_once_with(factura)
    mock_session.commit.assert_called_once()
    assert result is True


@pytest.mark.asyncio
async def test_delete_returns_false_when_not_found(repository, mock_session):
    # Arrange
    mock_session.get.return_value = None

    # Act
    result = await repository.delete(999)

    # Assert
    assert result is False
    mock_session.commit.assert_not_called()
