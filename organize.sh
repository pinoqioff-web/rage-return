#!/data/data/com.termux/files/usr/bin/bash
BASE="$HOME/rage-return/media"
mkdir -p "$BASE/videos" "$BASE/thumbnails" "$BASE/images" "$BASE/other"
find "$BASE" -maxdepth 1 -type f | while read -r file; do
  ext="${file##*.}"
  case "${ext,,}" in
    mp4|mkv|mov|avi|webm) mv "$file" "$BASE/videos/" ;;
    jpg|jpeg|png|webp) mv "$file" "$BASE/thumbnails/" ;;
    gif) mv "$file" "$BASE/images/" ;;
    *) mv "$file" "$BASE/other/" ;;
  esac
done
echo "PINOQIO media organized successfully."
