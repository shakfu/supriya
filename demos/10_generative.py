"""
10 -- Algorithmic composition

A self-running generative piece (~15s). Multiple voices with random pitch
selection, variable rhythms, and fading dynamics. Uses demand-rate UGens
(Drand, Dseq, Duty) for server-side decision-making.
"""

import time

from supriya import DoneAction, Server, find_free_port
from supriya.ugens import (
    Demand,
    Drand,
    Dseq,
    Dust,
    EnvGen,
    Envelope,
    Impulse,
    LFNoise2,
    LPF,
    Out,
    Pan2,
    SinOsc,
    SynthDefBuilder,
)

# -- Demand-driven melodic voice -----------------------------------------------
# The server itself picks notes from a scale using Drand, triggered by Impulse.

# A minor pentatonic scale across two octaves (as MIDI -> Hz would be complex,
# just use Hz values directly)
SCALE_HZ = [
    220.0, 261.6, 293.7, 349.2, 392.0,   # A3 C4 D4 F4 G4
    440.0, 523.3, 587.3, 698.5, 784.0,    # A4 C5 D5 F5 G5
]

with SynthDefBuilder(
    amplitude=0.12, rate=4.0, gate=1
) as builder:
    # Demand-rate: pick random pitches from the scale
    freq = Demand.kr(
        trigger=Impulse.kr(frequency=builder["rate"]),
        reset=0,
        source=Drand.dr(sequence=SCALE_HZ, repeats=1000),
    )
    sig = SinOsc.ar(frequency=freq) * builder["amplitude"]
    # Gentle wandering pan
    pan = LFNoise2.kr(frequency=0.3)
    env = EnvGen.kr(
        envelope=Envelope.asr(attack_time=2.0, sustain=1.0, release_time=2.0),
        gate=builder["gate"],
        done_action=DoneAction.FREE_SYNTH,
    )
    out = Pan2.ar(source=sig * env, position=pan)
    Out.ar(bus=0, source=out)
demand_voice_def = builder.build(name="demand_voice")

# -- Rhythmic pulse voice (sequenced rhythm, random pitch) ---------------------

BASS_HZ = [110.0, 130.8, 146.8, 164.8, 196.0]
RHYTHM = [0.25, 0.25, 0.5, 0.25, 0.125, 0.125, 0.5]

with SynthDefBuilder(amplitude=0.15, gate=1) as builder:
    trig = Impulse.kr(frequency=3.0)
    freq = Demand.kr(
        trigger=trig,
        reset=0,
        source=Drand.dr(sequence=BASS_HZ, repeats=1000),
    )
    sig = SinOsc.ar(frequency=freq)
    # Add a sub-octave for warmth
    sig = sig + SinOsc.ar(frequency=freq * 0.5) * 0.5
    sig = LPF.ar(source=sig, frequency=600)
    env = EnvGen.kr(
        envelope=Envelope.asr(attack_time=1.5, sustain=1.0, release_time=2.0),
        gate=builder["gate"],
        done_action=DoneAction.FREE_SYNTH,
    )
    Out.ar(bus=0, source=[sig * env * builder["amplitude"]] * 2)
bass_voice_def = builder.build(name="bass_demand")

# -- Sparse texture (Dust-triggered sine pings) --------------------------------

with SynthDefBuilder(amplitude=0.08, gate=1) as builder:
    trig = Dust.kr(density=2.0)
    freq = Demand.kr(
        trigger=trig,
        reset=0,
        source=Drand.dr(
            sequence=[880.0, 1046.5, 1174.7, 1318.5, 1568.0],
            repeats=1000,
        ),
    )
    sig = SinOsc.ar(frequency=freq) * builder["amplitude"]
    # Quick percussive decay per trigger
    ping_env = EnvGen.kr(
        envelope=Envelope.percussive(attack_time=0.005, release_time=0.3),
        gate=trig,
    )
    pan = LFNoise2.kr(frequency=0.5)
    master_env = EnvGen.kr(
        envelope=Envelope.asr(attack_time=1.0, sustain=1.0, release_time=1.5),
        gate=builder["gate"],
        done_action=DoneAction.FREE_SYNTH,
    )
    out = Pan2.ar(source=sig * ping_env * master_env, position=pan)
    Out.ar(bus=0, source=out)
ping_voice_def = builder.build(name="ping_voice")

# -- Boot and play -------------------------------------------------------------

print("Booting embedded server...")
server = Server(embedded=True)
server.boot(port=find_free_port())
print("Server online.")

with server.at():
    server.add_synthdefs(demand_voice_def, bass_voice_def, ping_voice_def)
time.sleep(0.3)

# Stagger the voices in
print("Generative piece starting...")

print("  Voice 1: demand-driven melody")
with server.at():
    v1 = server.add_synth(demand_voice_def, amplitude=0.12, rate=3.5)
time.sleep(2.0)

print("  Voice 2: bass pulses")
with server.at():
    v2 = server.add_synth(bass_voice_def, amplitude=0.12)
time.sleep(2.0)

print("  Voice 3: sparse pings")
with server.at():
    v3 = server.add_synth(ping_voice_def, amplitude=0.08)
time.sleep(6.0)

# Start fading voices out
print("Fading out...")
with server.at():
    v3.set(gate=0)
time.sleep(2.0)
with server.at():
    v2.set(gate=0)
time.sleep(1.5)
with server.at():
    v1.set(gate=0)
time.sleep(2.5)

print("Done.")
server.quit()
