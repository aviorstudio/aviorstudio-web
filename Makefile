.DEFAULT_GOAL := help
.PHONY: help install lint test build check dev stop clean
help:
	@echo 'make install  Install frozen dependencies with the pinned Bun toolchain'
	@echo 'make check    Type-check, build and verify every static output assertion'
	@echo 'make dev      Run the foreground Astro development server'
install:
	mise exec -- bun install --frozen-lockfile
lint:
	mise exec -- bun x --no-install biome check
build:
	mise exec -- bun run typecheck
	mise exec -- bun run build
test: lint
	python3 scripts/check-output.py
check: build test
dev:
	mise exec -- bun run dev
stop:
	@echo 'stop: unsupported: press Ctrl-C in the foreground dev terminal'
clean:
	python3 -c 'import shutil; shutil.rmtree("dist", ignore_errors=True)'
