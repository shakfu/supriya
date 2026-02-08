import logging

import pytest

from supriya import AsyncServer, Server
from supriya.enums import ParameterRate
from supriya.ugens import Out, Parameter, SinOsc, SynthDef, SynthDefBuilder

try:
    import supriya._scsynth  # noqa: F401

    _has_scsynth_ext = True
except ImportError:
    _has_scsynth_ext = False

_skip_no_scsynth = pytest.mark.skipif(
    not _has_scsynth_ext, reason="_scsynth extension not available"
)

SERVER_PARAMS = [
    pytest.param((AsyncServer, False), id="AsyncServer"),
    pytest.param((Server, False), id="Server"),
    pytest.param(
        (AsyncServer, True), id="AsyncServer-embedded", marks=_skip_no_scsynth
    ),
    pytest.param((Server, True), id="Server-embedded", marks=_skip_no_scsynth),
]


@pytest.fixture(autouse=True)
def capture_logs(caplog):
    caplog.set_level(logging.INFO, logger="supriya")


@pytest.fixture
def two_voice_synthdef() -> SynthDef:
    with SynthDefBuilder(
        frequencies=(220, 440),
        amplitude=Parameter(value=1.0, rate=ParameterRate.AUDIO),
    ) as builder:
        sin_osc = SinOsc.ar(frequency=builder["frequencies"])
        enveloped_sin = sin_osc * builder["amplitude"]
        Out.ar(bus=0, source=enveloped_sin)
    return builder.build(name="test:two-voice")
