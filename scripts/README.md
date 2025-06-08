# 🎯 Focus Timer - Global Alias Setup

This document explains how to set up and use global aliases for the Focus Timer application, allowing you to run it from anywhere on your system.

## 🚀 Quick Installation

Run the installation script from the Focus Timer directory:

```powershell
cd "c:\Users\ahm_e\AppData\Local\focus"
.\scripts\install-alias.ps1
```

## 🎛️ Available Commands

Once installed, you can use these commands from any directory:

### Basic Commands

```powershell
focus                    # Interactive launcher
focus gui               # Launch GUI mode
focus console           # Launch console mode
focus dashboard         # Open analytics dashboard
focus stats             # Show productivity statistics
```

### Session Commands

```powershell
focus quick              # 25-minute focus session (default)
focus quick 30           # 30-minute focus session
focus break              # 5-minute break (default)
focus break 10           # 10-minute break
```

### System Commands

```powershell
focus check             # Check system dependencies
focus info              # Show system information
```

### Convenient Shortcuts

```powershell
focus-quick 25          # Quick 25-minute session
focus-break 5           # Quick 5-minute break
focus-gui               # Launch GUI
focus-console           # Launch console
focus-dashboard         # Open dashboard
focus-stats             # Show stats
```

## 🔧 Manual Installation

If the automatic installation doesn't work, you can set up the aliases manually:

### PowerShell Profile Method

1. Open PowerShell and check your profile location:

   ```powershell
   echo $PROFILE.CurrentUserAllHosts
   ```

2. Edit your PowerShell profile:

   ```powershell
   notepad $PROFILE.CurrentUserAllHosts
   ```

3. Add this function to your profile:

   ```powershell
   function focus {
       param(
           [string]$Mode = "",
           [int]$Duration = 0
       )
       & "c:\Users\ahm_e\AppData\Local\focus\scripts\focus.ps1" $Mode $Duration
   }
   ```

4. Reload your profile:
   ```powershell
   . $PROFILE.CurrentUserAllHosts
   ```

### PATH Environment Variable Method

1. Add the scripts directory to your PATH:

   ```
   c:\Users\ahm_e\AppData\Local\focus\scripts
   ```

2. You can then use:
   ```cmd
   focus.bat gui
   focus.bat quick 25
   ```

### Git Bash / WSL Method

1. Add to your `.bashrc` or `.bash_profile`:

   ```bash
   alias focus='/c/Users/ahm_e/AppData/Local/focus/scripts/focus.sh'
   ```

2. Reload your shell:
   ```bash
   source ~/.bashrc
   ```

## 🎨 Customization

You can modify the scripts in the `scripts/` directory to:

- Change default session durations
- Add new commands
- Customize the launch behavior
- Add additional shortcuts

## 🛠️ Files Created

The installation creates these files:

- `scripts/focus.ps1` - PowerShell launcher script
- `scripts/focus.bat` - Windows Command Prompt batch file
- `scripts/focus.sh` - Git Bash / WSL shell script
- `scripts/install-alias.ps1` - Installation script

## 📝 Usage Examples

```powershell
# Start a quick 25-minute focus session
focus quick 25

# Take a 10-minute break
focus break 10

# Open the GUI from any directory
focus gui

# Check today's productivity stats
focus stats

# Open the analytics dashboard
focus dashboard

# Start interactive mode
focus
```

## 🔍 Troubleshooting

### "Command not found" Error

- Restart your terminal after installation
- Ensure the PowerShell profile was created correctly
- Check that the scripts directory is in your PATH

### Permission Errors

- Run the installation script as Administrator
- Manually set execution policy: `Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser`

### Virtual Environment Issues

- Ensure the virtual environment exists at `c:\Users\ahm_e\AppData\Local\focus\.venv`
- Recreate the virtual environment if necessary

### Script Path Issues

- Verify all paths in the scripts are correct
- Update paths if you've moved the Focus Timer installation

## 🎯 Benefits

- **Global Access**: Run Focus Timer from any directory
- **Quick Sessions**: Start sessions with simple commands
- **Multiple Shells**: Works with PowerShell, Command Prompt, and Git Bash
- **Convenient Shortcuts**: Pre-defined commands for common tasks
- **Virtual Environment**: Automatically handles venv activation

## 📞 Support

If you encounter issues:

1. Check the troubleshooting section above
2. Verify your virtual environment setup
3. Ensure all dependencies are installed
4. Check file permissions on the script files

Enjoy your enhanced productivity workflow! 🚀
