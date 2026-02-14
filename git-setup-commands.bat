@echo off
echo 🚀 NOCbRAIN Git Setup Script
echo =============================

REM Check if git is installed
git --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ Git is not installed. Please install Git first:
    echo    1. Download from https://git-scm.com/download/win
    echo    2. Or run: winget install Git.Git
    pause
    exit /b 1
)

echo ✅ Git found: 
git --version

REM Initialize repository
echo 📁 Initializing Git repository...
git init

REM Configure git if not configured
git config user.name >nul 2>&1
if %errorlevel% neq 0 (
    echo ⚙️  Git user not configured. Please enter your details:
    set /p username="Enter your GitHub username: "
    set /p email="Enter your GitHub email: "
    git config --global user.name "%username%"
    git config --global user.email "%email%"
)

REM Add all files
echo 📦 Adding files to Git...
git add .

REM Initial commit
echo 💾 Creating initial commit...
git commit -m "Initial commit: NOCbRAIN AI Network Operations Center Assistant

- Complete project structure with backend (FastAPI) and frontend (React)
- Docker and Kubernetes deployment configurations
- CI/CD pipeline with GitHub Actions
- Comprehensive documentation and security setup
- Modular architecture for network monitoring, security analysis, and infrastructure management"

echo ✅ Local repository ready!
echo.
echo 🌐 Next steps:
echo 1. Create repository on GitHub: https://github.com/new
echo 2. Repository name: nocbrain
echo 3. Description: AI Network Operations Center Assistant
echo 4. Choose Public
echo 5. Copy the repository URL
echo 6. Run these commands (replace YOUR_USERNAME):
echo    git remote add origin https://github.com/YOUR_USERNAME/nocbrain.git
echo    git branch -M main
echo    git push -u origin main
echo.
pause
