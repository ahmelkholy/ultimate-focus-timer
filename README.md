# Enhanced Focus Terminal

A comprehensive productivity timer application with classical music integration, multiple interfaces, and detailed analytics.

## 🎯 Features

### Core Functionality

- **Pomodoro Timer**: Customizable work and break sessions
- **Classical Music Integration**: Background music via MPV player
- **Multiple Interfaces**: GUI and console versions
- **Smart Notifications**: Visual and audio alerts
- **Productivity Analytics**: Detailed session tracking and insights

### Music Features

- **Automatic Music Playback**: Classical music starts with work sessions
- **Volume Control**: Adjustable music volume
- **Multiple Playlists**: Baroque, Classical, and Piano selections
- **Fade Transitions**: Smooth music transitions between sessions

### Analytics & Tracking

- **Session Logging**: All sessions automatically logged
- **Productivity Dashboard**: Comprehensive analytics with insights
- **Daily Breakdown**: Track daily productivity patterns
- **Export Options**: CSV export for external analysis
- **Trend Analysis**: Weekly and monthly productivity trends

## 🚀 Quick Start

### Method 1: Use the Launcher (Recommended)

```batch
focus.bat
```

or

```powershell
.\launcher.ps1
```

### Method 2: Direct GUI Launch

```powershell
.\focus_gui.ps1
```

### Method 3: Console Mode

```powershell
.\focus_manager.ps1
```

## 📁 File Structure

```
focus/
├── config.yml              # Main configuration file
├── focus.bat               # Windows batch launcher
├── launcher.ps1            # Main launcher with menu
├── focus_gui.ps1           # GUI timer application
├── focus_manager.ps1       # Console timer application
├── dashboard.ps1           # Productivity analytics
├── setup.ps1              # Initial setup script
├── scripts/
│   └── classical_music.ps1 # Music control script
├── static/
│   ├── *.mp3              # Notification sounds
│   └── ...
├── log/
│   └── focus.log          # Session history
└── exports/               # Data exports (created as needed)
```

## ⚙️ Configuration

Edit `config.yml` to customize:

### Session Timings

```yaml
work_mins: 25
short_break_mins: 5
long_break_mins: 15
```

### Classical Music Settings

```yaml
classical_music: true
classical_music_volume: 30
mpv_executable: "mpv"
pause_music_on_break: true
```

### Notifications

```yaml
notify: true
notify_sound: true
notify_early_warning: 2
desktop_notifications: true
```

### UI & Theme

```yaml
dark_theme: true
accent_color: "#00ff00"
animated_transitions: true
```

## 🎵 Music Setup

### Prerequisites

- **MPV Media Player**: Download from [mpv.io](https://mpv.io/)

### Automatic Installation

Run the setup script:

```powershell
.\setup.ps1
```

### Manual Installation

1. Download MPV from https://mpv.io/
2. Extract and add to PATH
3. Or install via package manager:

   ```bash
   # Chocolatey
   choco install mpv

   # Winget
   winget install mpv
   ```

### Music Sources

The application uses YouTube playlists by default:

- Classical Focus Music
- Baroque Masterpieces
- Piano Classics

You can customize playlists in `scripts/classical_music.ps1`.

## 📊 Analytics Dashboard

Access comprehensive productivity analytics:

```powershell
.\dashboard.ps1
```

### Metrics Tracked

- Total sessions and duration
- Work/break ratio
- Average session lengths
- Daily/weekly productivity trends
- Productivity scoring and insights

### Export Options

- CSV format for external analysis
- Daily breakdown reports
- Summary statistics

## 🛠️ Troubleshooting

### Common Issues

**MPV Not Found**

- Ensure MPV is installed and in PATH
- Run `setup.ps1` for guided installation

**PowerShell Execution Policy**

- Run: `Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser`

**No Sound/Music**

- Check MPV installation
- Verify internet connection for YouTube playlists
- Test with: `.\scripts\classical_music.ps1 -Action test`

**GUI Not Working**

- Ensure .NET Framework is installed
- Try console mode: `.\focus_manager.ps1`

## 📈 Usage Tips

### Productivity Best Practices

1. **Start with default 25-minute work sessions**
2. **Take all suggested breaks**
3. **Use classical music for better focus**
4. **Review analytics weekly**
5. **Adjust session lengths based on your patterns**

### Advanced Features

- **Custom Sessions**: Set any duration via GUI
- **Music Control**: Toggle music independently
- **Pause/Resume**: Flexible session management
- **Export Data**: Analyze patterns in Excel/other tools

## 🔧 Customization

### Adding Custom Playlists

Edit `scripts/classical_music.ps1`:

```powershell
$CLASSICAL_PLAYLISTS = @(
    "your-youtube-playlist-url",
    "another-playlist-url"
)
```

### Custom Notification Sounds

Add MP3 files to `static/` folder and update `config.yml`:

```yaml
notify_sound_work: "your-sound.mp3"
notify_sound_break: "your-break-sound.mp3"
```

### Theme Customization

Modify `config.yml`:

```yaml
accent_color: "#your-color"
color_scheme: "custom"
custom_css: "path/to/your.css"
```

## 🤝 Contributing

Feel free to enhance the application:

1. Fork the project
2. Create feature branches
3. Add new functionality
4. Submit pull requests

## 📝 License

This project is open source. Feel free to use and modify as needed.

## 🎉 Acknowledgments

- **MPV Media Player** for audio capabilities
- **Classical music communities** for curated playlists
- **Pomodoro Technique** by Francesco Cirillo

---

**Stay focused and productive! 🎯**
