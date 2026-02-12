"""
07 -- Compositional patterns

Use the pattern system to sequence melodic events. A treble melody
and a bass line run in parallel via PatternPlayer and Clock.
"""

import time

from supriya import Clock, DoneAction, Server, find_free_port
from supriya.patterns import (
    EventPattern,
    ParallelPattern,
    PatternPlayer,
    SequencePattern,
)
from supriya.ugens import (
    EnvGen,
    Envelope,
    LPF,
    Out,
    Pan2,
    SinOsc,
    SynthDefBuilder,
    VarSaw,
)

# -- Synthdef for melody -------------------------------------------------------

with SynthDefBuilder(frequency=440, amplitude=0.15, pan=0.0, gate=1) as builder:
    sig = SinOsc.ar(frequency=builder["frequency"]) * builder["amplitude"]
    env = EnvGen.kr(
        envelope=Envelope.adsr(
            attack_time=0.01, decay_time=0.1, sustain=0.5, release_time=0.2
        ),
        gate=builder["gate"],
        done_action=DoneAction.FREE_SYNTH,
    )
    out = Pan2.ar(source=sig * env, position=builder["pan"])
    Out.ar(bus=0, source=out)
melody_def = builder.build(name="melody_voice")

# -- Synthdef for bass ---------------------------------------------------------

with SynthDefBuilder(frequency=110, amplitude=0.2, gate=1) as builder:
    sig = VarSaw.ar(frequency=builder["frequency"], width=0.3) * builder["amplitude"]
    filtered = LPF.ar(source=sig, frequency=800)
    env = EnvGen.kr(
        envelope=Envelope.adsr(
            attack_time=0.01, decay_time=0.3, sustain=0.4, release_time=0.3
        ),
        gate=builder["gate"],
        done_action=DoneAction.FREE_SYNTH,
    )
    Out.ar(bus=0, source=[filtered * env, filtered * env])
bass_def = builder.build(name="bass_voice")

# -- Boot ----------------------------------------------------------------------

print("Booting embedded server...")
server = Server(embedded=True)
server.boot(port=find_free_port())
print("Server online.")

with server.at():
    server.add_synthdefs(melody_def, bass_def)
time.sleep(0.3)

# -- Define patterns -----------------------------------------------------------

# Melody: a repeating sequence of pitches with varied durations
treble = EventPattern(
    synthdef=melody_def,
    frequency=SequencePattern(
        [660, 550, 440, 550, 660, 660, 660, 550, 550, 550, 660, 880, 880],
        iterations=2,
    ),
    delta=SequencePattern([0.25, 0.25, 0.25, 0.25, 0.25, 0.25, 0.5,
                           0.25, 0.25, 0.5, 0.25, 0.25, 0.5],
                          iterations=2),
    duration=SequencePattern([0.2, 0.2, 0.2, 0.2, 0.2, 0.2, 0.45,
                              0.2, 0.2, 0.45, 0.2, 0.2, 0.45],
                             iterations=2),
    amplitude=0.15,
    pan=-0.3,
)

# Bass: slower root notes
bass = EventPattern(
    synthdef=bass_def,
    frequency=SequencePattern([165, 165, 220, 220, 165, 165, 220, 220],
                              iterations=2),
    delta=0.5,
    duration=0.45,
    amplitude=0.2,
)

combined = ParallelPattern([treble, bass])

# -- Play with clock -----------------------------------------------------------

print("Playing pattern (melody + bass)...")
clock = Clock()
clock.start(beats_per_minute=140)

player = PatternPlayer(pattern=combined, context=server, clock=clock)
player.play()

# Let the pattern run
time.sleep(10)

player.stop()
time.sleep(0.5)
clock.stop()

print("Done.")
server.quit()
