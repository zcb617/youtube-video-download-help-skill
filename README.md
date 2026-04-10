# YouTube Clipper Skill

> AI-powered YouTube video clipper for Claude Code. Download videos, generate semantic chapters, clip segments, translate subtitles to bilingual format, and burn subtitles into videos.

[![License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)
[![Python](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)

English | [简体中文](README.zh-CN.md)

[Features](#features) • [Installation](#installation) • [Usage](#usage) • [Requirements](#requirements) • [Configuration](#configuration) • [Troubleshooting](#troubleshooting)

---

⚠️ **IMPORTANT LEGAL NOTICE**

This tool uses **PO Token** to bypass YouTube's anti-bot verification. **This violates YouTube's Terms of Service** and carries significant risks:

- **IP Ban**: YouTube may block your IP address temporarily or permanently
- **Account Suspension**: Associated Google accounts may be suspended
- **Legal Action**: Bulk downloading may result in DMCA notices
- **ToS Violation**: Circumventing security features violates [YouTube's Terms](https://www.youtube.com/t/terms)

**By using this tool, you acknowledge that:**
1. You are solely responsible for any consequences
2. You will not use it for commercial redistribution
3. You understand this is an ongoing arms race that may stop working at any time

**This tool is provided for educational/research purposes only. Use at your own risk.**

See [PO Token Risks](#po-token-risks-and-considerations) section for details.

---

## Features

- **AI Semantic Analysis** - Generate fine-grained chapters (2-5 minutes each) by understanding video content, not just mechanical time splitting
- **Precise Clipping** - Use FFmpeg to extract video segments with frame-accurate timing
- **Bilingual Subtitles** - Batch translate subtitles to Chinese/English with 95% API call reduction
- **Subtitle Burning** - Hardcode bilingual subtitles into videos with customizable styling
- **Content Summarization** - Auto-generate social media content (Xiaohongshu, Douyin, WeChat)

---

## Installation

### Option 1: npx skills (Recommended)

```bash
npx skills add https://github.com/zcb617/youtube-video-download-help-skill
```

This command will automatically install the skill to `~/.claude/skills/youtube-clipper/`.

### Option 2: Manual Installation (macOS/Linux)

```bash
git clone https://github.com/zcb617/youtube-video-download-help-skill.git
cd youtube-video-download-help-skill
bash install_as_skill.sh
```

The install script will:
- Copy files to `~/.claude/skills/youtube-clipper/`
- Install Python dependencies (yt-dlp, pysrt, python-dotenv)
- Check system dependencies (Python, yt-dlp, FFmpeg)
- Create `.env` configuration file

### Option 3: Windows Installation

```powershell
# Clone the repository
git clone https://github.com/zcb617/youtube-video-download-help-skill.git
cd youtube-video-download-help-skill

# Run PowerShell install script
powershell -ExecutionPolicy Bypass -File install_as_skill.ps1
```

The PowerShell script will:
- Copy files to `%USERPROFILE%\.claude\skills\youtube-clipper\`
- Install Python dependencies
- Check system dependencies (Python, yt-dlp, FFmpeg, Node.js)
- Create `.env` configuration file
- Create helper batch scripts

---

## Requirements

### System Dependencies

| Dependency | Version | Purpose | Installation (macOS / Linux / Windows) |
|------------|---------|---------|----------------------------------------|
| **Python** | 3.8+ | Script execution | [python.org](https://www.python.org/downloads/) |
| **yt-dlp** | Latest | YouTube download | `brew install yt-dlp` / `sudo apt install yt-dlp` / `winget install yt-dlp` |
| **FFmpeg with libass** | Latest | Video processing & subtitle burning | `brew install ffmpeg-full` / `sudo apt install ffmpeg libass-dev` / `winget install ffmpeg` |
| **Node.js** | 20+ | PO Token generation | [nodejs.org](https://nodejs.org/) or `winget install OpenJS.NodeJS` |

### PO Token Provider (Required for YouTube Download)

**⚠️ IMPORTANT**: YouTube now requires PO Token for all downloads. Cookies alone are no longer sufficient.

#### What is PO Token?

**PO Token (Proof of Origin Token)** is YouTube's anti-bot verification mechanism. It replaced the older cookie-based authentication in 2024-2025.

**Key Characteristics**:
- **Short-lived**: Expires in minutes to hours (unlike cookies that last days/weeks)
- **Device-bound**: Generated using browser fingerprints (Canvas, WebGL, fonts, etc.)
- **Computationally expensive**: Requires executing JavaScript challenges in a real browser environment

#### Why Cookies No Longer Work

| Aspect | Cookie Era | PO Token Era |
|--------|-----------|--------------|
| Verification target | Account identity | Device + Behavior + Time |
| Token lifetime | Days to weeks | Minutes to hours |
| Generation method | Issued at login | Real-time JS computation |
| Detection points | HTTP headers only | Complete browser environment |

YouTube now requires a **fresh PO Token** for each playback request. The token must be generated in a real browser environment, making simple HTTP requests with cookies insufficient.

#### Technical Architecture

```
┌─────────┐     ┌─────────────────┐     ┌─────────────┐     ┌─────────┐
│ yt-dlp  │────▶│  PO Token       │────▶│  Headless   │────▶│ YouTube │
│         │◄────│  Provider       │◄────│  Chrome     │◄────│         │
└─────────┘     │  (Node.js)      │     └─────────────┘     └─────────┘
                └─────────────────┘
                        │
                        ▼
                ┌───────────────┐
                │ JavaScript    │
                │ Challenge     │
                │ (botguard.js) │
                └───────────────┘
```

**How it works**:
1. YouTube returns encrypted JavaScript code (`botguard.js`)
2. Code must execute in a **real browser** (V8 engine, Web APIs, etc.)
3. Browser fingerprints collected: Canvas, WebGL, fonts, timezone, screen resolution
4. PO Token generated through obfuscated algorithm
5. Token included in subsequent video requests

#### Installation

**Step 1: Install Python package**
```bash
pip install bgutil-ytdlp-pot-provider
```

**Step 2: Clone and build the provider service**
```bash
git clone --single-branch --branch 1.3.1 https://github.com/Brainicism/bgutil-ytdlp-pot-provider.git
cd bgutil-ytdlp-pot-provider/server
npm ci && npx tsc
```

**Step 3: Start the service**
```bash
node build/main.js
# Service runs on http://127.0.0.1:4416
```

**Step 4: Configure in `.env`**
```bash
PO_TOKEN_ENABLED=true
PO_TOKEN_PROVIDER_URL=http://127.0.0.1:4416
```

**Note**: The PO Token Provider must run locally because:
- Token generation depends on real browser environment
- YouTube detects if tokens are generated on remote servers
- Shared tokens would have identical device fingerprints (detectable)
- Timestamps must match network latency patterns

#### Why It's Free

The `bgutil-ytdlp-pot-provider` is an **open-source project** (GitHub: `Brainicism/bgutil-ytdlp-pot-provider`). It uses your local machine's resources (Node.js + Chromium) to generate tokens, not a paid API service.

**Trade-offs**:
- ✅ Free and open-source
- ✅ More reliable than cookies
- ⚠️ Requires Node.js 20+ and ~500MB disk space for Chromium
- ⚠️ Slower initial startup (browser launch time)
- ⚠️ Ongoing arms race with YouTube's detection systems

#### ⚠️ Risks and Considerations

**Terms of Service Violation**  
Using PO Token to bypass YouTube's anti-bot measures violates [YouTube's Terms of Service](https://www.youtube.com/t/terms), specifically:
- Section 4.C: Prohibition on circumventing any security features
- Section 5: Restrictions on automated access (bots, scrapers)

**Potential Consequences**:
- **IP Ban**: YouTube may temporarily or permanently block your IP address
- **Rate Limiting**: Aggressive downloading may trigger throttling
- **Account Suspension**: If using logged-in sessions, associated Google accounts may be suspended
- **Legal Action**: While rare for personal use, bulk downloading may result in DMCA notices or legal action

**Mitigation Strategies**:
- Use residential IP (avoid datacenter/VPN IPs)
- Limit download frequency (avoid concurrent downloads)
- Don't distribute downloaded content commercially
- Consider using YouTube's official API for legitimate use cases

**No Guarantee**  
PO Token is part of an ongoing arms race with YouTube. The method may stop working at any time if YouTube updates their detection systems. This tool is provided as-is with no warranty.

### Python Packages

These are automatically installed by the install script:
- `yt-dlp` - YouTube downloader
- `pysrt` - SRT subtitle parser
- `python-dotenv` - Environment variable management

### Important: FFmpeg libass Support

**macOS users**: The standard `ffmpeg` package from Homebrew does NOT include libass support (required for subtitle burning). You must install `ffmpeg-full`:

```bash
# Remove standard ffmpeg (if installed)
brew uninstall ffmpeg

# Install ffmpeg-full (includes libass)
brew install ffmpeg-full
```

**Windows users**: Install FFmpeg using winget (official Gyan's builds include libass):

```powershell
# Install FFmpeg with all codecs and libass
winget install ffmpeg

# Or use Chocolatey
choco install ffmpeg-full

# Or use Scoop
scoop install ffmpeg
```

**Verify libass support**:

```bash
# macOS/Linux
ffmpeg -filters 2>&1 | grep subtitles

# Windows (Command Prompt or PowerShell)
ffmpeg -filters | findstr subtitles

# Should output: subtitles    V->V  (...)
```

---

## Usage

### In Claude Code

Simply tell Claude to clip a YouTube video:

```
Clip this YouTube video: https://youtube.com/watch?v=VIDEO_ID
```

or

```
剪辑这个 YouTube 视频：https://youtube.com/watch?v=VIDEO_ID
```

### Workflow

1. **Environment Check** - Verifies yt-dlp, FFmpeg, and Python dependencies
2. **Video Download** - Downloads video (up to 1080p) and English subtitles
3. **AI Chapter Analysis** - Claude analyzes subtitles to generate semantic chapters (2-5 min each)
4. **User Selection** - Choose which chapters to clip and processing options
5. **Processing** - Clips video, translates subtitles, burns subtitles (if requested)
6. **Output** - Organized files in `./youtube-clips/<timestamp>/`

### Output Files

For each clipped chapter:

```
./youtube-clips/20260122_143022/
└── Chapter_Title/
    ├── Chapter_Title_clip.mp4              # Original clip (no subtitles)
    ├── Chapter_Title_with_subtitles.mp4    # With burned subtitles
    ├── Chapter_Title_bilingual.srt         # Bilingual subtitle file
    └── Chapter_Title_summary.md            # Social media content
```

---

## Configuration

The skill uses environment variables for customization. Edit `~/.claude/skills/youtube-clipper/.env`:

### Key Settings

```bash
# FFmpeg path (auto-detected if empty)
FFMPEG_PATH=

# Output directory (default: current working directory)
OUTPUT_DIR=./youtube-clips

# Video quality limit (720, 1080, 1440, 2160)
MAX_VIDEO_HEIGHT=1080

# Translation batch size (20-25 recommended)
TRANSLATION_BATCH_SIZE=20

# Target language for translation
TARGET_LANGUAGE=中文

# Target chapter duration in seconds (180-300 recommended)
TARGET_CHAPTER_DURATION=180
```

For full configuration options, see [.env.example](.env.example).

---

## Examples

### Example 1: Extract highlights from a tech interview

**Input**:
```
Clip this video: https://youtube.com/watch?v=Ckt1cj0xjRM
```

**Output** (AI-generated chapters):
```
1. [00:00 - 03:15] AGI as an exponential curve, not a point in time
2. [03:15 - 06:30] China's gap in AI development
3. [06:30 - 09:45] The impact of chip bans
...
```

**Result**: Select chapters → Get clipped videos with bilingual subtitles + social media content

### Example 2: Create short clips from a course

**Input**:
```
Clip this lecture video and create bilingual subtitles: https://youtube.com/watch?v=LECTURE_ID
```

**Options**:
- Generate bilingual subtitles: Yes
- Burn subtitles into video: Yes
- Generate summary: Yes

**Result**: High-quality clips ready for sharing on social media platforms

---

## Key Differentiators

### AI Semantic Chapter Analysis

Unlike mechanical time-based splitting, this skill uses Claude's AI to:
- Understand content semantics
- Identify natural topic transitions
- Generate meaningful chapter titles and summaries
- Ensure complete coverage with no gaps

**Example**:
```
❌ Mechanical splitting: [0:00-30:00], [30:00-60:00]
✅ AI semantic analysis:
   - [00:00-03:15] AGI definition
   - [03:15-07:30] China's AI landscape
   - [07:30-12:00] Chip ban impacts
```

### Batch Translation Optimization

Translates 20 subtitles at once instead of one-by-one:
- 95% reduction in API calls
- 10x faster translation
- Better translation consistency

### Bilingual Subtitle Format

Generated subtitle files contain both English and Chinese:

```srt
1
00:00:00,000 --> 00:00:03,500
This is the English subtitle
这是中文字幕

2
00:00:03,500 --> 00:00:07,000
Another English line
另一行中文
```

---

## Troubleshooting

### FFmpeg subtitle burning fails

**Error**: `Option not found: subtitles` or `filter not found`

**Solution**: Install `ffmpeg-full` (macOS) or ensure `libass-dev` is installed (Ubuntu):
```bash
# macOS
brew uninstall ffmpeg
brew install ffmpeg-full

# Ubuntu
sudo apt install ffmpeg libass-dev
```

### Video download is slow

**Solution**: Set a proxy in `.env`:
```bash
YT_DLP_PROXY=http://proxy-server:port
# or
YT_DLP_PROXY=socks5://proxy-server:port
```

### Subtitle translation fails

**Cause**: API rate limiting or network issues

**Solution**: The skill automatically retries up to 3 times. If persistent, check:
- Network connectivity
- Claude API status
- Reduce `TRANSLATION_BATCH_SIZE` in `.env`

### Special characters in filenames

**Issue**: Filenames with `:`, `/`, `?`, etc. may cause errors

**Solution**: The skill automatically sanitizes filenames by:
- Removing special characters: `/ \ : * ? " < > |`
- Replacing spaces with underscores
- Limiting length to 100 characters

### Windows PowerShell execution policy error

**Error**: `cannot be loaded because running scripts is disabled on this system`

**Solution**: Run PowerShell with Bypass policy:
```powershell
powershell -ExecutionPolicy Bypass -File install_as_skill.ps1
```

Or change execution policy for current user:
```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

### Windows: yt-dlp or ffmpeg not found after installation

**Issue**: Command not recognized in PowerShell/CMD after winget install

**Solution**: Refresh PATH environment variable or restart terminal:
```powershell
# Refresh PATH in current PowerShell session
$env:Path = [System.Environment]::GetEnvironmentVariable("Path", "Machine") + ";" + [System.Environment]::GetEnvironmentVariable("Path", "User")
```

Or restart PowerShell/Command Prompt after installation.

### Windows: PO Token Provider service won't start

**Issue**: `node is not recognized` or `npm is not recognized`

**Solution**:
1. Verify Node.js installation:
   ```powershell
   node --version
   npm --version
   ```

2. If not found, install via winget:
   ```powershell
   winget install OpenJS.NodeJS
   ```

3. Restart terminal and try again

---


## New Features

### PO Token Support (2026-04-10)

Added **PO Token authentication** for YouTube downloads. See [PO Token Provider](#po-token-provider-required-for-youtube-download) section above for:
- Technical architecture and why cookies no longer work
- Detailed installation instructions
- Technical background on JavaScript challenges and browser fingerprinting

Quick setup:
```bash
pip install bgutil-ytdlp-pot-provider
# Start the provider service (see detailed instructions above)
```

### Whisper GPU Transcription (2026-04-10)

Added `whisper_gpu.py` for automatic GPU selection and subtitle generation:

**Features**:
- Auto-detect GPU memory
- Auto-switch to best GPU if specified GPU has < 4GB memory
- CPU fallback when no GPU available
- Support `.env` configuration

**Usage**:
```bash
# Auto-select best GPU
python scripts/whisper_gpu.py video.mp4

# Specify GPU
python scripts/whisper_gpu.py video.mp4 --gpu 0

# Force CPU
python scripts/whisper_gpu.py video.mp4 --cpu
```

**Configuration (`.env`)**:
```bash
WHISPER_MODEL=medium
WHISPER_LANGUAGE=zh
WHISPER_MIN_MEMORY=4096
WHISPER_FORCE_CPU=false
```

## Documentation

- **[SKILL.md](SKILL.md)** - Complete workflow and technical details
- **[TECHNICAL_NOTES.md](TECHNICAL_NOTES.md)** - Implementation notes and design decisions
- **[FIXES_AND_IMPROVEMENTS.md](FIXES_AND_IMPROVEMENTS.md)** - Changelog and bug fixes
- **[references/](references/)** - FFmpeg, yt-dlp, and subtitle formatting guides

---

## Contributing

Contributions are welcome! Please:
- Report bugs via [GitHub Issues](https://github.com/zcb617/youtube-video-download-help-skill/issues)
- Submit feature requests
- Open pull requests for improvements

---

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

## Acknowledgements

- **[Claude Code](https://claude.ai/claude-code)** - The AI-powered CLI tool
- **[yt-dlp](https://github.com/yt-dlp/yt-dlp)** - YouTube download engine
- **[FFmpeg](https://ffmpeg.org/)** - Video processing powerhouse

---

<div align="center">

**Made with ❤️ by [zcb617](https://github.com/zcb617)**

If this skill helps you, please give it a ⭐️

</div>
