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
- `patches/sc-reentrant-world.patch` for patching SuperCollider `Version-3.14.1` to support re-entrant `World_New`/`World_Cleanup` cycles (required for embedded server testing)

### Fixed
- `BaseServer.__repr__` no longer crashes in embedded mode when `Options.serialize()` raises `RuntimeError`
- `Server._lifecycle` / `AsyncServer._lifecycle` wrapped with try/except to prevent silent thread/task death leaving futures unset (causing infinite hangs)
- `ServerCannotBoot` handler now sets `shutdown_future` to prevent hang in `boot()` when it awaits the shutdown result
- Embedded World lifecycle segfaults after ~3-5 boot/quit cycles, caused by three SC global state issues:
  - Network port (`SC_UdpInPort`/`SC_TcpInPort`) pointers leaked on each cycle; stale ASIO handlers fire against freed World
  - CoreAudio device listener callback not removed in `DriverStop()`, leaving dangling pointer after driver deletion
  - `gLibInitted` static flag never reset after `deinitialize_library()`, preventing plugin reload on subsequent `World_New`

### Changed
- CI now builds against SuperCollider `Version-3.14.1` (pinned tag) instead of `develop`
- CI build actions apply `sc-reentrant-world.patch` after cloning SuperCollider
- Lifecycle tests updated to use `find_free_port()` per test for embedded mode to avoid UDP port conflicts between sequential embedded World instances

### Known Issues
- `libc++abi: terminating` at process exit after embedded tests is a known SC atexit handler issue (does not affect test results)
