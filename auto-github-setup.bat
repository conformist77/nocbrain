@echo off
echo 🚀 NOCbRAIN Auto GitHub Setup
echo ==============================

REM Get GitHub username
set /p username="Enter your GitHub username: "

REM Check if repository exists
echo 🔍 Checking if repository exists...
curl -s -o nul -w "%%{http_code}" https://github.com/%username%/nocbrain | findstr "200" >nul
if %errorlevel% equ 0 (
    echo ✅ Repository already exists
) else (
    echo ❌ Repository not found. Please create it first:
    echo    1. Go to https://github.com/new
    echo    2. Repository name: nocbrain
    echo    3. Description: AI Network Operations Center Assistant
    echo    4. Choose Public
    echo    5. Click "Create repository"
    echo.
    pause
)

REM Add remote
echo 🔗 Adding remote...
git remote add origin https://github.com/%username%/nocbrain.git

REM Push to GitHub
echo 📤 Pushing to GitHub...
git branch -M main
git push -u origin main

if %errorlevel% equ 0 (
    echo ✅ Successfully pushed to GitHub!
    echo 📍 Repository URL: https://github.com/%username%/nocbrain
    echo 📚 Documentation: https://github.com/%username%/nocbrain/blob/main/README.md
) else (
    echo ❌ Failed to push. Check your credentials and repository access.
)

echo.
echo 🎉 NOCbRAIN is now on GitHub!
pause
