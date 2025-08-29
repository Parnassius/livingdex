.venv.dir: uv.lock
	@uv sync
	@touch .venv.dir

.node_modules.dir: package-lock.json
	@npm ci
	@touch .node_modules.dir

.nuget.dir: packages.lock.json
	@rm -rf nuget
	@dotnet restore --packages nuget
	@cp nuget/pkhex.core/*/lib/net*/PKHeX.Core.dll .venv/lib/python*/site-packages
	@touch .nuget.dir

.PHONY: deps
deps: .venv.dir .node_modules.dir .nuget.dir

.PHONY: format
format:
	@uv run ruff check src tests --fix-only
	@uv run ruff format src tests
	@npx --no prettier src/livingdex/templates --write
	@npx --no @biomejs/biome check src --write

.PHONY: format-check
format-check:
	@uv run ruff format src tests --check
	@npx --no prettier src/livingdex/templates --check

.PHONY: mypy
mypy:
	@uv run mypy src tests

.PHONY: ruff
ruff:
	@uv run ruff check src tests

.PHONY: biome
biome:
	@npx --no @biomejs/biome ci --error-on-warnings src

.PHONY: pytest
pytest:
	@uv run pytest

.PHONY: lint
lint: format-check mypy ruff biome

.PHONY: all
all: format mypy ruff biome pytest

.DEFAULT_GOAL := all
