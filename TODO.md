# TODO: Skip missing-binary tests + Fix embedded segfault

## Status: In Progress

## Completed

### Part 1: Skip missing-binary tests

- [x] `tests/conftest.py` -- added `_skip_no_sclang_exe` marker (sclang detection)
- [x] 10 ugen test files -- added `@_skip_no_sclang_exe` to all `*_vs_sclang` functions
  - `test_SynthDef_basic.py` (5 functions)
  - `test_SynthDef_parameters.py` (5 functions)
  - `test_SynthDef_system.py` (`test_sclang`)
  - `test_SynthDef_mfcc.py` (3 functions)
  - `test_SynthDef_ambisonics.py` (1 function)
  - `test_SynthDef_demand.py` (1 function)
  - `test_SynthDef_expansion.py` (1 function)
  - `test_SynthDef_optimization.py` (1 function)
  - `test_SynthDef_rngs.py` (1 function)
  - `test_SynthDef_width_first.py` (1 function)
- [x] `tests/test_scsynth.py` -- `@_skip_no_scsynth_exe` on `test_Options`
- [x] `tests/test_osc.py` -- `@_skip_no_scsynth_exe` on `test_OscProtocol`
- [x] `tests/book/test_ext_book.py` -- `pytest.importorskip("librosa")`
- [x] `tests/contexts/test_ServerSHM.py` -- xfail embedded param

### Part 2: Fix embedded segfault in test_Server_misc (and siblings)

- [x] `tests/contexts/test_Server_misc.py` -- added `quit()` + `find_free_port()` to fixture
- [x] `tests/contexts/test_Server_buffers.py` -- same fix
- [x] `tests/contexts/test_Server_buses.py` -- same fix
- [x] `tests/contexts/test_Server_nodes.py` -- same fix
- [x] `tests/contexts/test_Server_synthdefs.py` -- same fix

### Part 3: Fix full-suite segfault (leaked `serve_forever` threads)

- [x] Root-caused: `OscProtocol.disconnect()` skipped cleanup when status was
  `BOOTING` (not yet `ONLINE`), leaking `serve_forever` UDP threads
- [x] Fixed `ThreadedOscProtocol.disconnect()` in `src/supriya/osc.py:1124`
- [x] Fixed `AsyncOscProtocol.disconnect()` in `src/supriya/osc.py:1327`

**Root cause details:**

The segfault was triggered by `test_boot_a_and_connect_b_too_many_clients` in
`test_Server_lifecycle.py`. That test boots server A (embedded, `maximum_logins=1`),
then has server B call `connect()` to the same port. B's OSC protocol starts a
`serve_forever` UDP thread, sends `/notify`, gets rejected ("too many clients"),
and the lifecycle calls `osc_protocol.disconnect()`. But `disconnect()` checked
`self.status != BootStatus.ONLINE` and returned early -- the protocol was still in
`BOOTING` because the healthcheck hadn't promoted it to `ONLINE` yet. The
`serve_forever` thread was never stopped.

Each `too_many_clients` test (AsyncServer + Server params) leaked one thread.
These zombie `serve_forever` threads accumulated and eventually caused a
segfault/SIGABRT in `World_New` or `World_WaitForQuit` during subsequent embedded
world creation.

**Fix:** Changed the guard in both `disconnect()` methods from
`self.status != BootStatus.ONLINE` to
`self.status not in (BootStatus.ONLINE, BootStatus.BOOTING)`, so the
`serve_forever` thread is properly shut down even when the connection fails before
reaching `ONLINE` status.

**Verification:** Full `make test` completes without segfault. 430 passed,
318 skipped, 32 failed (all pre-existing), 1 xfailed.

## Remaining

### Pre-existing failures (not caused by these changes)

- `test_Score_buffers.py::test_add_buffer` / `test_read_buffer` -- `audio_paths`
  is empty (no `bird*.wav` files in `supriya/samples/`)
- Embedded tests that create synths fail with "UGen 'Control' not installed"
  (plugin path issue -- `find_ugen_plugins_path()` not finding plugins directory)
- `test_query_version` fails for embedded (calls `scsynth.find()`, no exe on PATH)
- `test_reboot` fails for embedded (port reuse within the test body)
- `test_Buffer_allocated` / `test_Node_allocated` fail for embedded
  (`ServerCannotBoot` -- internal `quit()` + `boot()` without `find_free_port()`)
- Various embedded node/bus tests fail because synths can't be created without
  UGen plugins (downstream of the "Control not installed" issue)
