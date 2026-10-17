#!/bin/bash
# Final export per CLAUDE.md §8 (Shorts variant 1080x1920):
#   H.264 High, 30 fps, 16-20 Mbps, yuv420p; AAC 320 kbps 48 kHz stereo; MP4 +faststart
# usage: export.sh <video_only.mp4> <mix.wav> <out.mp4> [share.mp4]
set -e
V=$1; A=$2; OUT=$3; SHARE=$4
ffmpeg -v error -y -i "$V" -i "$A" -map 0:v:0 -map 1:a:0 \
  -c:v libx264 -profile:v high -level 4.2 -preset slow -b:v 17M -maxrate 20M -bufsize 34M -pix_fmt yuv420p -r 30 \
  -g 60 -bf 2 -color_primaries bt709 -color_trc bt709 -colorspace bt709 \
  -c:a aac -b:a 320k -ar 48000 -ac 2 -shortest -movflags +faststart "$OUT"
if [ -n "$SHARE" ]; then
  ffmpeg -v error -y -i "$OUT" -c:v libx264 -profile:v high -preset slow -crf 23 -maxrate 6M -bufsize 12M -pix_fmt yuv420p \
    -c:a aac -b:a 192k -movflags +faststart "$SHARE"
fi
ffprobe -v error -show_entries stream=codec_name,profile,width,height,r_frame_rate,bit_rate,sample_rate,channels,pix_fmt -show_entries format=duration,size,bit_rate -of default=nw=1 "$OUT"
