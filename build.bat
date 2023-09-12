@echo off
cd /d %~dp0
set currdir=%~dp0
echo Currently building in: %currdir%

call nuitka --mingw64 --disable-console --standalone --onefile --show-memory --enable-plugin=tk-inter --include-data-files=%currdir%neko_spritesheet.png=neko_spritesheet.png --windows-icon-from-ico=%currdir%pneko.ico --company-name=Alkanixor --product-name=pNeko --file-version=0.1.0 --onefile-tempdir-spec="%%%%CACHE_DIR%%%%/%%%%COMPANY%%%%/%%%%PRODUCT%%%%/%%%%VERSION%%%%" neko.py

echo.
pause