#!/usr/bin/env pwsh

##############################################################################
# YouTube Clipper - Claude Code Skill Windows Installation Script
#
# Features:
# 1. Create Skill directory
# 2. Copy all necessary files
# 3. Install Python dependencies
# 4. Check system dependencies (yt-dlp, FFmpeg, Node.js)
#
# Usage:
#   powershell -ExecutionPolicy Bypass -File install_as_skill.ps1
##############################################################################

# Error handling: Stop on error
$ErrorActionPreference = "Stop"

# Color output functions
function Write-Info($msg) {
    Write-Host "ℹ️  $msg" -ForegroundColor Blue
}

function Write-Success($msg) {
    Write-Host "✅ $msg" -ForegroundColor Green
}

function Write-Warning($msg) {
    Write-Host "⚠️  $msg" -ForegroundColor Yellow
}

function Write-Error($msg) {
    Write-Host "❌ $msg" -ForegroundColor Red
}

function Write-Header($msg) {
    Write-Host ""
    Write-Host "========================================" -ForegroundColor Cyan
    Write-Host $msg -ForegroundColor Cyan
    Write-Host "========================================" -ForegroundColor Cyan
    Write-Host ""
}

# Check if command exists
function Test-Command($cmd) {
    return [bool](Get-Command -Name $cmd -ErrorAction SilentlyContinue)
}

# Get script directory
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path

# Main function
function Main {
    Write-Header "YouTube Clipper - Claude Code Skill Installation"

    # 1. Determine Skill directory
    $SkillDir = "$env:USERPROFILE\.claude\skills\youtube-clipper"
    Write-Info "Target directory: $SkillDir"

    # 2. Check if already exists
    if (Test-Path $SkillDir) {
        Write-Warning "Skill directory already exists: $SkillDir"
        $response = Read-Host "Overwrite? (y/N)"
        if ($response -ne 'y' -and $response -ne 'Y') {
            Write-Info "Installation cancelled"
            exit 0
        }
        Write-Info "Removing old version..."
        Remove-Item -Recurse -Force $SkillDir
    }

    # 3. Create directory
    Write-Info "Creating Skill directory..."
    New-Item -ItemType Directory -Path $SkillDir -Force | Out-Null
    Write-Success "Directory created"

    # 4. Copy files
    Write-Info "Copying project files..."

    # Get all files except exclusions
    $exclusions = @('.git', 'venv', '__pycache__', 'youtube-clips', '.env', '.gitignore')
    Get-ChildItem -Path $ScriptDir -Exclude $exclusions | ForEach-Object {
        $dest = Join-Path $SkillDir $_.Name
        if ($_.PSIsContainer) {
            Copy-Item -Path $_.FullName -Destination $dest -Recurse -Force
        } else {
            Copy-Item -Path $_.FullName -Destination $dest -Force
        }
    }
    Write-Success "Files copied"

    # 5. Check Python
    Write-Info "Checking Python environment..."
    if (-not (Test-Command "python") -and -not (Test-Command "python3")) {
        Write-Error "Python not found. Please install Python 3.8+ from https://python.org"
        exit 1
    }

    $PythonCmd = if (Test-Command "python3") { "python3" } else { "python" }
    $PythonVersion = & $PythonCmd --version
    Write-Success "Python installed: $PythonVersion"

    # 6. Check pip
    if (-not (Test-Command "pip") -and -not (Test-Command "pip3")) {
        Write-Error "pip not found. Please install pip"
        exit 1
    }
    $PipCmd = if (Test-Command "pip3") { "pip3" } else { "pip" }
    Write-Success "pip installed"

    # 7. Install Python dependencies
    Write-Info "Installing Python dependencies..."
    Set-Location $SkillDir

    & $PipCmd install -q yt-dlp pysrt python-dotenv
    Write-Success "Python dependencies installed (yt-dlp, pysrt, python-dotenv)"

    # 8. Install PO Token Provider (optional)
    Write-Header "Installing PO Token Provider (Optional)"
    Write-Info "PO Token Provider is used to bypass YouTube bot verification"
    Write-Info "This is optional but recommended for better download success"

    # Install Python package
    Write-Info "Installing bgutil-ytdlp-pot-provider..."
    & $PipCmd install -q bgutil-ytdlp-pot-provider 2>$null
    if ($?) {
        Write-Success "PO Token Provider installed"
    } else {
        Write-Warning "PO Token Provider installation failed, will auto-install on first use"
    }

    # Check Node.js
    Write-Info "Checking Node.js..."
    if (Test-Command "node") {
        $NodeVersion = node --version
        $NodeMajor = [int]($NodeVersion -replace 'v', '').Split('.')[0]

        if ($NodeMajor -ge 20) {
            Write-Success "Node.js installed: $NodeVersion"
        } else {
            Write-Warning "Node.js version is too old ($NodeVersion), version 20+ required"
            Write-Info "Please upgrade Node.js: https://nodejs.org/"
        }

        Write-Info ""
        Write-Info "To start PO Token Provider service:"
        Write-Info "  1. Clone service code:"
        Write-Info '     git clone --single-branch --branch 1.3.1 https://github.com/Brainicism/bgutil-ytdlp-pot-provider.git'
        Write-Info "  2. Start service:"
        Write-Info "     cd bgutil-ytdlp-pot-provider\server"
        Write-Info "     npm ci && npx tsc && node build\main.js"
    } else {
        Write-Warning "Node.js not installed, PO Token Provider service cannot start"
        Write-Info ""
        Write-Info "Node.js is required to run PO Token Provider service"
        Write-Info "Recommended: Install from https://nodejs.org/ (LTS version)"
        Write-Info ""
        Write-Info "Alternative using nvm-windows:"
        Write-Info "  1. Install nvm-windows: https://github.com/coreybutler/nvm-windows"
        Write-Info "  2. nvm install 24"
        Write-Info "  3. nvm use 24"
    }

    # 9. Install Whisper (optional)
    Write-Header "Installing Whisper (Optional)"
    Write-Info "Whisper is used for automatic subtitle generation on videos without subtitles"
    Write-Info "This is an optional dependency, CPU-only by default"

    Write-Info "Installing faster-whisper (CPU version)..."
    & $PipCmd install -q faster-whisper 2>$null
    if ($?) {
        Write-Success "faster-whisper installed"
    } else {
        Write-Warning "faster-whisper installation failed, will auto-install on first use"
    }

    # 10. Check yt-dlp
    Write-Info "Checking yt-dlp..."
    if (Test-Command "yt-dlp") {
        $YtDlpVersion = yt-dlp --version
        Write-Success "yt-dlp installed: $YtDlpVersion"
    } else {
        Write-Warning "yt-dlp command line tool not installed"
        Write-Info "Installation:"
        Write-Info "  winget install yt-dlp"
        Write-Info "  or: pip install -U yt-dlp"
    }

    # 11. Check FFmpeg
    Write-Header "Checking FFmpeg (required for subtitle burning)"

    $FFmpegFound = $false
    $LibassSupported = $false

    # Check common Windows FFmpeg paths
    $WindowsPaths = @(
        "C:\ProgramData\chocolatey\bin\ffmpeg.exe",
        "C:\Program Files\FFmpeg\bin\ffmpeg.exe",
        "C:\Program Files (x86)\FFmpeg\bin\ffmpeg.exe",
        "$env:USERPROFILE\scoop\shims\ffmpeg.exe"
    )

    foreach ($path in $WindowsPaths) {
        if (Test-Path $path) {
            Write-Success "FFmpeg found: $path"
            $FFmpegFound = $true

            # Check libass support
            $filters = & $path -filters 2>&1
            if ($filters -match "subtitles") {
                Write-Success "FFmpeg supports libass (subtitle burning available)"
                $LibassSupported = $true
            } else {
                Write-Warning "FFmpeg does not support libass (subtitle burning unavailable)"
            }
            break
        }
    }

    # Check PATH
    if (-not $FFmpegFound) {
        $FfmpegPath = Get-Command ffmpeg -ErrorAction SilentlyContinue
        if ($FfmpegPath) {
            $FFmpegFound = $true
            $Version = ffmpeg -version | Select-Object -First 1
            Write-Success "FFmpeg installed: $Version"

            $filters = ffmpeg -filters 2>&1
            if ($filters -match "subtitles") {
                Write-Success "FFmpeg supports libass (subtitle burning available)"
                $LibassSupported = $true
            } else {
                Write-Warning "FFmpeg does not support libass (subtitle burning unavailable)"
            }
        }
    }

    if (-not $FFmpegFound) {
        Write-Error "FFmpeg not installed"
        Write-Info "Installation:"
        Write-Info "  winget install ffmpeg          # Recommended"
        Write-Info "  or: choco install ffmpeg-full  # Using Chocolatey"
        Write-Info "  or: scoop install ffmpeg       # Using Scoop"
    } elseif (-not $LibassSupported) {
        Write-Warning "FFmpeg missing libass support, subtitle burning will not work"
        Write-Info "Solution: Reinstall FFmpeg with libass support:"
        Write-Info "  winget uninstall ffmpeg"
        Write-Info "  winget install ffmpeg"
    }

    # 12. Create .env file
    Write-Header "Configuration"

    if (Test-Path "$SkillDir\.env.example") {
        Write-Info "Creating .env file..."
        Copy-Item "$SkillDir\.env.example" "$SkillDir\.env"
        Write-Success ".env file created"
        Write-Info "Config file location: $SkillDir\.env"
        Write-Info "To customize: notepad $SkillDir\.env"
    } else {
        Write-Warning ".env.example file not found"
    }

    # 13. Create Windows helper scripts
    Write-Info "Creating Windows helper scripts..."

    # Create start_po_token.bat
    $StartPoTokenContent = @'@echo off
echo Starting PO Token Provider Service...
echo.
echo Prerequisites:
echo 1. Node.js 20+ must be installed
echo 2. PO Token Provider must be cloned: git clone --single-branch --branch 1.3.1 https://github.com/Brainicism/bgutil-ytdlp-pot-provider.git
echo.

if not exist "bgutil-ytdlp-pot-provider\server\package.json" (
    echo ERROR: PO Token Provider not found!
    echo Please clone it first:
    echo git clone --single-branch --branch 1.3.1 https://github.com/Brainicism/bgutil-ytdlp-pot-provider.git
    pause
    exit /b 1
)

cd bgutil-ytdlp-pot-provider\server
npm ci && npx tsc && node build\main.js
pause
'@
    $StartPoTokenContent | Out-File -FilePath "$SkillDir\start_po_token.bat" -Encoding ASCII

    Write-Success "Helper scripts created"

    # 14. Completion
    Write-Header "Installation Complete!"

    Write-Success "YouTube Clipper successfully installed as Claude Code Skill"
    Write-Host ""
    Write-Info "Installation location: $SkillDir"
    Write-Host ""

    # Check dependency status
    if (-not $FFmpegFound -or -not $LibassSupported) {
        Write-Warning "System dependencies incomplete, some features may be unavailable"
        Write-Host ""
    }

    Write-Info "Usage:"
    Write-Info "  In Claude Code, type:"
    Write-Info '  "Clip this YouTube video: https://youtube.com/watch?v=VIDEO_ID"'
    Write-Host ""
    Write-Info "Documentation:"
    Write-Info "  - Skill Guide: $SkillDir\SKILL.md"
    Write-Info "  - Project README: $SkillDir\README.md"
    Write-Info "  - Technical Notes: $SkillDir\TECHNICAL_NOTES.md"
    Write-Host ""
    Write-Success "Enjoy! 🎉"
    Write-Host ""
}

# Error handling
trap {
    Write-Error "Error occurred during installation: $_"
    exit 1
}

# Run main function
Main
