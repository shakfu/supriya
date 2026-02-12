"""
05 -- Playing audio files

Load bundled bird samples into buffers and play them back at different
rates using PlayBuf.
"""

import time
from pathlib import Path

import supriya
from supriya import DoneAction, Server, find_free_port
from supriya.ugens import (
    BufRateScale,
    EnvGen,
    Envelope,
    Out,
    Pan2,
    PlayBuf,
    SynthDefBuilder,
)

SAMPLES_DIR = Path(supriya.__file__).parent / "samples"

# -- Sample playback synthdef (mono input, stereo output) ----------------------

with SynthDefBuilder(
    buffer_id=0, rate=1.0, amplitude=0.5, pan=0.0
) as builder:
    sig = PlayBuf.ar(
        channel_count=1,
        buffer_id=builder["buffer_id"],
        rate=BufRateScale.kr(buffer_id=builder["buffer_id"]) * builder["rate"],
        done_action=DoneAction.FREE_SYNTH,
    )
    out = Pan2.ar(source=sig * builder["amplitude"], position=builder["pan"])
    Out.ar(bus=0, source=out)
play_def = builder.build(name="sample_play")

# -- Boot and play -------------------------------------------------------------

print("Booting embedded server...")
server = Server(embedded=True)
server.boot(port=find_free_port())
print("Server online.")

with server.at():
    server.add_synthdefs(play_def)
time.sleep(0.2)

# Load bird samples
sample_files = sorted(SAMPLES_DIR.glob("birds-*.wav"))[:4]
buffers = []
for path in sample_files:
    buf = server.add_buffer(file_path=path)
    buffers.append(buf)
    print(f"  Loaded: {path.name}")
time.sleep(0.5)

# Play each sample at normal speed
print("Playing samples at normal speed...")
for i, buf in enumerate(buffers):
    pan = -0.6 + (i * 0.4)
    with server.at():
        server.add_synth(play_def, buffer_id=buf.id_, rate=1.0, amplitude=0.5, pan=pan)
    time.sleep(1.5)

# Play samples at altered rates
rates = [0.5, 1.5, 0.75, 2.0]
print("Playing samples at varied rates...")
for buf, rate in zip(buffers, rates):
    print(f"  rate={rate}")
    with server.at():
        server.add_synth(
            play_def, buffer_id=buf.id_, rate=rate, amplitude=0.4, pan=0.0
        )
    time.sleep(1.2)

time.sleep(1.0)

# Clean up buffers
for buf in buffers:
    buf.free()

print("Done.")
server.quit()
