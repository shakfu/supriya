"""
02 -- Shaping sound over time

Percussive sine tones at different pitches, followed by a sustained tone
with an ADSR envelope and gate release.
"""

import time

from supriya import DoneAction, Server, find_free_port
from supriya.ugens import (
    EnvGen,
    Envelope,
    Out,
    Pan2,
    SinOsc,
    SynthDefBuilder,
)
from supriya.enums import ParameterRate

# -- Percussive synthdef (self-freeing) ----------------------------------------

with SynthDefBuilder(frequency=440, amplitude=0.3, pan=0.0) as builder:
    sig = SinOsc.ar(frequency=builder["frequency"]) * builder["amplitude"]
    env = EnvGen.kr(
        envelope=Envelope.percussive(attack_time=0.01, release_time=0.5),
        done_action=DoneAction.FREE_SYNTH,
    )
    out = Pan2.ar(source=sig * env, position=builder["pan"])
    Out.ar(bus=0, source=out)
perc_def = builder.build(name="perc_sine")

# -- Sustained synthdef (gate-controlled) --------------------------------------

with SynthDefBuilder(
    frequency=440, amplitude=0.3, gate=1, pan=0.0
) as builder:
    sig = SinOsc.ar(frequency=builder["frequency"]) * builder["amplitude"]
    env = EnvGen.kr(
        envelope=Envelope.adsr(
            attack_time=0.05, decay_time=0.2, sustain=0.6, release_time=0.8
        ),
        gate=builder["gate"],
        done_action=DoneAction.FREE_SYNTH,
    )
    out = Pan2.ar(source=sig * env, position=builder["pan"])
    Out.ar(bus=0, source=out)
adsr_def = builder.build(name="adsr_sine")

# -- Boot and play -------------------------------------------------------------

print("Booting embedded server...")
server = Server(embedded=True)
server.boot(port=find_free_port())
print("Server online.")

# Send both synthdefs
with server.at():
    server.add_synthdefs(perc_def, adsr_def)
time.sleep(0.2)

# Play a descending percussive sequence
notes = [880, 660, 550, 440, 330]
pans = [-0.6, -0.3, 0.0, 0.3, 0.6]
print("Playing percussive sequence...")
for freq, pan in zip(notes, pans):
    with server.at():
        server.add_synth(perc_def, frequency=freq, amplitude=0.3, pan=pan)
    time.sleep(0.3)
time.sleep(0.5)

# Play a sustained tone, hold it, then release via gate
print("Playing sustained ADSR tone (hold 2s, then release)...")
with server.at():
    held = server.add_synth(adsr_def, frequency=330, amplitude=0.3, pan=0.0)
time.sleep(2.0)

print("Releasing gate...")
with server.at():
    held.set(gate=0)
time.sleep(1.0)

print("Done.")
server.quit()
