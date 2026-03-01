@echo off
echo ========================================
echo   CHRISTMAS MUSIC CONVERTER
echo ========================================
echo.

if not exist "songs" mkdir songs
if not exist "converted" mkdir converted
if not exist "lyrics" mkdir lyrics

echo Looking for MP3 files in songs folder...
echo.

for %%f in (songs\*.mp3) do (
    echo Converting: %%~nf
    ffmpeg -i "%%f" -acodec pcm_s16le -ar 44100 "converted\%%~nf.wav" -y -loglevel quiet
    if exist "converted\%%~nf.wav" (
        echo   ✓ Success
    ) else (
        echo   ✗ Failed
    )
)

echo.
echo Conversion complete!
echo Press any key to exit...
pause > nul