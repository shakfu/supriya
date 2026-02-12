import asyncio
import shutil

import pytest
import pytest_asyncio

import supriya
from supriya import scsynth
from supriya.contexts.realtime import BaseServer


pytest_plugins = ["sphinx.testing.fixtures"]

try:
    scsynth.find()
    _has_scsynth_exe = True
except RuntimeError:
    _has_scsynth_exe = False

_has_supernova_exe = shutil.which("supernova") is not None

try:
    from supriya import sclang

    sclang.find()
    _has_sclang_exe = True
except RuntimeError:
    _has_sclang_exe = False

_skip_no_scsynth_exe = pytest.mark.skipif(
    not _has_scsynth_exe, reason="scsynth executable not found"
)

_skip_no_supernova_exe = pytest.mark.skipif(
    not _has_supernova_exe, reason="supernova executable not found"
)

_skip_no_sclang_exe = pytest.mark.skipif(
    not _has_sclang_exe, reason="sclang executable not found"
)


@pytest.fixture
def server():
    server = supriya.Server()
    server.set_latency(0.0)
    server.boot()
    server.add_synthdefs(supriya.default)
    server.sync()
    yield server
    server.quit()


@pytest.fixture(scope="module")
def persistent_server():
    server = supriya.Server()
    server.set_latency(0.0)
    server.boot()
    yield server
    server.quit()


@pytest.fixture(autouse=True)
def add_libraries(doctest_namespace):
    doctest_namespace["supriya"] = supriya


@pytest.fixture(autouse=True, scope="session")
def shutdown_scsynth():
    scsynth.kill()
    yield
    scsynth.kill()


@pytest_asyncio.fixture(autouse=True)
async def shutdown_realtime_contexts(shutdown_scsynth):
    for context in tuple(BaseServer._contexts):
        result = context._shutdown()
        if asyncio.iscoroutine(result):
            await result
    yield
    for context in tuple(BaseServer._contexts):
        result = context._shutdown()
        if asyncio.iscoroutine(result):
            await result
