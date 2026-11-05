#!/usr/bin/env bash
# Generates the test media used by smoke.mjs and bigfile.mjs into test/media/ (not committed).
set -euo pipefail
cd "$(dirname "$0")"
mkdir -p media && cd media
ffmpeg -v error -y -f lavfi -i "testsrc2=size=1080x1920:rate=30:duration=6" -f lavfi -i "sine=frequency=440:duration=6:sample_rate=48000" \
  -c:v libx264 -pix_fmt yuv420p -preset veryfast -c:a aac -b:a 128k -shortest portrait.mp4
ffmpeg -v error -y -f lavfi -i "smptehdbars=size=1920x1080:rate=30:duration=5" -f lavfi -i "sine=frequency=660:duration=5:sample_rate=44100" \
  -vf "drawtext=text='LANDSCAPE %{pts\:hms}':fontsize=90:fontcolor=white:x=60:y=60:box=1:boxcolor=black" \
  -c:v libx264 -pix_fmt yuv420p -preset veryfast -c:a aac -b:a 128k -shortest landscape.mp4
# phone-style clip: landscape pixels with rotation metadata
ffmpeg -v error -y -f lavfi -i "testsrc=size=1920x1080:rate=30:duration=4" -vf "drawbox=x=0:y=0:w=400:h=200:color=red:t=fill" \
  -c:v libx264 -pix_fmt yuv420p -preset veryfast -an rot_raw.mp4
ffmpeg -v error -y -display_rotation 90 -i rot_raw.mp4 -c copy rotated.mp4
# 120 BPM click track with a louder section from 10 s
python3 - <<'EOF'
import numpy as np, wave
sr = 44100; dur = 20.0; n = int(sr * dur); t = np.arange(n) / sr; x = np.zeros(n)
period = 0.5
for k in range(int(dur / period)):
    s = int(k * period * sr); L = int(0.12 * sr); i = np.arange(L)
    seg = (1.0 if k % 4 == 0 else 0.55) * np.exp(-i / (0.02 * sr)) * np.sin(2 * np.pi * (60 + 120 * np.exp(-i / (0.01 * sr))) * i / sr)
    x[s:s + L] += seg[:max(0, min(L, n - s))]
x += (0.05 + 0.25 * (t > 10)) * np.sin(2 * np.pi * 220 * t) * 0.5
x = x / np.max(np.abs(x)) * 0.8
w = wave.open('music.wav', 'wb'); w.setnchannels(1); w.setsampwidth(2); w.setframerate(sr); w.writeframes((x * 32767).astype(np.int16).tobytes()); w.close()
EOF
ffmpeg -v error -y -f lavfi -i "color=c=0x2a6f97:size=1200x800,drawbox=x=100:y=100:w=300:h=300:color=yellow:t=fill" -frames:v 1 still.png
# ~2 GB lossless file with its index (moov) at the end, for bigfile.mjs
if [ ! -f big.mp4 ]; then
  ffmpeg -v error -y -f lavfi -i "testsrc2=s=1920x1080:r=30:d=24,noise=alls=40:allf=t+u" -f lavfi -i "sine=f=330:d=24:sample_rate=48000" \
    -c:v libx264 -preset ultrafast -qp 0 -pix_fmt yuv420p -c:a aac -b:a 160k -shortest big.mp4
fi
ls -la
