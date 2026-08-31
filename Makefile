.PHONY: install run-batch lint

install:
	python -m pip install -e ".[dev]"

run-batch:
	python -m fraud_service.batch

lint:
	ruff check src tests