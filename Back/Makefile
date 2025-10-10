PYTHON=python
PYTEST=$(PYTHON) -m pytest
TEST_DIR=testing
SRC_DIR=src

# Target por defecto
default: test

# Correr TODOS los tests
test:
	$(PYTEST) -q $(TEST_DIR)

# Unit tests
unit:
	$(PYTEST) -q $(TEST_DIR)/unit

# Integration tests
integration:
	$(PYTEST) -q $(TEST_DIR)/integration

# End-to-end tests
e2e:
	$(PYTEST) -q $(TEST_DIR)/e2e

# Tests con cobertura
coverage:
	$(PYTEST) --cov=$(SRC_DIR) --cov-report=term-missing $(TEST_DIR)

# Limpiar caches de python/pytest
clean:
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type d -name ".pytest_cache" -exec rm -rf {} +
	find . -type d -name ".coverage" -exec rm -rf {} +


