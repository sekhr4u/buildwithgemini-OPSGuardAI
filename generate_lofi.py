import wave
import math
import struct

sample_rate = 44100
duration = 16.0  # 16 seconds loop
total_samples = int(sample_rate * duration)

bpm = 85
beat_sec = 60.0 / bpm
bar_sec = beat_sec * 4

# Scale notes (frequencies in Hz)
notes = {
    'C4': 261.63, 'E4': 329.63, 'G4': 392.00, 'B4': 493.88,
    'A3': 220.00, 'C5': 523.25, 'E5': 659.25, 'G5': 783.99,
    'D4': 293.66, 'F4': 349.23, 'A4': 440.00,
    'G3': 196.00, 'D5': 587.33, 'B3': 246.94, 'F3': 174.61
}

# Chords (Cmaj7, Am7, Dm7, G7)
chords = [
    [notes['C4'], notes['E4'], notes['G4'], notes['B4']],
    [notes['A3'], notes['C4'], notes['E4'], notes['G4']],
    [notes['D4'], notes['F4'], notes['A4'], notes['C5']],
    [notes['G3'], notes['B3'], notes['D4'], notes['F4']]
]

bass_notes = [notes['C4']/2, notes['A3']/2, notes['D4']/2, notes['G3']/2]

def kick_sample(t_in_beat):
    if t_in_beat > 0.2: return 0.0
    freq = 130 * math.exp(-t_in_beat * 25)
    env = math.exp(-t_in_beat * 15)
    return math.sin(2 * math.pi * freq * t_in_beat) * env * 0.7

def snare_sample(t_in_beat):
    if t_in_beat > 0.25: return 0.0
    import random
    noise = (random.random() * 2 - 1)
    tone = math.sin(2 * math.pi * 180 * t_in_beat)
    env = math.exp(-t_in_beat * 20)
    return (noise * 0.7 + tone * 0.3) * env * 0.5

def hihat_sample(t_in_beat):
    if t_in_beat > 0.08: return 0.0
    import random
    noise = (random.random() * 2 - 1)
    env = math.exp(-t_in_beat * 50)
    return noise * env * 0.25

import random
random.seed(42)

print("Synthesizing Upbeat Lo-Fi Track...")
buffer = bytearray()

for i in range(total_samples):
    t = i / sample_rate
    
    # Measure & Beat position
    current_bar = int(t / bar_sec) % 4
    t_in_bar = t % bar_sec
    current_beat = int(t / beat_sec) % 16
    t_in_beat = (t % beat_sec)
    
    # 1. Soft Warm Chords
    chord = chords[current_bar]
    chord_val = 0.0
    for note in chord:
        # Sine + gentle 2nd harmonic for warm lo-fi key sound
        val = math.sin(2 * math.pi * note * t) * 0.6 + math.sin(2 * math.pi * note * 2 * t) * 0.15
        # Soft tremolo/LFO
        lfo = 1.0 + 0.15 * math.sin(2 * math.pi * 3 * t)
        chord_val += val * lfo
    chord_val = (chord_val / len(chord)) * 0.35
    
    # 2. Warm Sub Bass
    b_note = bass_notes[current_bar]
    bass_val = math.sin(2 * math.pi * b_note * t) * 0.4
    
    # 3. Drums
    drum_val = 0.0
    # Kick on beats 0, 6, 8, 14
    if current_beat in [0, 6, 8, 14]:
        drum_val += kick_sample(t_in_beat)
    # Snare on beats 4, 12
    if current_beat in [4, 12]:
        drum_val += snare_sample(t_in_beat)
    # Hihat every half-beat (8ths)
    t_in_eighth = (t % (beat_sec / 2))
    drum_val += hihat_sample(t_in_eighth)
    
    # 4. Mix & Master
    mix = chord_val + bass_val + drum_val
    # Soft limiter / clip
    mix = max(-0.95, min(0.95, mix))
    
    sample_int = int(mix * 32767)
    buffer.extend(struct.pack('<h', sample_int))  # Left
    buffer.extend(struct.pack('<h', sample_int))  # Right (Stereo)

with wave.open('lofi_track.wav', 'wb') as wf:
    wf.setnchannels(2)
    wf.setsampwidth(2)
    wf.setframerate(sample_rate)
    wf.writeframes(buffer)

print("Synthesized lofi_track.wav successfully!")
