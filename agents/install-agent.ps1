# NOCbRAIN Agent Installation Script for Windows
# Supports: Windows 10, Windows Server 2016+

param(
    [Parameter(Mandatory=$false)]
    [string]$ServerUrl = "https://api.nocbrain.com",
    
    [Parameter(Mandatory=$false)]
    [string]$ApiKey = "",
    
    [Parameter(Mandatory=$false)]
    [string]$AgentId = "",
    
    [Parameter(Mandatory=$false)]
    [string]$InstallDir = "C:\Program Files\NOCbRAIN Agent",
    
    [Parameter(Mandatory=$false)]
    [switch]$Uninstall,
    
    [Parameter(Mandatory=$false)]
    [switch]$Update
)

# Colors for output
$Colors = @{
    Red = "Red"
    Green = "Green"
    Yellow = "Yellow"
    Blue = "Blue"
    White = "White"
}

function Write-ColorOutput {
    param(
        [string]$Message,
        [string]$Color = "White"
    )
    Write-Host $Message -ForegroundColor $Colors[$Color]
}

function Write-Status {
    param([string]$Message)
    Write-ColorOutput "[INFO] $Message" "Green"
}

function Write-Warning {
    param([string]$Message)
    Write-ColorOutput "[WARNING] $Message" "Yellow"
}

function Write-Error {
    param([string]$Message)
    Write-ColorOutput "[ERROR] $Message" "Red"
}

function Write-Header {
    Write-ColorOutput @"
==================================
 NOCbRAIN Agent Installer
 Version: 1.0.0
==================================
"@ "Blue"
}

function Test-AdminPrivileges {
    $currentUser = [Security.Principal.WindowsIdentity]::GetCurrent()
    $principal = New-Object Security.Principal.WindowsPrincipal($currentUser)
    if (-not $principal.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)) {
        Write-Error "This script must be run as Administrator"
        exit 1
    }
}

function Install-PythonDependencies {
    Write-Status "Installing Python dependencies..."
    
    try {
        # Check if Python is installed
        $pythonVersion = python --version 2>&1
        if ($pythonVersion -match "Python 3") {
            Write-Status "Python 3 is already installed: $pythonVersion"
        } else {
            Write-Error "Python 3 is required but not found"
            Write-Status "Please install Python 3.8+ from https://python.org"
            exit 1
        }
        
        # Install required packages
        Write-Status "Installing Python packages..."
        python -m pip install --upgrade pip
        python -m pip install psutil requests cryptography pywin32
        
        Write-Status "Python dependencies installed successfully"
    }
    catch {
        Write-Error "Failed to install Python dependencies: $_"
        exit 1
    }
}

function Create-InstallDirectory {
    Write-Status "Creating installation directory..."
    
    if (-not (Test-Path $InstallDir)) {
        New-Item -ItemType Directory -Path $InstallDir -Force
        Write-Status "Created directory: $InstallDir"
    }
    else {
        Write-Warning "Installation directory already exists: $InstallDir"
    }
}

function Install-Agent {
    Write-Status "Installing NOCbRAIN agent..."
    
    try {
        # Download agent
        $agentUrl = "https://raw.githubusercontent.com/conformist77/nocbrain/main/agents/nocbrain-agent.py"
        $agentPath = Join-Path $InstallDir "nocbrain-agent.py"
        
        Invoke-WebRequest -Uri $agentUrl -OutFile $agentPath
        
        # Create executable wrapper
        $wrapperPath = Join-Path $InstallDir "nocbrain-agent.bat"
        $wrapperContent = @"
@echo off
cd /d "$InstallDir"
python nocbrain-agent.py %*
"@
        $wrapperContent | Out-File -FilePath $wrapperPath -Encoding ASCII
        
        Write-Status "Agent installed successfully"
    }
    catch {
        Write-Error "Failed to install agent: $_"
        exit 1
    }
}

function Create-ConfigFile {
    Write-Status "Creating configuration file..."
    
    $configDir = Join-Path $InstallDir "config"
    $configFile = Join-Path $configDir "config.json"
    
    if (-not (Test-Path $configDir)) {
        New-Item -ItemType Directory -Path $configDir -Force
    }
    
    if (-not (Test-Path $configFile)) {
        if ([string]::IsNullOrEmpty($AgentId)) {
            $AgentId = "$env:COMPUTERNAME-$(Get-Date -Format 'yyyyMMddHHmmss')"
        }
        
        $configContent = @"
{
  "server_url": "$ServerUrl",
  "api_key": "$ApiKey",
  "agent_id": "$AgentId",
  "collection_interval": 60,
  "encryption_enabled": true,
  "compression_enabled": true
}
"@
        
        $configContent | Out-File -FilePath $configFile -Encoding UTF8
        Write-Status "Configuration file created: $configFile"
        
        if ([string]::IsNullOrEmpty($ApiKey)) {
            Write-Warning "Please edit $configFile and set your API key"
        }
    }
    else {
        Write-Warning "Configuration file already exists: $configFile"
    }
}

function Create-WindowsService {
    Write-Status "Creating Windows service..."
    
    try {
        # Check if service already exists
        $service = Get-Service -Name "NOCbRAIN Agent" -ErrorAction SilentlyContinue
        
        if ($service) {
            Write-Warning "Service already exists, updating..."
            Stop-Service -Name "NOCbRAIN Agent" -Force
            Remove-Service -Name "NOCbRAIN Agent" -Force
        }
        
        # Create service using New-Service
        $serviceName = "NOCbRAIN Agent"
        $displayName = "NOCbRAIN Monitoring Agent"
        $description = "NOCbRAIN AI Network Operations Center Monitoring Agent"
        $binaryPath = "python `"$InstallDir\nocbrain-agent.py`" --config `"$configFile`""
        
        New-Service -Name $serviceName -DisplayName $displayName -Description $description -BinaryPathName $binaryPath -StartupType Automatic
        
        Write-Status "Windows service created successfully"
    }
    catch {
        Write-Error "Failed to create Windows service: $_"
        Write-Status "Trying alternative method with NSSM..."
        
        # Try using NSSM (Non-Sucking Service Manager)
        try {
            $nssmUrl = "https://nssm.cc/release/nssm-2.24.zip"
            $nssmZip = Join-Path $env:TEMP "nssm.zip"
            $nssmDir = Join-Path $InstallDir "nssm"
            
            Invoke-WebRequest -Uri $nssmUrl -OutFile $nssmZip
            Expand-Archive -Path $nssmZip -DestinationPath $nssmDir -Force
            
            $nssmExe = Join-Path $nssmDir "win64\nssm.exe"
            & $nssmExe install "NOCbRAIN Agent" "python `"$InstallDir\nocbrain-agent.py`" --config `"$configFile`""
            
            Write-Status "Service created with NSSM"
        }
        catch {
            Write-Error "Failed to create service with NSSM: $_"
            Write-Warning "You'll need to run the agent manually or create the service manually"
        }
    }
}

function Start-Service {
    Write-Status "Starting NOCbRAIN agent service..."
    
    try {
        Start-Service -Name "NOCbRAIN Agent"
        
        # Wait a bit and check status
        Start-Sleep -Seconds 3
        
        $service = Get-Service -Name "NOCbRAIN Agent"
        if ($service.Status -eq "Running") {
            Write-Status "NOCbRAIN agent service is running"
        } else {
            Write-Error "Failed to start NOCbRAIN agent service"
            Write-Status "Service status: $($service.Status)"
            exit 1
        }
    }
    catch {
        Write-Error "Failed to start service: $_"
        exit 1
    }
}

function Set-FirewallRules {
    Write-Status "Configuring Windows Firewall..."
    
    try {
        # Check if firewall is enabled
        $firewallProfile = Get-NetFirewallProfile -Profile Domain,Public,Private
        
        if ($firewallProfile.Enabled) {
            # Add outbound rule for HTTPS (agent typically uses outbound connections)
            $ruleName = "NOCbRAIN Agent Outbound"
            $existingRule = Get-NetFirewallRule -DisplayName $ruleName -ErrorAction SilentlyContinue
            
            if (-not $existingRule) {
                New-NetFirewallRule -DisplayName $ruleName -Direction Outbound -Protocol TCP -RemotePort 443 -Action Allow -Description "Allow NOCbRAIN agent to communicate with server"
                Write-Status "Firewall rule created: $ruleName"
            } else {
                Write-Warning "Firewall rule already exists: $ruleName"
            }
        } else {
            Write-Warning "Windows Firewall is not enabled"
        }
    }
    catch {
        Write-Warning "Failed to configure firewall: $_"
    }
}

function Show-Status {
    Write-Status "Installation completed successfully!"
    Write-Host ""
    Write-Host "Agent Information:" -ForegroundColor Blue
    Write-Host "  - Installation directory: $InstallDir"
    Write-Host "  - Configuration file: $configFile"
    Write-Host "  - Service name: NOCbRAIN Agent"
    Write-Host ""
    Write-Host "Management Commands:" -ForegroundColor Blue
    Write-Host "  - Start service: Start-Service 'NOCbRAIN Agent'"
    Write-Host "  - Stop service: Stop-Service 'NOCbRAIN Agent'"
    Write-Host "  - Restart service: Restart-Service 'NOCbRAIN Agent'"
    Write-Host "  - Check status: Get-Service 'NOCbRAIN Agent'"
    Write-Host "  - View logs: Get-EventLog -LogName Application -Source 'NOCbRAIN Agent' -Newest 10"
    Write-Host ""
    Write-Host "Next Steps:" -ForegroundColor Blue
    Write-Host "  1. Edit configuration: notepad `"$configFile`""
    Write-Host "  2. Set your API key"
    Write-Host "  3. Restart service: Restart-Service 'NOCbRAIN Agent'"
    Write-Host ""
}

function Uninstall-Agent {
    Write-Status "Uninstalling NOCbRAIN agent..."
    
    try {
        # Stop and remove service
        Stop-Service -Name "NOCbRAIN Agent" -Force -ErrorAction SilentlyContinue
        Remove-Service -Name "NOCbRAIN Agent" -Force -ErrorAction SilentlyContinue
        
        # Remove firewall rule
        Remove-NetFirewallRule -DisplayName "NOCbRAIN Agent Outbound" -ErrorAction SilentlyContinue
        
        # Remove installation directory
        if (Test-Path $InstallDir) {
            Remove-Item -Path $InstallDir -Recurse -Force
        }
        
        Write-Status "NOCbRAIN agent uninstalled successfully"
    }
    catch {
        Write-Error "Failed to uninstall agent: $_"
    }
}

function Update-Agent {
    Write-Status "Updating NOCbRAIN agent..."
    
    try {
        Stop-Service -Name "NOCbRAIN Agent" -Force
        Install-Agent
        Start-Service
        Write-Status "NOCbRAIN agent updated successfully"
    }
    catch {
        Write-Error "Failed to update agent: $_"
    }
}

# Main execution
try {
    Write-Header
    
    if ($Uninstall) {
        Test-AdminPrivileges
        Uninstall-Agent
    }
    elseif ($Update) {
        Test-AdminPrivileges
        Update-Agent
    }
    else {
        Test-AdminPrivileges
        Install-PythonDependencies
        Create-InstallDirectory
        Install-Agent
        Create-ConfigFile
        Create-WindowsService
        Set-FirewallRules
        Start-Service
        Show-Status
    }
}
catch {
    Write-Error "Installation failed: $_"
    exit 1
}
