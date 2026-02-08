# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- Embedded scsynth server support via `_scsynth` nanobind extension wrapping libscsynth
- `EmbeddedProcessProtocol` in `scsynth.py` for in-process World lifecycle management
- `_active_world` class-level guard preventing multiple concurrent embedded Worlds (SC limitation)
- Embedded parametrization for lifecycle tests: boot, quit, reboot, connect, and error-handling scenarios
- `SERVER_PARAMS` in test conftest with embedded variants for `AsyncServer` and `Server`

### Fixed
- `BaseServer.__repr__` no longer crashes in embedded mode when `Options.serialize()` raises `RuntimeError`
- `Server._lifecycle` / `AsyncServer._lifecycle` wrapped with try/except to prevent silent thread/task death leaving futures unset (causing infinite hangs)
- `ServerCannotBoot` handler now sets `shutdown_future` to prevent hang in `boot()` when it awaits the shutdown result

### Changed
- Lifecycle tests updated to use `find_free_port()` per test for embedded mode to avoid UDP port conflicts between sequential embedded World instances

### Known Issues
- Embedded multi-client tests skipped: SC's `World_Cleanup` corrupts global C runtime state when the World is destroyed with registered UDP clients, causing segfaults on subsequent World creation
- Embedded reboot test (`test_boot_reboot_sticky_options`) skipped: cumulative World create/destroy cycles degrade SC global state after ~20+ lifecycles per process
- `libc++abi: terminating` at process exit after embedded tests is a known SC atexit handler issue (does not affect test results)
