"""
08 -- Granular synthesis

Load a sample and granulate it with GrainBuf. Grain rate, position,
and duration are modulated by low-frequency noise generators.
"""

import time
from pathlib import Path

import supriya
from supriya import DoneAction, Server, find_free_port
from supriya.ugens import (
    Dust,
    EnvGen,
    Envelope,
    GrainBuf,
    LFNoise1,
    LFNoise2,
    Out,
    SynthDefBuilder,
)

SAMPLES_DIR = Path(supriya.__file__).parent / "samples"

# -- Granular synthdef ---------------------------------------------------------

with SynthDefBuilder(
    buffer_id=0, amplitude=0.3, density=12.0, gate=1
) as builder:
    # Trigger grains with Dust (stochastic impulses)
    trig = Dust.kr(density=builder["density"])
    # Slowly wandering position in the buffer (0..1)
    pos = LFNoise2.kr(frequency=0.2)  # smooth random
    pos = pos * 0.5 + 0.5  # map to 0..1
    # Grain duration varies between 0.02 and 0.15 seconds
    dur = LFNoise1.kr(frequency=0.5) * 0.065 + 0.085
    # Rate wanders slightly around 1.0
    rate = LFNoise1.kr(frequency=0.3) * 0.3 + 1.0
    # Pan wanders
    pan = LFNoise2.kr(frequency=0.4)

    grains = GrainBuf.ar(
        channel_count=2,
        trigger=trig,
        duration=dur,
        buffer_id=builder["buffer_id"],
        rate=rate,
        position=pos,
        pan=pan,
        interpolate=2,
    )
    env = EnvGen.kr(
        envelope=Envelope.asr(attack_time=1.0, sustain=1.0, release_time=2.0),
        gate=builder["gate"],
        done_action=DoneAction.FREE_SYNTH,
    )
    Out.ar(bus=0, source=grains * env * builder["amplitude"])
grain_def = builder.build(name="grain_cloud")

# -- Boot and play -------------------------------------------------------------

print("Booting embedded server...")
server = Server(embedded=True)
server.boot(port=find_free_port())
print("Server online.")

with server.at():
    server.add_synthdefs(grain_def)
time.sleep(0.2)

# Load a bird sample for granulation
sample_path = SAMPLES_DIR / "birds-03.wav"
buf = server.add_buffer(file_path=sample_path)
print(f"Loaded sample: {sample_path.name}")
time.sleep(0.3)

# Sparse grain cloud
print("Sparse grain cloud (density=8, 4s)...")
with server.at():
    g1 = server.add_synth(grain_def, buffer_id=buf.id_, amplitude=0.3, density=8.0)
time.sleep(4.0)
with server.at():
    g1.set(gate=0)
time.sleep(2.5)

# Dense grain cloud
print("Dense grain cloud (density=30, 5s)...")
with server.at():
    g2 = server.add_synth(grain_def, buffer_id=buf.id_, amplitude=0.25, density=30.0)
time.sleep(5.0)
with server.at():
    g2.set(gate=0)
time.sleep(2.5)

buf.free()
print("Done.")
server.quit()
