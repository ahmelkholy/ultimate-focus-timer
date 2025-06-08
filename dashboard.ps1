# Focus Productivity Dashboard
# Analyze and visualize your focus session data

param(
    [string]$Period = "week", # day, week, month, all
    [switch]$Export
)

# Load session data
function Get-SessionData {
    $logPath = "log\focus.log"
    $sessions = @()

    if (Test-Path $logPath) {
        $content = Get-Content $logPath

        foreach ($line in $content) {
            if ($line -match '(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}) - (Started|Completed) (\w+) session.*?(\d+) minutes') {
                $sessions += [PSCustomObject]@{
                    Timestamp = [DateTime]::Parse($matches[1])
                    Action    = $matches[2]
                    Type      = $matches[3]
                    Duration  = [int]$matches[4]
                    Date      = [DateTime]::Parse($matches[1]).Date
                }
            }
        }
    }

    return $sessions
}

# Filter sessions by period
function Get-FilteredSessions {
    param($Sessions, $Period)

    $now = Get-Date
    switch ($Period) {
        "day" {
            $cutoff = $now.Date
            return $Sessions | Where-Object { $_.Timestamp -ge $cutoff }
        }
        "week" {
            $cutoff = $now.AddDays(-7)
            return $Sessions | Where-Object { $_.Timestamp -ge $cutoff }
        }
        "month" {
            $cutoff = $now.AddDays(-30)
            return $Sessions | Where-Object { $_.Timestamp -ge $cutoff }
        }
        default {
            return $Sessions
        }
    }
}

# Calculate statistics
function Get-ProductivityStats {
    param($Sessions)

    $completedSessions = $Sessions | Where-Object { $_.Action -eq "Completed" }
    $workSessions = $completedSessions | Where-Object { $_.Type -eq "work" }
    $breakSessions = $completedSessions | Where-Object { $_.Type -ne "work" }

    $stats = @{
        TotalSessions       = $completedSessions.Count
        WorkSessions        = $workSessions.Count
        BreakSessions       = $breakSessions.Count
        TotalWorkTime       = ($workSessions | Measure-Object -Property Duration -Sum).Sum
        TotalBreakTime      = ($breakSessions | Measure-Object -Property Duration -Sum).Sum
        AverageWorkSession  = if ($workSessions.Count -gt 0) { [math]::Round(($workSessions | Measure-Object -Property Duration -Average).Average, 1) } else { 0 }
        AverageBreakSession = if ($breakSessions.Count -gt 0) { [math]::Round(($breakSessions | Measure-Object -Property Duration -Average).Average, 1) } else { 0 }
        ProductiveHours     = [math]::Round((($workSessions | Measure-Object -Property Duration -Sum).Sum) / 60, 1)
        DaysActive          = ($completedSessions | Group-Object Date).Count
    }

    return $stats
}

# Generate daily breakdown
function Get-DailyBreakdown {
    param($Sessions)

    $completedSessions = $Sessions | Where-Object { $_.Action -eq "Completed" }
    $dailyStats = $completedSessions | Group-Object Date | ForEach-Object {
        $workSessions = $_.Group | Where-Object { $_.Type -eq "work" }
        $workTime = ($workSessions | Measure-Object -Property Duration -Sum).Sum

        [PSCustomObject]@{
            Date         = $_.Name
            Sessions     = $_.Count
            WorkSessions = $workSessions.Count
            WorkMinutes  = $workTime
            WorkHours    = [math]::Round($workTime / 60, 1)
        }
    } | Sort-Object Date -Descending

    return $dailyStats
}

# Display dashboard
function Show-Dashboard {
    param($Stats, $DailyBreakdown, $Period)

    Write-Host "═══════════════════════════════════════════════════════════════" -ForegroundColor Cyan
    Write-Host "                    🎯 FOCUS PRODUCTIVITY DASHBOARD" -ForegroundColor Magenta
    Write-Host "═══════════════════════════════════════════════════════════════" -ForegroundColor Cyan
    Write-Host ""

    Write-Host "📊 SUMMARY ($Period)" -ForegroundColor Yellow
    Write-Host "├─ Total Sessions: $($Stats.TotalSessions)" -ForegroundColor White
    Write-Host "├─ Work Sessions: $($Stats.WorkSessions)" -ForegroundColor Green
    Write-Host "├─ Break Sessions: $($Stats.BreakSessions)" -ForegroundColor Blue
    Write-Host "├─ Productive Hours: $($Stats.ProductiveHours)" -ForegroundColor Magenta
    Write-Host "├─ Days Active: $($Stats.DaysActive)" -ForegroundColor Cyan
    Write-Host "├─ Avg Work Session: $($Stats.AverageWorkSession) min" -ForegroundColor Green
    Write-Host "└─ Avg Break Session: $($Stats.AverageBreakSession) min" -ForegroundColor Blue
    Write-Host ""

    if ($Stats.TotalSessions -gt 0) {
        $workRatio = [math]::Round(($Stats.WorkSessions / $Stats.TotalSessions) * 100, 1)
        Write-Host "📈 PRODUCTIVITY METRICS" -ForegroundColor Yellow
        Write-Host "├─ Work/Break Ratio: $workRatio% work" -ForegroundColor White
        Write-Host "├─ Total Focus Time: $($Stats.TotalWorkTime) minutes" -ForegroundColor Green
        Write-Host "├─ Total Break Time: $($Stats.TotalBreakTime) minutes" -ForegroundColor Blue

        if ($Stats.DaysActive -gt 0) {
            $avgSessionsPerDay = [math]::Round($Stats.TotalSessions / $Stats.DaysActive, 1)
            $avgWorkPerDay = [math]::Round($Stats.TotalWorkTime / $Stats.DaysActive, 1)
            Write-Host "├─ Avg Sessions/Day: $avgSessionsPerDay" -ForegroundColor White
            Write-Host "└─ Avg Work/Day: $avgWorkPerDay minutes" -ForegroundColor Green
        }
        Write-Host ""
    }

    if ($DailyBreakdown.Count -gt 0) {
        Write-Host "📅 DAILY BREAKDOWN (Recent)" -ForegroundColor Yellow
        $DailyBreakdown | Select-Object -First 7 | ForEach-Object {
            $date = [DateTime]::Parse($_.Date).ToString("ddd, MMM dd")
            $bar = "█" * [math]::Min(20, $_.WorkHours * 2)
            Write-Host "├─ $date : $($_.WorkSessions) sessions, $($_.WorkHours)h $bar" -ForegroundColor White
        }
        Write-Host ""
    }

    # Productivity insights
    Write-Host "💡 INSIGHTS" -ForegroundColor Yellow

    if ($Stats.TotalSessions -eq 0) {
        Write-Host "├─ No sessions recorded yet. Start your first focus session!" -ForegroundColor Gray
    }
    elseif ($Stats.ProductiveHours -lt 2) {
        Write-Host "├─ Getting started! Try to reach 2+ hours of focus time daily." -ForegroundColor Yellow
    }
    elseif ($Stats.ProductiveHours -lt 4) {
        Write-Host "├─ Good progress! You're building a solid focus habit." -ForegroundColor Green
    }
    else {
        Write-Host "├─ Excellent focus! You're in the productivity zone! 🔥" -ForegroundColor Green
    }

    if ($Stats.AverageWorkSession -gt 0) {
        if ($Stats.AverageWorkSession -lt 20) {
            Write-Host "├─ Consider longer work sessions for deeper focus." -ForegroundColor Yellow
        }
        elseif ($Stats.AverageWorkSession -gt 45) {
            Write-Host "├─ Great endurance! Consider adding more breaks." -ForegroundColor Blue
        }
        else {
            Write-Host "├─ Perfect session length for optimal focus!" -ForegroundColor Green
        }
    }

    $today = Get-Date
    $todayStats = $DailyBreakdown | Where-Object { [DateTime]::Parse($_.Date).Date -eq $today.Date }
    if ($todayStats) {
        if ($todayStats.WorkHours -eq 0) {
            Write-Host "└─ Haven't started today yet? Your next session is waiting! ⏰" -ForegroundColor Cyan
        }
        elseif ($todayStats.WorkHours -lt 2) {
            Write-Host "└─ Good start today! Keep the momentum going! 🚀" -ForegroundColor Green
        }
        else {
            Write-Host "└─ Fantastic productivity today! You're crushing it! 💪" -ForegroundColor Green
        }
    }
    else {
        Write-Host "└─ Haven't started today yet? Your next session is waiting! ⏰" -ForegroundColor Cyan
    }

    Write-Host ""
    Write-Host "═══════════════════════════════════════════════════════════════" -ForegroundColor Cyan
}

# Export data
function Export-Data {
    param($Sessions, $Stats, $DailyBreakdown)

    $timestamp = Get-Date -Format "yyyyMMdd_HHmmss"
    $exportPath = "exports\focus_data_$timestamp.csv"

    # Ensure export directory exists
    if (!(Test-Path "exports")) {
        New-Item -ItemType Directory -Path "exports" -Force | Out-Null
    }

    # Export raw sessions
    $Sessions | Export-Csv -Path $exportPath -NoTypeInformation

    # Export daily breakdown
    $dailyPath = "exports\daily_breakdown_$timestamp.csv"
    $DailyBreakdown | Export-Csv -Path $dailyPath -NoTypeInformation

    # Export summary stats
    $statsPath = "exports\summary_stats_$timestamp.txt"
    $Stats.GetEnumerator() | ForEach-Object { "$($_.Key): $($_.Value)" } | Out-File -FilePath $statsPath

    Write-Host "Data exported to:" -ForegroundColor Green
    Write-Host "  Sessions: $exportPath" -ForegroundColor White
    Write-Host "  Daily: $dailyPath" -ForegroundColor White
    Write-Host "  Stats: $statsPath" -ForegroundColor White
}

# Main execution
try {
    $allSessions = Get-SessionData
    $filteredSessions = Get-FilteredSessions $allSessions $Period
    $stats = Get-ProductivityStats $filteredSessions
    $dailyBreakdown = Get-DailyBreakdown $filteredSessions

    Show-Dashboard $stats $dailyBreakdown $Period

    if ($Export) {
        Export-Data $filteredSessions $stats $dailyBreakdown
    }

    # Interactive options
    Write-Host "Options:" -ForegroundColor Gray
    Write-Host "  [D]ay / [W]eek / [M]onth / [A]ll periods" -ForegroundColor White
    Write-Host "  [E]xport data / [Q]uit" -ForegroundColor White

    do {
        $choice = Read-Host "`nChoice"
        switch ($choice.ToUpper()) {
            "D" { & $MyInvocation.MyCommand.Path -Period "day" }
            "W" { & $MyInvocation.MyCommand.Path -Period "week" }
            "M" { & $MyInvocation.MyCommand.Path -Period "month" }
            "A" { & $MyInvocation.MyCommand.Path -Period "all" }
            "E" {
                Export-Data $filteredSessions $stats $dailyBreakdown
                continue
            }
            "Q" { break }
            default {
                Write-Host "Invalid choice." -ForegroundColor Red
                continue
            }
        }
        break
    } while ($true)
}
catch {
    Write-Host "Error generating dashboard: $($_.Exception.Message)" -ForegroundColor Red
}

Write-Host "`nKeep focusing and stay productive! 🎯" -ForegroundColor Green
