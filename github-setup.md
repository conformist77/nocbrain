# GitHub Repository Setup Guide for NOCbRAIN

## Prerequisites
- GitHub account
- Git installed on your system
- GitHub CLI (gh) recommended

## Step 1: Create GitHub Repository

### Option A: Using GitHub CLI (Recommended)
```bash
# Install GitHub CLI if not already installed
# Windows: winget install GitHub.cli
# Mac: brew install gh
# Linux: sudo apt install gh

# Login to GitHub
gh auth login

# Create repository
gh repo create nocbrain --public --description "AI Network Operations Center Assistant" --clone=false

# Initialize local repository
git init
git branch -M main

# Add remote
git remote add origin https://github.com/YOUR_USERNAME/nocbrain.git
```

### Option B: Manual GitHub Setup
1. Go to https://github.com/new
2. Repository name: `nocbrain`
3. Description: `AI Network Operations Center Assistant`
4. Choose Public (for open source)
5. Don't initialize with README (we already have one)
6. Click "Create repository"
7. Copy the remote URL and add it locally:
```bash
git init
git branch -M main
git remote add origin https://github.com/YOUR_USERNAME/nocbrain.git
```

## Step 2: Configure Git Security

### Set up Git configuration
```bash
git config --global user.name "Your Name"
git config --global user.email "your.email@example.com"
```

### Create .gitignore (already included in project)
The project already includes a comprehensive .gitignore file that excludes:
- Environment variables (.env files)
- Database files
- Logs
- Build artifacts
- IDE configurations
- Secrets and certificates

## Step 3: Initial Commit and Push

```bash
# Add all files
git add .

# Make initial commit
git commit -m "Initial commit: NOCbRAIN AI Network Operations Center Assistant

- Complete project structure with backend (FastAPI) and frontend (React)
- Docker and Kubernetes deployment configurations
- CI/CD pipeline with GitHub Actions
- Comprehensive documentation and security setup
- Modular architecture for network monitoring, security analysis, and infrastructure management"

# Push to GitHub
git push -u origin main
```

## Step 4: Configure GitHub Repository Settings

### Enable Security Features
1. Go to your repository on GitHub
2. Click Settings → Security & analysis
3. Enable:
   - Dependabot alerts
   - Dependabot security updates
   - Code scanning
   - Secret scanning

### Set up Branch Protection
1. Settings → Branches → Add branch protection rule
2. Branch name pattern: `main`
3. Enable:
   - Require pull request reviews before merging
   - Require status checks to pass before merging
   - Require branches to be up to date before merging

### Configure Teams and Permissions
1. Settings → Collaborators & teams
2. Add collaborators with appropriate permissions
3. Create teams for different roles (Developers, Security, etc.)

## Step 5: Set up GitHub Secrets

### Required Secrets for CI/CD
Go to Settings → Secrets and variables → Actions → New repository secret:

1. `DOCKER_USERNAME`: Your Docker Hub username
2. `DOCKER_PASSWORD`: Your Docker Hub password or access token
3. `OPENAI_API_KEY`: OpenAI API key for AI features
4. `VAULT_TOKEN`: HashiCorp Vault token
5. `DATABASE_URL`: Production database connection string

### Environment-Specific Secrets
Create separate secrets for different environments:
- `STAGING_DATABASE_URL`
- `PRODUCTION_DATABASE_URL`
- `STAGING_REDIS_URL`
- `PRODUCTION_REDIS_URL`

## Step 6: Configure GitHub Copilot

### Enable Copilot for Repository
1. Go to Settings → Copilot
2. Enable "Allow GitHub Copilot access in this repository"
3. Configure policies for code suggestions

### Create Copilot Instructions
Create `.github/copilot-instructions.md`:
```markdown
# NOCbRAIN Copilot Instructions

## Project Context
NOCbRAIN is an AI-powered Network Operations Center assistant for monitoring, security analysis, and infrastructure management.

## Coding Standards
- Python: Follow PEP 8, use type hints
- TypeScript: Use strict mode, prefer functional components
- Security: Never hardcode secrets, use environment variables
- Testing: Write tests for all new features
- Documentation: Update docs for API changes

## Architecture Guidelines
- Modular design with clear separation of concerns
- Use dependency injection
- Implement proper error handling
- Follow RESTful API design principles
- Use async/await for I/O operations

## Security Requirements
- Validate all inputs
- Use parameterized queries
- Implement proper authentication/authorization
- Log security events
- Follow OWASP guidelines

## Performance Requirements
- Optimize database queries
- Use caching appropriately
- Implement rate limiting
- Monitor resource usage
```

## Step 7: Set up Automated Workflows

### Dependabot Configuration
Create `.github/dependabot.yml`:
```yaml
version: 2
updates:
  # Monitor Python dependencies
  - package-ecosystem: "pip"
    directory: "/backend"
    schedule:
      interval: "weekly"
    open-pull-requests-limit: 10

  # Monitor Node.js dependencies
  - package-ecosystem: "npm"
    directory: "/frontend"
    schedule:
      interval: "weekly"
    open-pull-requests-limit: 10

  # Monitor Docker dependencies
  - package-ecosystem: "docker"
    directory: "/"
    schedule:
      interval: "weekly"
    open-pull-requests-limit: 5
```

### Issue and PR Templates
Create `.github/ISSUE_TEMPLATE/bug_report.md`:
```markdown
---
name: Bug Report
about: Create a report to help us improve
title: "[BUG] "
labels: bug
assignees: ''
---

**Describe the bug**
A clear and concise description of what the bug is.

**To Reproduce**
Steps to reproduce the behavior:
1. Go to '...'
2. Click on '....'
3. Scroll down to '....'
4. See error

**Expected behavior**
A clear and concise description of what you expected to happen.

**Screenshots**
If applicable, add screenshots to help explain your problem.

**Environment:**
- OS: [e.g. Windows 10, macOS 12.0, Ubuntu 20.04]
- Browser: [e.g. Chrome, Firefox, Safari]
- Version: [e.g. 1.0.0]

**Additional context**
Add any other context about the problem here.
```

## Step 8: Configure Project Boards

### Create Project Boards
1. Go to Projects → New project
2. Choose "Board template"
3. Create boards for:
   - Backlog
   - In Progress
   - Code Review
   - Testing
   - Done

### Automate with GitHub Actions
Create workflows to automatically move issues between columns based on labels and PR status.

## Step 9: Set up Monitoring and Analytics

### GitHub Insights
1. Enable Insights for your repository
2. Configure traffic analytics
3. Set up dependency graphs

### External Monitoring
Consider integrating with:
- SonarCloud for code quality
- CodeClimate for maintainability
- Snyk for security scanning

## Step 10: Community Management

### Contributing Guidelines
The project already includes `CONTRIBUTING.md`. Make sure it's visible and linked from the README.

### Code of Conduct
Create `CODE_OF_CONDUCT.md`:
```markdown
# Contributor Covenant Code of Conduct

## Our Pledge
We as members, contributors, and leaders pledge to make participation in our
community a harassment-free experience for everyone...

## Our Standards
Examples of behavior that contributes to a positive environment...

## Enforcement
Instances of abusive, harassing, or otherwise unacceptable behavior may be
reported by contacting the project team at conduct@nocbrain.org.
```

### Support Channels
- GitHub Discussions for community support
- Issues for bug reports and feature requests
- Discord/Slack for real-time communication

## Quick Start Commands

After completing the setup, use these commands:

```bash
# Clone the repository
git clone https://github.com/YOUR_USERNAME/nocbrain.git
cd nocbrain

# Set up development environment
./scripts/setup.sh

# Start development
docker-compose up

# Run tests
./scripts/test.sh

# Deploy to staging
./scripts/deploy.sh staging
```

## Security Best Practices

1. **Never commit secrets**: Use environment variables and GitHub Secrets
2. **Enable 2FA**: Require two-factor authentication for all collaborators
3. **Review dependencies**: Regularly update and audit dependencies
4. **Monitor access**: Review repository access logs regularly
5. **Use signed commits**: Configure GPG signing for commits

This setup provides a secure, scalable foundation for your NOCbRAIN project with proper Git workflows, security practices, and automation.
