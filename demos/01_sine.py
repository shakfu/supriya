"""
01 -- Hello, sine wave

The absolute minimum: boot an embedded server, play a 440 Hz sine wave
for two seconds, then quit.
"""

import time

from supriya import Server, find_free_port
from supriya.ugens import EnvGen, Envelope, Out, SinOsc, SynthDefBuilder

# -- Build a minimal synthdef --------------------------------------------------

with SynthDefBuilder(frequency=440, amplitude=0.3) as builder:
    sig = SinOsc.ar(frequency=builder["frequency"]) * builder["amplitude"]
    Out.ar(bus=0, source=[sig, sig])
sine_def = builder.build(name="sine")

# -- Boot, play, quit ---------------------------------------------------------

print("Booting embedded server...")
server = Server(embedded=True)
server.boot(port=find_free_port())
print("Server online.")

with server.at():
    with server.add_synthdefs(sine_def):
        synth = server.add_synth(sine_def, frequency=440, amplitude=0.3)
print("Playing 440 Hz sine wave for 2 seconds...")
time.sleep(2)

synth.free()
time.sleep(0.1)

print("Done.")
server.quit()
