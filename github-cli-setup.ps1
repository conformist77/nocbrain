# NOCbRAIN GitHub CLI Setup Script
# PowerShell script for automated GitHub repository setup

Write-Host "🚀 NOCbRAIN GitHub Setup Script" -ForegroundColor Green
Write-Host "=================================" -ForegroundColor Green

# Check if GitHub CLI is installed
try {
    gh --version | Out-Null
    Write-Host "✅ GitHub CLI found: $(gh --version)" -ForegroundColor Green
} catch {
    Write-Host "❌ GitHub CLI not found. Install with: winget install GitHub.cli" -ForegroundColor Red
    Write-Host "Or use the manual method with git-setup-commands.bat" -ForegroundColor Yellow
    exit 1
}

# Check if logged in to GitHub
try {
    gh auth status | Out-Null
    Write-Host "✅ Already logged in to GitHub" -ForegroundColor Green
} catch {
    Write-Host "🔐 Please login to GitHub..." -ForegroundColor Yellow
    gh auth login
}

# Get GitHub username
$username = gh api user --jq '.login'
Write-Host "👤 GitHub username: $username" -ForegroundColor Cyan

# Create repository
Write-Host "📁 Creating GitHub repository..." -ForegroundColor Yellow
try {
    gh repo create nocbrain --public --description "AI Network Operations Center Assistant" --clone=false
    Write-Host "✅ Repository created successfully" -ForegroundColor Green
} catch {
    Write-Host "⚠️  Repository might already exist. Continuing..." -ForegroundColor Yellow
}

# Initialize local git repository
Write-Host "🔧 Initializing local Git repository..." -ForegroundColor Yellow
git init

# Configure git if needed
if (-not (git config user.name)) {
    $name = Read-Host "Enter your name for Git commits"
    $email = Read-Host "Enter your email for Git commits"
    git config --global user.name $name
    git config --global user.email $email
}

# Add files and commit
Write-Host "📦 Adding files and creating initial commit..." -ForegroundColor Yellow
git add .
git commit -m "Initial commit: NOCbRAIN AI Network Operations Center Assistant

- Complete project structure with backend (FastAPI) and frontend (React)
- Docker and Kubernetes deployment configurations
- CI/CD pipeline with GitHub Actions
- Comprehensive documentation and security setup
- Modular architecture for network monitoring, security analysis, and infrastructure management"

# Add remote and push
Write-Host "🌐 Adding remote and pushing to GitHub..." -ForegroundColor Yellow
git remote add origin "https://github.com/$username/nocbrain.git"
git branch -M main
git push -u origin main

Write-Host "🎉 NOCbRAIN successfully deployed to GitHub!" -ForegroundColor Green
Write-Host "📍 Repository URL: https://github.com/$username/nocbrain" -ForegroundColor Cyan
Write-Host "📚 Documentation: https://github.com/$username/nocbrain/blob/main/README.md" -ForegroundColor Cyan
Write-Host "" -ForegroundColor White
Write-Host "🚀 Next steps:" -ForegroundColor Yellow
Write-Host "1. Configure GitHub Secrets for API keys" -ForegroundColor White
Write-Host "2. Enable GitHub Actions" -ForegroundColor White
Write-Host "3. Set up branch protection rules" -ForegroundColor White
Write-Host "4. Invite collaborators" -ForegroundColor White
