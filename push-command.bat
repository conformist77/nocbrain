@echo off
echo 📤 Pushing NOCbRAIN to GitHub...
echo ================================

cd c:\Users\renderkar\Documents\NOCbRAIN

git push -u origin main

if %errorlevel% equ 0 (
    echo ✅ Successfully pushed to GitHub!
    echo 📍 Repository: https://github.com/conformist77/nocbrain
    echo 🎉 NOCbRAIN is now live on GitHub!
) else (
    echo ❌ Push failed. Make sure:
    echo    1. Repository exists on GitHub
    echo    2. You have internet connection
    echo    3. Your GitHub credentials are configured
)

pause
