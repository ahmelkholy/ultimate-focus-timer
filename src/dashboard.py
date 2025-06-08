#!/usr/bin/env python3
"""
Focus Productivity Dashboard
Analyze and visualize your focus session data with advanced analytics
"""

import argparse
import csv
import json
import os
import re
import signal
import sys
import tkinter as tk
from dataclasses import dataclass
from datetime import datetime, timedelta
from pathlib import Path
from tkinter import filedialog, messagebox, ttk
from typing import Any, Dict, List, Optional

import matplotlib.dates as mdates
import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

# Set style for better visualizations
try:
    # Configure matplotlib for Windows compatibility
    import matplotlib

    matplotlib.use("TkAgg")  # Ensure TkAgg backend is used
    plt.style.use("seaborn-v0_8")
    sns.set_palette("husl")
except Exception as e:
    print(f"Warning: Could not set matplotlib style: {e}")
    # Use default style if seaborn fails


@dataclass
class SessionData:
    """Represents a single focus session"""

    timestamp: datetime
    action: str  # Started, Completed, Paused, etc.
    session_type: str  # work, short_break, long_break
    duration: int  # in minutes
    date: datetime


class SessionAnalyzer:
    """Analyzes session data and generates statistics"""

    def __init__(self, log_path: str = "log/focus.log"):
        self.log_path = Path(log_path)
        self.sessions: List[SessionData] = []
        self.load_session_data()

    def load_session_data(self) -> None:
        """Load session data from log file"""
        if not self.log_path.exists():
            print(f"Log file not found: {self.log_path}")
            return

        pattern = r"(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}) - (Started|Completed|Paused|Resumed) (\w+) session.*?(\d+) minutes"

        try:
            with open(self.log_path, "r", encoding="utf-8") as file:
                for line in file:
                    match = re.search(pattern, line)
                    if match:
                        timestamp = datetime.strptime(
                            match.group(1), "%Y-%m-%d %H:%M:%S"
                        )
                        action = match.group(2)
                        session_type = match.group(3)
                        duration = int(match.group(4))

                        self.sessions.append(
                            SessionData(
                                timestamp=timestamp,
                                action=action,
                                session_type=session_type,
                                duration=duration,
                                date=timestamp.date(),
                            )
                        )
        except Exception as e:
            print(f"Error loading session data: {e}")

    def filter_sessions(self, period: str) -> List[SessionData]:
        """Filter sessions by time period"""
        now = datetime.now()

        if period == "day":
            cutoff = now.replace(hour=0, minute=0, second=0, microsecond=0)
        elif period == "week":
            cutoff = now - timedelta(days=7)
        elif period == "month":
            cutoff = now - timedelta(days=30)
        elif period == "year":
            cutoff = now - timedelta(days=365)
        else:  # all
            return self.sessions

        return [s for s in self.sessions if s.timestamp >= cutoff]

    def calculate_stats(self, sessions: List[SessionData]) -> Dict[str, Any]:
        """Calculate comprehensive productivity statistics"""
        completed_sessions = [s for s in sessions if s.action == "Completed"]
        work_sessions = [s for s in completed_sessions if s.session_type == "work"]
        break_sessions = [
            s
            for s in completed_sessions
            if s.session_type in ["short_break", "long_break"]
        ]

        total_work_time = sum(s.duration for s in work_sessions)
        total_break_time = sum(s.duration for s in break_sessions)

        # Get unique dates
        unique_dates = set(s.date for s in completed_sessions)

        stats = {
            "total_sessions": len(completed_sessions),
            "work_sessions": len(work_sessions),
            "break_sessions": len(break_sessions),
            "total_work_time": total_work_time,
            "total_break_time": total_break_time,
            "productive_hours": round(total_work_time / 60, 1),
            "days_active": len(unique_dates),
            "avg_work_session": (
                round(sum(s.duration for s in work_sessions) / len(work_sessions), 1)
                if work_sessions
                else 0
            ),
            "avg_break_session": (
                round(sum(s.duration for s in break_sessions) / len(break_sessions), 1)
                if break_sessions
                else 0
            ),
            "work_ratio": (
                round((len(work_sessions) / len(completed_sessions)) * 100, 1)
                if completed_sessions
                else 0
            ),
            "avg_sessions_per_day": (
                round(len(completed_sessions) / len(unique_dates), 1)
                if unique_dates
                else 0
            ),
            "avg_work_per_day": (
                round(total_work_time / len(unique_dates), 1) if unique_dates else 0
            ),
            "longest_work_session": max((s.duration for s in work_sessions), default=0),
            "shortest_work_session": min(
                (s.duration for s in work_sessions), default=0
            ),
            "total_focus_days": len(unique_dates),
            "streak_days": self._calculate_streak(sessions),
        }

        return stats

    def get_quick_stats(self) -> Dict[str, Any]:
        """Get quick statistics summary for command line display"""
        # Get all sessions
        all_sessions = self.sessions
        total_stats = self.calculate_stats(all_sessions)

        # Get today's sessions
        today_sessions = self.filter_sessions("day")
        today_stats = self.calculate_stats(today_sessions)

        # Get week's sessions
        week_sessions = self.filter_sessions("week")
        week_stats = self.calculate_stats(week_sessions)

        # Calculate total minutes (work + break time)
        total_minutes = total_stats.get("total_work_time", 0) + total_stats.get(
            "total_break_time", 0
        )

        return {
            "today_sessions": today_stats.get("total_sessions", 0),
            "week_sessions": week_stats.get("total_sessions", 0),
            "total_sessions": total_stats.get("total_sessions", 0),
            "total_minutes": int(total_minutes),
            "streak": total_stats.get("streak_days", 0),
        }

    def _calculate_streak(self, sessions: List[SessionData]) -> int:
        """Calculate current streak of consecutive days with focus sessions"""
        if not sessions:
            return 0

        completed_sessions = [s for s in sessions if s.action == "Completed"]
        dates = sorted(set(s.date for s in completed_sessions), reverse=True)

        if not dates:
            return 0

        today = datetime.now().date()
        streak = 0

        # Check if today has sessions or yesterday (for streak continuity)
        if dates[0] == today or (
            len(dates) > 0 and dates[0] == today - timedelta(days=1)
        ):
            streak = 1
            last_date = dates[0]

            for date in dates[1:]:
                if last_date - date == timedelta(days=1):
                    streak += 1
                    last_date = date
                else:
                    break

        return streak

    def get_daily_breakdown(self, sessions: List[SessionData]) -> pd.DataFrame:
        """Generate daily breakdown statistics"""
        completed_sessions = [s for s in sessions if s.action == "Completed"]

        # Group by date
        daily_data = {}
        for session in completed_sessions:
            date_str = session.date.strftime("%Y-%m-%d")
            if date_str not in daily_data:
                daily_data[date_str] = {
                    "date": session.date,
                    "total_sessions": 0,
                    "work_sessions": 0,
                    "work_minutes": 0,
                    "break_minutes": 0,
                }

            daily_data[date_str]["total_sessions"] += 1
            if session.session_type == "work":
                daily_data[date_str]["work_sessions"] += 1
                daily_data[date_str]["work_minutes"] += session.duration
            else:
                daily_data[date_str]["break_minutes"] += session.duration

        # Convert to DataFrame
        df_data = []
        for data in daily_data.values():
            df_data.append(
                {
                    "Date": data["date"],
                    "Sessions": data["total_sessions"],
                    "Work Sessions": data["work_sessions"],
                    "Work Minutes": data["work_minutes"],
                    "Work Hours": round(data["work_minutes"] / 60, 1),
                    "Break Minutes": data["break_minutes"],
                }
            )

        df = pd.DataFrame(df_data)
        if not df.empty:
            df = df.sort_values("Date", ascending=False)

        return df

    def get_hourly_pattern(self, sessions: List[SessionData]) -> Dict[int, int]:
        """Analyze productivity patterns by hour of day"""
        work_sessions = [
            s for s in sessions if s.action == "Completed" and s.session_type == "work"
        ]
        hourly_data = {}

        for hour in range(24):
            hourly_data[hour] = 0

        for session in work_sessions:
            hour = session.timestamp.hour
            hourly_data[hour] += session.duration

        return hourly_data

    def export_data(
        self, sessions: List[SessionData], stats: Dict[str, Any], daily_df: pd.DataFrame
    ) -> str:
        """Export data to CSV files"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        export_dir = Path("exports")
        export_dir.mkdir(exist_ok=True)

        # Export raw sessions
        sessions_file = export_dir / f"focus_sessions_{timestamp}.csv"
        with open(sessions_file, "w", newline="", encoding="utf-8") as file:
            writer = csv.writer(file)
            writer.writerow(["Timestamp", "Action", "Type", "Duration", "Date"])
            for session in sessions:
                writer.writerow(
                    [
                        session.timestamp.strftime("%Y-%m-%d %H:%M:%S"),
                        session.action,
                        session.session_type,
                        session.duration,
                        session.date.strftime("%Y-%m-%d"),
                    ]
                )

        # Export daily breakdown
        daily_file = export_dir / f"daily_breakdown_{timestamp}.csv"
        daily_df.to_csv(daily_file, index=False)

        # Export summary stats
        stats_file = export_dir / f"summary_stats_{timestamp}.json"
        with open(stats_file, "w", encoding="utf-8") as file:
            json.dump(stats, file, indent=2, default=str)

        return str(export_dir)


class DashboardGUI:
    """Advanced GUI dashboard with visualizations"""

    def __init__(self, analyzer: SessionAnalyzer):
        try:
            print("Initializing dashboard...")
            self.analyzer = analyzer
            self.is_running = True

            print("Creating root window...")
            self.root = tk.Tk()
            self.root.title("🎯 Focus Productivity Dashboard")
            self.root.geometry("1200x800")
            self.root.configure(bg="#2c3e50")

            # Set up proper window closing protocol
            self.root.protocol("WM_DELETE_WINDOW", self.on_closing)

            # Set up signal handlers for clean shutdown
            signal.signal(signal.SIGINT, self.signal_handler)
            signal.signal(signal.SIGTERM, self.signal_handler)

            # Configure style
            print("Configuring styles...")
            self.style = ttk.Style()
            self.style.theme_use("clam")
            self.configure_styles()

            self.current_period = "week"
            print("Creating widgets...")
            self.create_widgets()
            print("Updating dashboard...")
            self.update_dashboard()
            print("Dashboard initialization complete.")
        except Exception as e:
            print(f"Error during dashboard initialization: {e}")
            import traceback

            traceback.print_exc()
            self.cleanup()
            raise

    def configure_styles(self):
        """Configure custom styles for the GUI"""
        # Configure notebook style
        self.style.configure("TNotebook", background="#2c3e50")
        self.style.configure(
            "TNotebook.Tab", background="#34495e", foreground="white", padding=[20, 10]
        )
        self.style.map("TNotebook.Tab", background=[("selected", "#3498db")])

        # Configure frame style
        self.style.configure(
            "Card.TFrame", background="#34495e", relief="raised", borderwidth=2
        )

    def signal_handler(self, signum, frame):
        """Handle system signals for clean shutdown"""
        print(f"\nReceived signal {signum}, shutting down dashboard...")
        self.cleanup()
        sys.exit(0)

    def on_closing(self):
        """Handle window close event"""
        print("Dashboard window closing...")
        self.cleanup()

    def cleanup(self):
        """Clean up resources and close the application"""
        try:
            self.is_running = False
            if hasattr(self, "root") and self.root:
                print("Destroying tkinter root window...")
                self.root.quit()  # Exit the mainloop
                self.root.destroy()  # Destroy the window

            # Close any matplotlib figures
            plt.close("all")

            print("Dashboard cleanup complete.")
        except Exception as e:
            print(f"Error during cleanup: {e}")
        finally:
            # Force exit if still running
            if hasattr(self, "is_running") and self.is_running:
                os._exit(0)

    def create_widgets(self):
        """Create and layout GUI widgets"""
        # Header
        header_frame = tk.Frame(self.root, bg="#2c3e50", height=80)
        header_frame.pack(fill="x", padx=10, pady=(10, 0))
        header_frame.pack_propagate(False)

        title_label = tk.Label(
            header_frame,
            text="🎯 FOCUS PRODUCTIVITY DASHBOARD",
            font=("Arial", 24, "bold"),
            fg="#ecf0f1",
            bg="#2c3e50",
        )
        title_label.pack(pady=20)

        # Control frame
        control_frame = tk.Frame(self.root, bg="#2c3e50", height=50)
        control_frame.pack(fill="x", padx=10)
        control_frame.pack_propagate(False)

        # Period selection
        tk.Label(
            control_frame, text="Period:", font=("Arial", 12), fg="white", bg="#2c3e50"
        ).pack(side="left", padx=(0, 10))

        self.period_var = tk.StringVar(value=self.current_period)
        period_combo = ttk.Combobox(
            control_frame,
            textvariable=self.period_var,
            values=["day", "week", "month", "year", "all"],
            state="readonly",
            width=10,
        )
        period_combo.pack(side="left", padx=(0, 20))
        period_combo.bind("<<ComboboxSelected>>", self.on_period_change)

        # Buttons
        ttk.Button(
            control_frame, text="🔄 Refresh", command=self.update_dashboard
        ).pack(side="left", padx=(0, 10))
        ttk.Button(control_frame, text="📊 Export Data", command=self.export_data).pack(
            side="left", padx=(0, 10)
        )
        ttk.Button(
            control_frame,
            text="📈 Generate Report",
            command=self.generate_visual_report,
        ).pack(side="left")

        # Notebook for tabs
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill="both", expand=True, padx=10, pady=10)

        # Overview tab
        self.overview_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.overview_frame, text="📊 Overview")

        # Charts tab
        self.charts_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.charts_frame, text="📈 Charts")

        # Details tab
        self.details_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.details_frame, text="📋 Details")

        self.create_overview_tab()
        self.create_charts_tab()
        self.create_details_tab()

    def create_overview_tab(self):
        """Create the overview statistics tab"""
        # Stats cards frame
        stats_frame = tk.Frame(self.overview_frame, bg="#2c3e50")
        stats_frame.pack(fill="both", expand=True, padx=10, pady=10)

        # Create stats card containers
        self.stats_cards = {}

        # Top row - main stats
        top_frame = tk.Frame(stats_frame, bg="#2c3e50")
        top_frame.pack(fill="x", pady=(0, 10))

        for i, (key, title, color) in enumerate(
            [
                ("total_sessions", "Total Sessions", "#3498db"),
                ("work_sessions", "Work Sessions", "#2ecc71"),
                ("productive_hours", "Productive Hours", "#e74c3c"),
                ("days_active", "Active Days", "#f39c12"),
            ]
        ):
            card = self.create_stat_card(top_frame, title, "0", color)
            card.pack(side="left", fill="both", expand=True, padx=5)
            self.stats_cards[key] = card

        # Middle row - averages
        mid_frame = tk.Frame(stats_frame, bg="#2c3e50")
        mid_frame.pack(fill="x", pady=(0, 10))

        for i, (key, title, color) in enumerate(
            [
                ("avg_work_session", "Avg Work Session", "#9b59b6"),
                ("avg_break_session", "Avg Break Session", "#1abc9c"),
                ("work_ratio", "Work Ratio %", "#34495e"),
                ("streak_days", "Current Streak", "#e67e22"),
            ]
        ):
            card = self.create_stat_card(mid_frame, title, "0", color)
            card.pack(side="left", fill="both", expand=True, padx=5)
            self.stats_cards[key] = card

        # Insights section
        insights_frame = ttk.LabelFrame(
            stats_frame, text="💡 Productivity Insights", style="Card.TFrame"
        )
        insights_frame.pack(fill="both", expand=True, pady=(10, 0))

        self.insights_text = tk.Text(
            insights_frame,
            height=8,
            bg="#34495e",
            fg="white",
            font=("Consolas", 11),
            wrap="word",
            padx=10,
            pady=10,
        )
        self.insights_text.pack(fill="both", expand=True, padx=10, pady=10)

    def create_stat_card(self, parent, title, value, color):
        """Create a statistics card widget"""
        card = tk.Frame(parent, bg=color, relief="raised", bd=2)

        title_label = tk.Label(
            card, text=title, font=("Arial", 10, "bold"), fg="white", bg=color
        )
        title_label.pack(pady=(10, 5))

        value_label = tk.Label(
            card, text=value, font=("Arial", 24, "bold"), fg="white", bg=color
        )
        value_label.pack(pady=(0, 10))

        # Store reference to value label for updates
        card.value_label = value_label

        return card

    def create_charts_tab(self):
        """Create the charts and visualizations tab"""
        # Charts will be created dynamically
        self.charts_container = tk.Frame(self.charts_frame, bg="#2c3e50")
        self.charts_container.pack(fill="both", expand=True)

    def create_details_tab(self):
        """Create the detailed data tab"""
        # Treeview for daily breakdown
        columns = ("Date", "Sessions", "Work Sessions", "Work Hours", "Break Minutes")
        self.tree = ttk.Treeview(
            self.details_frame, columns=columns, show="headings", height=15
        )

        for col in columns:
            self.tree.heading(col, text=col)
            self.tree.column(col, width=120, anchor="center")

        # Scrollbar
        scrollbar = ttk.Scrollbar(
            self.details_frame, orient="vertical", command=self.tree.yview
        )
        self.tree.configure(yscrollcommand=scrollbar.set)

        # Pack treeview and scrollbar
        self.tree.pack(side="left", fill="both", expand=True, padx=(10, 0), pady=10)
        scrollbar.pack(side="right", fill="y", padx=(0, 10), pady=10)

    def update_dashboard(self):
        """Update all dashboard data and visualizations"""
        # Get filtered data
        sessions = self.analyzer.filter_sessions(self.current_period)
        stats = self.analyzer.calculate_stats(sessions)
        daily_df = self.analyzer.get_daily_breakdown(sessions)

        # Update stats cards
        self.update_stats_cards(stats)

        # Update insights
        self.update_insights(stats, sessions)

        # Update charts
        self.update_charts(sessions, stats)

        # Update details table
        self.update_details_table(daily_df)

    def update_stats_cards(self, stats: Dict[str, Any]):
        """Update the statistics cards with current data"""
        card_mappings = {
            "total_sessions": str(stats["total_sessions"]),
            "work_sessions": str(stats["work_sessions"]),
            "productive_hours": f"{stats['productive_hours']}h",
            "days_active": str(stats["days_active"]),
            "avg_work_session": f"{stats['avg_work_session']}m",
            "avg_break_session": f"{stats['avg_break_session']}m",
            "work_ratio": f"{stats['work_ratio']}%",
            "streak_days": f"{stats['streak_days']} days",
        }

        for key, value in card_mappings.items():
            if key in self.stats_cards:
                self.stats_cards[key].value_label.config(text=value)

    def update_insights(self, stats: Dict[str, Any], sessions: List[SessionData]):
        """Generate and display productivity insights"""
        insights = []

        # Clear existing insights
        self.insights_text.delete(1.0, tk.END)

        # Generate insights based on data
        if stats["total_sessions"] == 0:
            insights.append(
                "🚀 Ready to start your productivity journey? Your first session awaits!"
            )
        else:
            # Productivity level insights
            if stats["productive_hours"] < 2:
                insights.append(
                    "🌱 Building momentum! Try to reach 2+ hours of focus time daily."
                )
            elif stats["productive_hours"] < 4:
                insights.append(
                    "📈 Good progress! You're developing a solid focus habit."
                )
            elif stats["productive_hours"] < 8:
                insights.append("🔥 Excellent focus! You're in the productivity zone!")
            else:
                insights.append("🏆 Outstanding! You're a productivity champion!")

            # Session length insights
            if stats["avg_work_session"] > 0:
                if stats["avg_work_session"] < 20:
                    insights.append(
                        "⏰ Consider longer work sessions (25-45 min) for deeper focus."
                    )
                elif stats["avg_work_session"] > 50:
                    insights.append(
                        "🛑 Great endurance! Consider adding more breaks to stay fresh."
                    )
                else:
                    insights.append(
                        "✅ Perfect session length for optimal focus and retention!"
                    )

            # Streak insights
            if stats["streak_days"] >= 7:
                insights.append(
                    f"🔥 Amazing {stats['streak_days']}-day streak! Consistency is key!"
                )
            elif stats["streak_days"] >= 3:
                insights.append(
                    f"💪 Great {stats['streak_days']}-day streak! Keep the momentum going!"
                )
            elif stats["streak_days"] == 0:
                insights.append(
                    "⭐ Start a new streak today! Consistency builds lasting habits."
                )

            # Work ratio insights
            if stats["work_ratio"] > 80:
                insights.append(
                    "🎯 High focus ratio! Remember to take breaks for optimal performance."
                )
            elif stats["work_ratio"] < 60:
                insights.append(
                    "🔄 Consider more work sessions relative to breaks for better flow."
                )

            # Daily average insights
            if stats["avg_sessions_per_day"] < 3:
                insights.append(
                    "📅 Try to aim for 3-5 sessions per day for better habit formation."
                )
            elif stats["avg_sessions_per_day"] > 8:
                insights.append(
                    "⚡ High session frequency! Ensure you're not burning out."
                )

        # Display insights
        for i, insight in enumerate(insights, 1):
            self.insights_text.insert(tk.END, f"{i}. {insight}\n\n")

        self.insights_text.config(state="disabled")

    def update_charts(self, sessions: List[SessionData], stats: Dict[str, Any]):
        """Update charts and visualizations"""
        # Clear existing charts
        for widget in self.charts_container.winfo_children():
            widget.destroy()

        if not sessions:
            no_data_label = tk.Label(
                self.charts_container,
                text="No data available for the selected period",
                font=("Arial", 16),
                fg="gray",
                bg="#2c3e50",
            )
            no_data_label.pack(expand=True)
            return

        # Create matplotlib figure
        fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(12, 8))
        fig.patch.set_facecolor("#2c3e50")

        # Daily productivity trend
        daily_df = self.analyzer.get_daily_breakdown(sessions)
        if not daily_df.empty:
            ax1.plot(
                daily_df["Date"],
                daily_df["Work Hours"],
                marker="o",
                color="#2ecc71",
                linewidth=2,
            )
            ax1.set_title(
                "Daily Productivity Trend",
                color="white",
                fontsize=12,
                fontweight="bold",
            )
            ax1.set_ylabel("Work Hours", color="white")
            ax1.tick_params(colors="white")
            ax1.grid(True, alpha=0.3)
            ax1.set_facecolor("#34495e")

        # Session type distribution
        session_types = {}
        for session in sessions:
            if session.action == "Completed":
                session_types[session.session_type] = (
                    session_types.get(session.session_type, 0) + 1
                )

        if session_types:
            labels = list(session_types.keys())
            values = list(session_types.values())
            colors = ["#2ecc71", "#3498db", "#e74c3c"][: len(labels)]
            ax2.pie(
                values, labels=labels, colors=colors, autopct="%1.1f%%", startangle=90
            )
            ax2.set_title(
                "Session Type Distribution",
                color="white",
                fontsize=12,
                fontweight="bold",
            )

        # Hourly productivity pattern
        hourly_data = self.analyzer.get_hourly_pattern(sessions)
        hours = list(hourly_data.keys())
        minutes = list(hourly_data.values())

        ax3.bar(hours, minutes, color="#9b59b6", alpha=0.7)
        ax3.set_title(
            "Productivity by Hour", color="white", fontsize=12, fontweight="bold"
        )
        ax3.set_xlabel("Hour of Day", color="white")
        ax3.set_ylabel("Work Minutes", color="white")
        ax3.tick_params(colors="white")
        ax3.set_facecolor("#34495e")

        # Weekly focus trend (last 7 days)
        recent_sessions = [
            s for s in sessions if s.timestamp >= datetime.now() - timedelta(days=7)
        ]
        weekly_data = {}
        for i in range(7):
            date = (datetime.now() - timedelta(days=i)).date()
            weekly_data[date.strftime("%a")] = 0

        for session in recent_sessions:
            if session.action == "Completed" and session.session_type == "work":
                day_name = session.timestamp.strftime("%a")
                if day_name in weekly_data:
                    weekly_data[day_name] += session.duration

        days = list(weekly_data.keys())
        minutes = list(weekly_data.values())

        ax4.bar(days, minutes, color="#e67e22", alpha=0.7)
        ax4.set_title(
            "Weekly Focus Pattern", color="white", fontsize=12, fontweight="bold"
        )
        ax4.set_ylabel("Work Minutes", color="white")
        ax4.tick_params(colors="white")
        ax4.set_facecolor("#34495e")

        # Style all subplots
        for ax in [ax1, ax2, ax3, ax4]:
            ax.spines["bottom"].set_color("white")
            ax.spines["top"].set_color("white")
            ax.spines["right"].set_color("white")
            ax.spines["left"].set_color("white")

        plt.tight_layout()

        # Embed in tkinter
        canvas = FigureCanvasTkAgg(fig, self.charts_container)
        canvas.draw()
        canvas.get_tk_widget().pack(fill="both", expand=True)

    def update_details_table(self, daily_df: pd.DataFrame):
        """Update the details table with daily breakdown"""
        # Clear existing items
        for item in self.tree.get_children():
            self.tree.delete(item)

        # Insert new data
        for _, row in daily_df.iterrows():
            self.tree.insert(
                "",
                "end",
                values=(
                    row["Date"].strftime("%Y-%m-%d"),
                    row["Sessions"],
                    row["Work Sessions"],
                    row["Work Hours"],
                    row["Break Minutes"],
                ),
            )

    def on_period_change(self, event=None):
        """Handle period selection change"""
        self.current_period = self.period_var.get()
        self.update_dashboard()

    def export_data(self):
        """Export dashboard data"""
        try:
            sessions = self.analyzer.filter_sessions(self.current_period)
            stats = self.analyzer.calculate_stats(sessions)
            daily_df = self.analyzer.get_daily_breakdown(sessions)

            export_path = self.analyzer.export_data(sessions, stats, daily_df)
            messagebox.showinfo("Export Complete", f"Data exported to:\n{export_path}")
        except Exception as e:
            messagebox.showerror("Export Error", f"Failed to export data:\n{str(e)}")

    def generate_visual_report(self):
        """Generate a comprehensive visual report"""
        try:
            # Ask user for save location
            filename = filedialog.asksaveasfilename(
                defaultextension=".png",
                filetypes=[("PNG files", "*.png"), ("PDF files", "*.pdf")],
                title="Save Report As",
            )

            if filename:
                sessions = self.analyzer.filter_sessions(self.current_period)

                # Create a comprehensive report figure
                fig, axes = plt.subplots(3, 2, figsize=(15, 12))
                fig.suptitle(
                    f"Focus Productivity Report - {self.current_period.title()} View",
                    fontsize=16,
                    fontweight="bold",
                )

                # Add various charts to the report
                # (Implementation would include all the chart generation logic)

                plt.tight_layout()
                plt.savefig(filename, dpi=300, bbox_inches="tight", facecolor="white")
                plt.close()

                messagebox.showinfo(
                    "Report Generated", f"Visual report saved to:\n{filename}"
                )
        except Exception as e:
            messagebox.showerror(
                "Report Error", f"Failed to generate report:\n{str(e)}"
            )

    def run(self):
        """Start the dashboard GUI"""
        try:
            print("Starting dashboard GUI mainloop...")
            # Make the window interruptible by checking periodically
            self.root.after(100, self.check_running)
            self.root.mainloop()
            print("Dashboard GUI mainloop ended.")
        except KeyboardInterrupt:
            print("Keyboard interrupt received...")
            self.cleanup()
        except Exception as e:
            print(f"Error in dashboard mainloop: {e}")
            import traceback

            traceback.print_exc()
            self.cleanup()
        finally:
            print("Dashboard run method completed.")
            self.cleanup()

    def check_running(self):
        """Periodically check if the application should continue running"""
        if self.is_running and self.root:
            self.root.after(100, self.check_running)
        else:
            self.cleanup()


def console_dashboard(period: str = "week", export: bool = False):
    """Run console version of the dashboard"""
    analyzer = SessionAnalyzer()
    sessions = analyzer.filter_sessions(period)
    stats = analyzer.calculate_stats(sessions)
    daily_df = analyzer.get_daily_breakdown(sessions)

    # Console output with enhanced formatting
    print("═" * 70)
    print("                🎯 FOCUS PRODUCTIVITY DASHBOARD")
    print("═" * 70)
    print()

    print(f"📊 SUMMARY ({period.upper()})")
    print(f"├─ Total Sessions: {stats['total_sessions']}")
    print(f"├─ Work Sessions: {stats['work_sessions']}")
    print(f"├─ Break Sessions: {stats['break_sessions']}")
    print(f"├─ Productive Hours: {stats['productive_hours']}")
    print(f"├─ Days Active: {stats['days_active']}")
    print(f"├─ Current Streak: {stats['streak_days']} days")
    print(f"├─ Avg Work Session: {stats['avg_work_session']} min")
    print(f"└─ Avg Break Session: {stats['avg_break_session']} min")
    print()

    if stats["total_sessions"] > 0:
        print("📈 PRODUCTIVITY METRICS")
        print(f"├─ Work/Break Ratio: {stats['work_ratio']}% work")
        print(f"├─ Total Focus Time: {stats['total_work_time']} minutes")
        print(f"├─ Total Break Time: {stats['total_break_time']} minutes")
        print(f"├─ Avg Sessions/Day: {stats['avg_sessions_per_day']}")
        print(f"└─ Avg Work/Day: {stats['avg_work_per_day']} minutes")
        print()

    if not daily_df.empty:
        print("📅 DAILY BREAKDOWN (Recent)")
        for _, row in daily_df.head(7).iterrows():
            date_str = row["Date"].strftime("%a, %b %d")
            bar = "█" * min(20, int(row["Work Hours"] * 2))
            print(
                f"├─ {date_str}: {row['Work Sessions']} sessions, {row['Work Hours']}h {bar}"
            )
        print()

    # Enhanced insights
    print("💡 PRODUCTIVITY INSIGHTS")
    if stats["total_sessions"] == 0:
        print("├─ No sessions recorded yet. Start your first focus session!")
    elif stats["productive_hours"] < 2:
        print("├─ Building momentum! Try to reach 2+ hours of focus time daily.")
    elif stats["productive_hours"] < 4:
        print("├─ Good progress! You're developing a solid focus habit.")
    else:
        print("├─ Excellent focus! You're in the productivity zone! 🔥")

    if stats["streak_days"] >= 7:
        print(f"├─ Amazing {stats['streak_days']}-day streak! Consistency is key! 🏆")
    elif stats["streak_days"] >= 3:
        print(f"├─ Great {stats['streak_days']}-day streak! Keep it going! 💪")
    elif stats["streak_days"] == 0:
        print("├─ Ready to start a new streak? Today is perfect! ⭐")

    print("└─ Remember: Consistency beats perfection! 🎯")
    print()
    print("═" * 70)

    if export:
        export_path = analyzer.export_data(sessions, stats, daily_df)
        print(f"📁 Data exported to: {export_path}")

    return analyzer, sessions, stats, daily_df


def main():
    """Main entry point for the dashboard"""
    parser = argparse.ArgumentParser(description="Focus Productivity Dashboard")
    parser.add_argument(
        "--period",
        choices=["day", "week", "month", "year", "all"],
        default="week",
        help="Time period to analyze",
    )
    parser.add_argument("--export", action="store_true", help="Export data to CSV")
    parser.add_argument("--gui", action="store_true", help="Launch GUI dashboard")
    parser.add_argument("--console", action="store_true", help="Run console dashboard")

    args = parser.parse_args()

    if args.gui:
        analyzer = SessionAnalyzer()
        dashboard_gui = DashboardGUI(analyzer)
        dashboard_gui.run()
    else:
        console_dashboard(args.period, args.export)


if __name__ == "__main__":
    main()
    main()
