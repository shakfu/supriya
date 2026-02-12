"""
04 -- Frequency modulation

Classic two-operator FM: a carrier SinOsc whose frequency is modulated
by another SinOsc. Sweep the modulation index, then play a short melody.
"""

import time

from supriya import DoneAction, Server, find_free_port
from supriya.ugens import (
    EnvGen,
    Envelope,
    Line,
    Out,
    Pan2,
    SinOsc,
    SynthDefBuilder,
    XLine,
)

# -- FM synthdef with controllable index ---------------------------------------

with SynthDefBuilder(
    carrier_freq=440,
    mod_ratio=2.0,
    mod_index=3.0,
    amplitude=0.2,
    pan=0.0,
    gate=1,
) as builder:
    mod_freq = builder["carrier_freq"] * builder["mod_ratio"]
    modulator = SinOsc.ar(frequency=mod_freq) * mod_freq * builder["mod_index"]
    carrier = SinOsc.ar(frequency=builder["carrier_freq"] + modulator)
    env = EnvGen.kr(
        envelope=Envelope.adsr(
            attack_time=0.01, decay_time=0.1, sustain=0.7, release_time=0.3
        ),
        gate=builder["gate"],
        done_action=DoneAction.FREE_SYNTH,
    )
    out = Pan2.ar(source=carrier * env * builder["amplitude"], position=builder["pan"])
    Out.ar(bus=0, source=out)
fm_def = builder.build(name="fm_synth")

# -- FM with sweeping index (self-freeing) ------------------------------------

with SynthDefBuilder(
    carrier_freq=220, mod_ratio=3.0, amplitude=0.2
) as builder:
    index = XLine.kr(start=0.1, stop=10.0, duration=5.0)
    mod_freq = builder["carrier_freq"] * builder["mod_ratio"]
    modulator = SinOsc.ar(frequency=mod_freq) * mod_freq * index
    carrier = SinOsc.ar(frequency=builder["carrier_freq"] + modulator)
    env = EnvGen.kr(
        envelope=Envelope.linen(attack_time=0.2, sustain_time=4.5, release_time=0.3),
        done_action=DoneAction.FREE_SYNTH,
    )
    Out.ar(bus=0, source=[carrier * env * builder["amplitude"]] * 2)
fm_sweep_def = builder.build(name="fm_sweep")

# -- Boot and play -------------------------------------------------------------

print("Booting embedded server...")
server = Server(embedded=True)
server.boot(port=find_free_port())
print("Server online.")

with server.at():
    server.add_synthdefs(fm_def, fm_sweep_def)
time.sleep(0.2)

print("FM sweep: modulation index 0.1 -> 10.0 over 5s...")
with server.at():
    server.add_synth(fm_sweep_def, carrier_freq=220, mod_ratio=3.0, amplitude=0.2)
time.sleep(5.5)

# Short FM melody
melody = [
    (330, 1.5, -0.4),
    (440, 2.0, 0.0),
    (550, 1.5, 0.2),
    (660, 3.0, 0.4),
    (440, 1.5, 0.0),
]
print("FM melody...")
for freq, ratio, pan in melody:
    with server.at():
        s = server.add_synth(
            fm_def,
            carrier_freq=freq,
            mod_ratio=ratio,
            mod_index=2.5,
            amplitude=0.2,
            pan=pan,
        )
    time.sleep(0.4)
    with server.at():
        s.set(gate=0)
    time.sleep(0.15)

time.sleep(0.5)
print("Done.")
server.quit()
