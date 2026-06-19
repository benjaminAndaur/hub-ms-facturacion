# Guía de Pruebas — hub-ms-facturacion

## Cómo correr los tests

```bash
python -m venv .venv
.venv\Scripts\activate          # Windows
# source .venv/bin/activate     # Linux/Mac

pip install -r requirements.txt
pytest
```

`pytest.ini` ya corre con cobertura y falla si baja de 60%:

```ini
[pytest]
asyncio_mode = auto
addopts = --cov=src --cov-report=term-missing --cov-report=xml --cov-report=html --cov-fail-under=60
testpaths = src/tests
```

Estado actual: 28 tests, 86.9% de cobertura (`src/service`, `src/repository`, `src/utils/auth.py`). Los tests de `repository` mockean `AsyncSession` completo (sin BD real); los de `service` mockean el repositorio inyectado con `AsyncMock`.

Reporte HTML: `htmlcov/index.html`. Reporte para SonarQube: `coverage.xml`.

## SonarQube

Este repo tiene su propio `sonar-project.properties`. Para analizarlo, el SonarQube de `hub-infra` debe estar levantado (`docker-compose -f docker-compose.sonarqube.yml up -d` desde `hub-infra`) y este repo debe conectarse a la misma red Docker:

```bash
docker run --rm --network hub-infra_sonar-network \
  -v "$(pwd):/usr/src" \
  sonarsource/sonar-scanner-cli \
  -Dsonar.host.url=http://sonarqube:9000 \
  -Dsonar.token=<TU_TOKEN>
```

Ver `hub-backends/GUIA_PRUEBAS.md` para el detalle completo de cómo levantar SonarQube y generar el token.

## Nota sobre PyJWT y el claim `sub`

Si agregas tests que generen un JWT de prueba, el claim `sub` debe ser **string** (`"sub": "1"`, no `"sub": 1`) — PyJWT 2.10+ valida esto estrictamente y lanza `InvalidSubjectError` si no se cumple.
