"""
09 -- Chaotic oscillators

Use HenonL and LorenzL as audio sources. Mix with Dust-triggered Ringz
resonators for metallic textures. Filter and pan the result.
"""

import time

from supriya import DoneAction, Server, find_free_port
from supriya.ugens import (
    Dust,
    EnvGen,
    Envelope,
    HenonL,
    LFNoise1,
    LPF,
    LorenzL,
    Out,
    Pan2,
    Ringz,
    SynthDefBuilder,
)

# -- Henon map oscillator ------------------------------------------------------

with SynthDefBuilder(amplitude=0.1, gate=1) as builder:
    # HenonL produces output in roughly -1.5..1.5 range
    chaos = HenonL.ar(frequency=11025, a=1.3, b=0.3)
    filtered = LPF.ar(source=chaos * 0.3, frequency=3000)
    env = EnvGen.kr(
        envelope=Envelope.asr(attack_time=0.5, sustain=1.0, release_time=1.0),
        gate=builder["gate"],
        done_action=DoneAction.FREE_SYNTH,
    )
    out = Pan2.ar(
        source=filtered * env * builder["amplitude"], position=-0.4
    )
    Out.ar(bus=0, source=out)
henon_def = builder.build(name="henon")

# -- Lorenz attractor ----------------------------------------------------------

with SynthDefBuilder(amplitude=0.08, gate=1) as builder:
    chaos = LorenzL.ar(frequency=11025, s=10, r=28, b=2.667, h=0.05)
    filtered = LPF.ar(source=chaos * 0.5, frequency=4000)
    env = EnvGen.kr(
        envelope=Envelope.asr(attack_time=0.5, sustain=1.0, release_time=1.0),
        gate=builder["gate"],
        done_action=DoneAction.FREE_SYNTH,
    )
    out = Pan2.ar(
        source=filtered * env * builder["amplitude"], position=0.4
    )
    Out.ar(bus=0, source=out)
lorenz_def = builder.build(name="lorenz")

# -- Dust-triggered resonators -------------------------------------------------

with SynthDefBuilder(amplitude=0.1, gate=1) as builder:
    dust = Dust.ar(density=3.0)
    # Parallel resonators at different frequencies
    freq1 = LFNoise1.kr(frequency=0.2) * 500 + 1200
    freq2 = LFNoise1.kr(frequency=0.15) * 400 + 2500
    ring1 = Ringz.ar(source=dust, frequency=freq1, decay_time=0.15)
    ring2 = Ringz.ar(source=dust, frequency=freq2, decay_time=0.1)
    sig = (ring1 + ring2) * 0.15
    env = EnvGen.kr(
        envelope=Envelope.asr(attack_time=0.3, sustain=1.0, release_time=0.5),
        gate=builder["gate"],
        done_action=DoneAction.FREE_SYNTH,
    )
    out = Pan2.ar(source=sig * env * builder["amplitude"], position=0.0)
    Out.ar(bus=0, source=out)
ring_def = builder.build(name="dust_ringz")

# -- Boot and play -------------------------------------------------------------

print("Booting embedded server...")
server = Server(embedded=True)
server.boot(port=find_free_port())
print("Server online.")

with server.at():
    server.add_synthdefs(henon_def, lorenz_def, ring_def)
time.sleep(0.3)

# Layer 1: Henon
print("Henon chaotic oscillator...")
with server.at():
    h = server.add_synth(henon_def, amplitude=0.1)
time.sleep(2.0)

# Layer 2: add Lorenz
print("Adding Lorenz attractor...")
with server.at():
    l = server.add_synth(lorenz_def, amplitude=0.08)
time.sleep(2.0)

# Layer 3: add resonators
print("Adding Dust-triggered resonators...")
with server.at():
    r = server.add_synth(ring_def, amplitude=0.1)
time.sleep(4.0)

# Fade out in reverse order
print("Fading out...")
with server.at():
    r.set(gate=0)
time.sleep(1.0)
with server.at():
    l.set(gate=0)
time.sleep(1.0)
with server.at():
    h.set(gate=0)
time.sleep(1.5)

print("Done.")
server.quit()
