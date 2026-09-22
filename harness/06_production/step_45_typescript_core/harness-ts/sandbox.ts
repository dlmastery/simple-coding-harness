/** Step 45 - an OS sandbox for bash.
 *
 * Permissions are not real security. A file can still be removed from a
 * one-liner, because the rules only see the command text. A sandbox asks a
 * different question: is this specific operation allowed at all? The kernel
 * answers it.
 *
 * One policy - read anything, write only inside the project, no network - and
 * one mechanism per OS: seatbelt on macOS, bubblewrap on Linux. Windows has
 * no equivalent here and the banner says so.
 *
 * Python's subprocess.run blocks the thread until the command exits. Node
 * has no blocking wait for a spawned process that also captures its output,
 * so run() returns a promise: it settles when the process exits, and the
 * timeout is a timer that kills the process tree. The command gets a
 * process group of its own (detached on POSIX), so the kill reaches what
 * it started too - the same start_new_session + killpg the Python
 * harness uses - and a grandchild that kept the output pipe open cannot
 * hold the turn: the promise settles a moment after the exit whether the
 * pipe closed or not.
 */

import { spawn } from "node:child_process";
import { existsSync, mkdtempSync, realpathSync, writeFileSync } from "node:fs";
import { tmpdir } from "node:os";
import { delimiter, join, resolve } from "node:path";

export const PROJECT = resolve(process.cwd());

export const DRAIN_MS = 200; // after the exit, how long the output pipes get to close on their own

/** The real path of the temp directory; on macOS /var/folders is a link into /private. */
export function tempDir(): string {
  return realpathSync(tmpdir());
}

/** The seatbelt profile, the same one as harness/sandbox.py: the project and the temp directory are writable. */
export const PROFILE = `(version 1)
(deny default)
(allow process-exec process-fork signal)
(allow file-read*)
(allow sysctl-read)
(deny network*)
(allow file-write* (subpath "${PROJECT}") (subpath "${tempDir()}") (literal "/dev/null"))
(deny file-write* (subpath "${PROJECT}/.git"))
`;

export type Output = { stdout: string; stderr: string };

/** The error run() rejects with when the timer fires first. `output` is what the command printed before the kill. */
export class TimedOut extends Error {
  timeout: number;
  output: string;

  constructor(timeout: number, output = "") {
    super(`Timed out after ${timeout}s`);
    this.name = "TimedOut";
    this.timeout = timeout;
    this.output = output;
  }
}

function which(name: string): string | null {
  for (const dir of (process.env.PATH ?? "").split(delimiter)) {
    if (dir && existsSync(join(dir, name))) return join(dir, name);
  }
  return null;
}

/** Wrap a shell command in an OS sandbox. null means we have no sandbox. */
export function wrap(command: string): string[] | null {
  if (process.platform === "darwin") {
    // one profile file per command: parallel callers must not write the same file at the same time
    const profile = join(mkdtempSync(join(tmpdir(), "simple-harness-")), "profile.sb");
    writeFileSync(profile, PROFILE);
    return ["sandbox-exec", "-f", profile, "/bin/sh", "-c", command];
  }

  if (process.platform === "linux" && which("bwrap")) {
    return [
      "bwrap",
      "--ro-bind", "/", "/",
      "--bind", PROJECT, PROJECT,
      "--bind", tempDir(), tempDir(),
      "--dev", "/dev", "--proc", "/proc",
      "--unshare-net", "--die-with-parent",
      "/bin/sh", "-c", command,
    ];
  }

  return null; // Windows, or Linux without bubblewrap
}

export function name(): string {
  if (process.platform === "darwin") return "seatbelt";
  if (process.platform === "linux" && which("bwrap")) return "bubblewrap";
  return "none";
}

/** End the process and everything it started: the whole tree on Windows, the whole process group elsewhere. */
export function kill(pid: number | undefined, child: { kill(signal?: NodeJS.Signals): boolean }): void {
  if (pid === undefined) return;
  if (process.platform === "win32") {
    spawn("taskkill", ["/T", "/F", "/PID", String(pid)], { stdio: "ignore" });
    return;
  }
  try {
    process.kill(-pid, "SIGKILL"); // the group: a negative pid is every process the command started
  } catch {
    child.kill("SIGKILL"); // the group is gone already, or was never made; the shell itself at least
  }
}

// no pagers and no credential prompts: the command has no terminal to answer on
export const ENV = { PAGER: "cat", GIT_PAGER: "cat", GIT_TERMINAL_PROMPT: "0", PYTHONIOENCODING: "utf-8" };

/** Run a command, sandboxed when the OS lets us. Resolves with its output. */
export function run(command: string, timeout = 60): Promise<Output> {
  const sandboxed = wrap(command);
  const options = {
    stdio: ["ignore", "pipe", "pipe"] as ["ignore", "pipe", "pipe"],
    env: { ...process.env, ...ENV },
    detached: process.platform !== "win32", // its own process group, so kill() can reach its children
  };
  const child = sandboxed ? spawn(sandboxed[0], sandboxed.slice(1), options) : spawn(command, { ...options, shell: true });

  return new Promise((done, fail) => {
    let stdout = "";
    let stderr = "";
    let expired = false;
    let settled = false;
    child.stdout.setEncoding("utf-8");
    child.stderr.setEncoding("utf-8");
    child.stdout.on("data", (chunk: string) => (stdout += chunk));
    child.stderr.on("data", (chunk: string) => (stderr += chunk));
    const timer = setTimeout(() => {
      expired = true;
      kill(child.pid, child);
    }, timeout * 1000);
    const settle = () => {
      if (settled) return;
      settled = true;
      clearTimeout(timer);
      if (expired) fail(new TimedOut(timeout, stdout + stderr));
      else done({ stdout, stderr });
    };
    child.on("error", (failure) => {
      clearTimeout(timer);
      settled = true;
      fail(failure);
    });
    child.on("close", settle); // the pipes closed: the output is complete
    child.on("exit", () => setTimeout(settle, DRAIN_MS)); // or the process is gone and a child still holds the pipe: settle anyway
  });
}
