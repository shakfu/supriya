.PHONY: build build-scsynth clean demos docs docs-clean help install-scsynth lint mypy pytest reformat test test-scsynth
.DEFAULT_GOAL := help

project = supriya
origin := $(shell git config --get remote.origin.url)
formatPaths = src/${project}/ docs/ examples/ tests/ *.py
mypyPaths = src/${project}/ examples/ tests/
testPaths = src/${project}/ tests/

help: ## This help
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-30s\033[0m %s\n", $$1, $$2}'

build: ## Build wheel via uv
	uv build

build-scsynth: ## Build wheel with embedded libscsynth
	uv build -C cmake.define.SUPRIYA_EMBED_SCSYNTH=ON

install-scsynth: ## Install editable with embedded libscsynth
	uv pip install -e . -C cmake.define.SUPRIYA_EMBED_SCSYNTH=ON

demos: ## Run all demo scripts sequentially
	@for f in demos/0*.py demos/1*.py; do \
		echo "=== $$f ==="; \
		uv run python "$$f"; \
		echo; \
	done

clean: ## Clean-out transitory files
	find . -name '*.pyc' | xargs rm
	find . -name '.ipynb_checkpoints' | xargs rm -Rf
	rm -Rif *.egg-info/
	rm -Rif .*cache/
	rm -Rif __pycache__
	rm -Rif build/
	rm -Rif dist/
	rm -Rif htmlcov/
	rm -Rif prof/
	rm -Rif wheelhouse/

docs: ## Build documentation
	make -C docs/ html

docs-clean: ## Build documentation from scratch
	make -C docs/ clean html

lint: reformat ruff-lint mypy ## Run all linters

mypy: ## Type-check via mypy
	uv run mypy ${mypyPaths}

mypy-cov: ## Type-check via mypy with coverage reported to ./mypycov/
	uv run mypy --html-report ./mypycov/ ${mypyPaths}

mypy-strict: ## Type-check via mypy strictly
	uv run mypy --strict ${mypyPaths}

pytest: ## Unit test via pytest
	uv run pytest ${testPaths} --cov=supriya

test: ## Run tests via uv
	uv run pytest tests/

test-scsynth: ## Run tests using venv directly (after make install-scsynth)
	.venv/bin/python -m pytest tests/ \
		--ignore=tests/book \
		--ignore=tests/contexts/test_Scope.py \
		--ignore=tests/contexts/test_Server_buffers.py \
		--ignore=tests/contexts/test_Server_buses.py \
		--ignore=tests/contexts/test_Server_misc.py \
		--ignore=tests/contexts/test_Server_nodes.py \
		--ignore=tests/contexts/test_Server_synthdefs.py \
		--ignore=tests/patterns \
		--ignore=tests/test_examples.py

reformat: ruff-imports-fix ruff-format-fix ## Reformat codebase

ruff-format: ## Lint via ruff
	uv run ruff format --check --diff ${formatPaths}

ruff-format-fix: ## Lint via ruff
	uv run ruff format ${formatPaths}

ruff-imports: ## Format imports via ruff
	uv run ruff check --select I,RUF022 ${formatPaths}

ruff-imports-fix: ## Format imports via ruff
	uv run ruff check --select I,RUF022 --fix ${formatPaths}

ruff-lint: ## Lint via ruff
	uv run ruff check --diff ${formatPaths}

ruff-lint-fix: ## Lint via ruff
	uv run ruff check --fix ${formatPaths}
