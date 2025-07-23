@echo off
echo 🧹 Cleaning up scattered files in root directory...

REM Move test scripts to tests folder
if exist test_*.py (
    echo Moving test scripts to tests/
    move test_*.py tests\ 2>nul
)

if exist check_*.py (
    echo Moving check scripts to tests/
    move check_*.py tests\ 2>nul
)

if exist debug_*.py (
    echo Moving debug scripts to tests/
    move debug_*.py tests\ 2>nul
)

if exist quick_*.py (
    echo Moving quick scripts to tests/
    move quick_*.py tests\ 2>nul
)

if exist get_*.py (
    echo Moving get scripts to tests/
    move get_*.py tests\ 2>nul
)

REM Move setup scripts to help-files
if exist setup_*.py (
    echo Moving setup scripts to help-files/
    move setup_*.py help-files\ 2>nul
)

if exist *_guide.py (
    echo Moving guide scripts to help-files/
    move *_guide.py help-files\ 2>nul
)

if exist *_help.py (
    echo Moving help scripts to help-files/
    move *_help.py help-files\ 2>nul
)

REM Move local dev files
if exist config.yml (
    echo Moving config.yml to local-dev-resources/
    move config.yml local-dev-resources\ 2>nul
)

if exist start_*.bat (
    echo Moving batch files to local-dev-resources/
    move start_*.bat local-dev-resources\ 2>nul
)

if exist cloudflared.exe (
    echo Moving cloudflared.exe to local-dev-resources/
    move cloudflared.exe local-dev-resources\ 2>nul
)

echo ✅ Cleanup complete! Root directory should be clean now.
pause
