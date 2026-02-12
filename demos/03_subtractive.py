"""
03 -- Filtering noise and saws

Subtractive synthesis: a sawtooth through a sweeping low-pass filter,
then white noise through a resonant filter modulated by an LFO.
"""

import time

from supriya import DoneAction, Server, find_free_port
from supriya.ugens import (
    EnvGen,
    Envelope,
    LFSaw,
    LPF,
    Out,
    Pan2,
    RLPF,
    Saw,
    SynthDefBuilder,
    WhiteNoise,
    XLine,
)

# -- Filtered saw with sweeping cutoff ----------------------------------------

with SynthDefBuilder(amplitude=0.2) as builder:
    sig = Saw.ar(frequency=110) * builder["amplitude"]
    cutoff = XLine.kr(start=5000, stop=300, duration=4.0)
    filtered = LPF.ar(source=sig, frequency=cutoff)
    env = EnvGen.kr(
        envelope=Envelope.linen(attack_time=0.1, sustain_time=3.5, release_time=0.4),
        done_action=DoneAction.FREE_SYNTH,
    )
    Out.ar(bus=0, source=[filtered * env, filtered * env])
sweep_def = builder.build(name="saw_sweep")

# -- Resonant noise with LFO-modulated cutoff ---------------------------------

with SynthDefBuilder(amplitude=0.15) as builder:
    sig = WhiteNoise.ar() * builder["amplitude"]
    lfo = LFSaw.kr(frequency=0.3)
    # Map LFO (-1..1) to cutoff range (200..4000)
    cutoff = lfo * 1900 + 2100
    filtered = RLPF.ar(source=sig, frequency=cutoff, reciprocal_of_q=0.1)
    env = EnvGen.kr(
        envelope=Envelope.linen(attack_time=0.5, sustain_time=4.0, release_time=0.5),
        done_action=DoneAction.FREE_SYNTH,
    )
    out = Pan2.ar(source=filtered * env, position=0.0)
    Out.ar(bus=0, source=out)
noise_def = builder.build(name="res_noise")

# -- Boot and play -------------------------------------------------------------

print("Booting embedded server...")
server = Server(embedded=True)
server.boot(port=find_free_port())
print("Server online.")

with server.at():
    server.add_synthdefs(sweep_def, noise_def)
time.sleep(0.2)

print("Sawtooth with sweeping LPF cutoff (4s)...")
with server.at():
    server.add_synth(sweep_def, amplitude=0.2)
time.sleep(4.5)

print("White noise through resonant filter with LFO (5s)...")
with server.at():
    server.add_synth(noise_def, amplitude=0.15)
time.sleep(5.5)

print("Done.")
server.quit()
