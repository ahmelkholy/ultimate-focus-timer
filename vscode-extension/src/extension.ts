import axios from "axios";
import * as vscode from "vscode";

// Daemon connection settings
const DAEMON_HOST = "http://127.0.0.1:8765";

// Status bar item
let statusBarItem: vscode.StatusBarItem;

// Current session state
interface SessionStatus {
  phase: string;
  started_at: string | null;
  phase_started_at: string | null;
  phase_duration_minutes: number;
  remaining_seconds: number;
  distraction_blocking_active: boolean;
  audio_active: boolean;
}

let currentStatus: SessionStatus | null = null;

/**
 * Activate the extension
 */
export function activate(context: vscode.ExtensionContext) {
  console.log("Ultimate Focus Timer extension activated");

  // Create status bar item
  statusBarItem = vscode.window.createStatusBarItem(
    vscode.StatusBarAlignment.Right,
    100,
  );
  statusBarItem.command = "ultimateFocusTimer.startSession";
  statusBarItem.text = "$(target) Focus";
  statusBarItem.tooltip = "Start Ultradian Focus Session (90 min cycle)";
  statusBarItem.show();

  context.subscriptions.push(statusBarItem);

  // Register commands
  context.subscriptions.push(
    vscode.commands.registerCommand(
      "ultimateFocusTimer.startSession",
      async () => {
        await startFocusSession();
      },
    ),
  );

  context.subscriptions.push(
    vscode.commands.registerCommand(
      "ultimateFocusTimer.stopSession",
      async () => {
        await stopFocusSession();
      },
    ),
  );

  context.subscriptions.push(
    vscode.commands.registerCommand(
      "ultimateFocusTimer.showStatus",
      async () => {
        await showSessionStatus();
      },
    ),
  );

  // Start status polling
  startStatusPolling(context);
}

/**
 * Start a new focus session
 */
async function startFocusSession() {
  try {
    const response = await axios.post(`${DAEMON_HOST}/start`, {
      enable_audio: true,
      enable_blocking: true,
    });

    currentStatus = response.data;
    updateStatusBar();

    vscode.window.showInformationMessage(
      "🎯 Ultradian Focus Session Started! (90 min cycle: 5m ramp → 85m deep work → 20m rest)",
    );
  } catch (error) {
    handleDaemonError(error);
  }
}

/**
 * Stop the current session
 */
async function stopFocusSession() {
  try {
    const response = await axios.post(`${DAEMON_HOST}/stop`);
    currentStatus = response.data;
    updateStatusBar();

    vscode.window.showInformationMessage("🛑 Focus Session Stopped");
  } catch (error) {
    handleDaemonError(error);
  }
}

/**
 * Show current session status
 */
async function showSessionStatus() {
  try {
    const response = await axios.get(`${DAEMON_HOST}/status`);
    const s = response.data as SessionStatus;
    currentStatus = s;

    if (s.phase === "idle") {
      vscode.window.showInformationMessage(
        "💤 No active session. Click the Focus button to start!",
      );
    } else {
      const minutes = Math.floor(s.remaining_seconds / 60);
      const seconds = s.remaining_seconds % 60;
      const timeStr = `${minutes}:${seconds.toString().padStart(2, "0")}`;

      const phaseEmoji: Record<string, string> = {
        ramp_up: "🔥",
        deep_work: "🎯",
        neural_rest: "🧘",
      };

      vscode.window.showInformationMessage(
        `${phaseEmoji[s.phase] ?? "⏱️"} ${s.phase.toUpperCase()} - ${timeStr} remaining`,
      );
    }
  } catch (error) {
    handleDaemonError(error);
  }
}

/**
 * Start polling daemon for status updates
 */
function startStatusPolling(context: vscode.ExtensionContext) {
  const interval = setInterval(async () => {
    try {
      const response = await axios.get(`${DAEMON_HOST}/status`);
      currentStatus = response.data;
      updateStatusBar();
    } catch (error) {
      // Daemon not running - show idle state
      currentStatus = null;
      updateStatusBar();
    }
  }, 2000); // Poll every 2 seconds

  context.subscriptions.push({
    dispose: () => clearInterval(interval),
  });
}

/**
 * Update the status bar display
 */
function updateStatusBar() {
  if (!currentStatus || currentStatus.phase === "idle") {
    statusBarItem.text = "$(target) Focus";
    statusBarItem.tooltip = "Start Ultradian Focus Session (90 min cycle)";
    statusBarItem.command = "ultimateFocusTimer.startSession";
    statusBarItem.backgroundColor = undefined;
  } else {
    const minutes = Math.floor(currentStatus.remaining_seconds / 60);
    const seconds = currentStatus.remaining_seconds % 60;
    const timeStr = `${minutes}:${seconds.toString().padStart(2, "0")}`;

    const phaseConfig: Record<
      string,
      { emoji: string; color: vscode.ThemeColor | undefined }
    > = {
      ramp_up: {
        emoji: "🔥",
        color: new vscode.ThemeColor("statusBarItem.warningBackground"),
      },
      deep_work: {
        emoji: "🎯",
        color: new vscode.ThemeColor("statusBarItem.errorBackground"),
      },
      neural_rest: {
        emoji: "🧘",
        color: new vscode.ThemeColor("statusBarItem.prominentBackground"),
      },
    };

    const config = phaseConfig[currentStatus.phase] || {
      emoji: "⏱️",
      color: undefined,
    };

    statusBarItem.text = `${config.emoji} ${timeStr}`;
    statusBarItem.tooltip = `${currentStatus.phase.toUpperCase()} - ${timeStr} remaining\nClick to stop`;
    statusBarItem.command = "ultimateFocusTimer.stopSession";
    statusBarItem.backgroundColor = config.color;
  }
}

/**
 * Handle daemon connection errors
 */
function handleDaemonError(error: any) {
  if (error.code === "ECONNREFUSED" || error.code === "ENOTFOUND") {
    vscode.window.showErrorMessage(
      "❌ Focus Timer Daemon not running. Start it with: python -m src.daemon",
    );
  } else {
    vscode.window.showErrorMessage(`❌ Focus Timer Error: ${error.message}`);
  }
}

/**
 * Deactivate the extension
 */
export function deactivate() {
  console.log("Ultimate Focus Timer extension deactivated");
}
