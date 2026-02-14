@echo off
echo 🗑️  Recreating NOCbRAIN Repository
echo ==================================

echo Instructions:
echo ==============
echo 1. Go to https://github.com/conformist77/nocbrain
echo 2. Click Settings tab
echo 3. Scroll down to "Danger Zone"
echo 4. Click "Delete repository"
echo 5. Type "conformist77/nocbrain" to confirm
echo 6. Create new repository: https://github.com/new
echo    - Name: nocbrain
echo    - Description: AI Network Operations Center Assistant
echo    - Choose Public
echo    - Click Create repository
echo.
echo After doing the above steps, press any key to continue...
pause

cd c:\Users\renderkar\Documents\NOCbRAIN

echo 🔧 Resetting local repository...
git remote remove origin
git remote add origin https://github.com/conformist77/nocbrain.git
git branch -M main

echo 📤 Pushing to new repository...
git push -u origin main

if %errorlevel% equ 0 (
    echo ✅ Successfully pushed to GitHub!
    echo 📍 Repository: https://github.com/conformist77/nocbrain
    echo 🎉 NOCbRAIN is now live on GitHub!
) else (
    echo ❌ Push failed. Check your internet and GitHub access.
)

pause
