"""
06 -- Buses, groups, and effects

Route a dry synth through an audio bus into an effects group containing
reverb and delay.
"""

import time

from supriya import AddAction, DoneAction, Server, find_free_port
from supriya.ugens import (
    CombC,
    EnvGen,
    Envelope,
    FreeVerb,
    In,
    Out,
    Pan2,
    ReplaceOut,
    Saw,
    SinOsc,
    SynthDefBuilder,
)

# -- Dry source: detuned saws -------------------------------------------------

with SynthDefBuilder(
    frequency=220, amplitude=0.2, out=0, gate=1
) as builder:
    sig = (Saw.ar(frequency=builder["frequency"])
           + Saw.ar(frequency=builder["frequency"] * 1.005)) * 0.5
    env = EnvGen.kr(
        envelope=Envelope.adsr(
            attack_time=0.01, decay_time=0.2, sustain=0.6, release_time=0.5
        ),
        gate=builder["gate"],
        done_action=DoneAction.FREE_SYNTH,
    )
    Out.ar(bus=builder["out"], source=sig * env * builder["amplitude"])
dry_def = builder.build(name="dry_saw")

# -- Reverb effect -------------------------------------------------------------

with SynthDefBuilder(in_bus=0, mix=0.4, room=0.7, damp=0.5) as builder:
    sig = In.ar(bus=builder["in_bus"], channel_count=1)
    wet = FreeVerb.ar(source=sig, mix=builder["mix"], room_size=builder["room"],
                      damping=builder["damp"])
    ReplaceOut.ar(bus=builder["in_bus"], source=wet)
reverb_def = builder.build(name="reverb")

# -- Comb delay effect ---------------------------------------------------------

with SynthDefBuilder(in_bus=0, delay=0.3, decay=2.0) as builder:
    sig = In.ar(bus=builder["in_bus"], channel_count=1)
    wet = sig + CombC.ar(
        source=sig,
        maximum_delay_time=1.0,
        delay_time=builder["delay"],
        decay_time=builder["decay"],
    ) * 0.4
    ReplaceOut.ar(bus=builder["in_bus"], source=wet)
delay_def = builder.build(name="comb_delay")

# -- Stereo output (bus -> hardware out) ---------------------------------------

with SynthDefBuilder(in_bus=0, amplitude=1.0) as builder:
    sig = In.ar(bus=builder["in_bus"], channel_count=1)
    out = Pan2.ar(source=sig * builder["amplitude"], position=0.0)
    Out.ar(bus=0, source=out)
output_def = builder.build(name="stereo_out")

# -- Boot and play -------------------------------------------------------------

print("Booting embedded server...")
server = Server(embedded=True)
server.boot(port=find_free_port())
print("Server online.")

with server.at():
    server.add_synthdefs(dry_def, reverb_def, delay_def, output_def)
time.sleep(0.3)

# Allocate a private audio bus
fx_bus = server.add_bus("audio")

# Create group structure: source_group -> fx_group
# Both are children of the default group; fx_group runs after source_group.
with server.at():
    source_group = server.add_group()
    fx_group = server.add_group(
        add_action=AddAction.ADD_AFTER, target_node=source_group
    )

# Add effects into fx_group, then the stereo output after fx_group
with server.at():
    server.add_synth(
        reverb_def,
        add_action=AddAction.ADD_TO_HEAD,
        target_node=fx_group,
        in_bus=fx_bus.id_,
        mix=0.4,
        room=0.7,
    )
    server.add_synth(
        delay_def,
        add_action=AddAction.ADD_TO_TAIL,
        target_node=fx_group,
        in_bus=fx_bus.id_,
        delay=0.25,
        decay=1.5,
    )
    server.add_synth(
        output_def,
        add_action=AddAction.ADD_AFTER,
        target_node=fx_group,
        in_bus=fx_bus.id_,
        amplitude=1.0,
    )

# Play notes through the effect chain
notes = [220, 330, 440, 550, 330, 220]
print("Playing notes through reverb + delay chain...")
for freq in notes:
    with server.at():
        s = server.add_synth(
            dry_def,
            add_action=AddAction.ADD_TO_TAIL,
            target_node=source_group,
            frequency=freq,
            amplitude=0.25,
            out=fx_bus.id_,
        )
    time.sleep(0.4)
    with server.at():
        s.set(gate=0)
    time.sleep(0.2)

# Let the reverb/delay tails ring out
print("Letting effects ring out...")
time.sleep(3.0)

print("Done.")
server.quit()
