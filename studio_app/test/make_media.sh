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
# a small "scene pack": five different shots back to back (for shot detection)
ffmpeg -v error -y -f lavfi -i "smptehdbars=s=1280x720:r=30:d=2" -f lavfi -i "testsrc=s=1280x720:r=30:d=2.5" -f lavfi -i "mandelbrot=s=1280x720:r=30,trim=duration=2" \
  -f lavfi -i "color=c=0x8b0000:s=1280x720:r=30:d=1.5,drawbox=x=500:y=200:w=280:h=320:color=black:t=fill" -f lavfi -i "cellauto=s=1280x720:r=30,trim=duration=2" \
  -f lavfi -i "sine=f=220:d=10:sample_rate=48000" \
  -filter_complex "[0:v][1:v][2:v][3:v][4:v]concat=n=5:v=1:a=0,format=yuv420p[v]" -map "[v]" -map 5:a -c:v libx264 -preset veryfast -c:a aac -shortest pack.mp4
# a 12 s "talk" for long form: a face-like frame and speech-like bursts with pauses
ffmpeg -v error -y -i nat_astronaut.mp4 -i nat_chelsea.mp4 -i nat_coffee.mp4 -f lavfi -i "sine=f=180:d=12:sample_rate=48000" \
  -filter_complex "[0:v]scale=1280:720,setsar=1[a];[1:v]scale=1280:720,setsar=1[b];[2:v]scale=1280:720,setsar=1[c];[a][b][c]concat=n=3:v=1:a=0,tpad=stop_mode=clone:stop_duration=0,format=yuv420p[v];[3:a]volume='if(between(t,1.0,2.1)+between(t,6.8,7.9),0,1)':eval=frame[s]" \
  -map "[v]" -map "[s]" -c:v libx264 -preset veryfast -c:a aac -t 12 talk.mp4
