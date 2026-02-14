@echo off
echo 🔧 Fixing NOCbRAIN Repository Setup
echo ====================================

cd c:\Users\renderkar\Documents\NOCbRAIN

echo 1. Removing existing remote...
git remote remove origin

echo 2. Adding new remote...
git remote add origin https://github.com/conformist77/nocbrain.git

echo 3. Verifying remote...
git remote -v

echo 4. Pushing to GitHub...
git push -u origin main

if %errorlevel% equ 0 (
    echo ✅ Successfully pushed to GitHub!
    echo 📍 Repository: https://github.com/conformist77/nocbrain
    echo 🎉 NOCbRAIN is now live on GitHub!
) else (
    echo ❌ Push failed. Trying force push...
    git push -u origin main --force
    if %errorlevel% equ 0 (
        echo ✅ Force push successful!
        echo 📍 Repository: https://github.com/conformist77/nocbrain
    ) else (
        echo ❌ Still failed. Manual steps:
        echo    1. Go to https://github.com/conformist77/nocbrain
        echo    2. Click Settings → Danger Zone → Delete repository
        echo    3. Create new repository with same name
        echo    4. Run this script again
    )
)

pause
