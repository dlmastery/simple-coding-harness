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
 * so run() returns a promise: it resolves on the close event, and the
 * timeout is a timer that kills the process tree.
 */

import { spawn } from "node:child_process";
import { existsSync, writeFileSync } from "node:fs";
import { tmpdir } from "node:os";
import { delimiter, join, resolve } from "node:path";

export const PROJECT = resolve(process.cwd());

export const PROFILE = `(version 1)
(deny default)
(allow process-exec process-fork signal)
(allow file-read*)
(allow sysctl-read)
(deny network*)
(allow file-write* (subpath "${PROJECT}") (literal "/dev/null"))
(deny file-write* (subpath "${PROJECT}/.git"))
`;

export type Output = { stdout: string; stderr: string };

/** The error run() rejects with when the timer fires first. */
export class TimedOut extends Error {
  timeout: number;

  constructor(timeout: number) {
    super(`Timed out after ${timeout}s`);
    this.timeout = timeout;
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
    const profile = join(tmpdir(), "simple-harness.sb");
    writeFileSync(profile, PROFILE);
    return ["sandbox-exec", "-f", profile, "/bin/sh", "-c", command];
  }

  if (process.platform === "linux" && which("bwrap")) {
    return [
      "bwrap",
      "--ro-bind", "/", "/",
      "--bind", PROJECT, PROJECT,
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

/** End the process and everything it started. */
export function kill(pid: number | undefined, child: { kill(signal?: NodeJS.Signals): boolean }): void {
  if (process.platform === "win32" && pid !== undefined) {
    spawn("taskkill", ["/T", "/F", "/PID", String(pid)], { stdio: "ignore" });
  } else {
    child.kill("SIGKILL");
  }
}

/** Run a command, sandboxed when the OS lets us. Resolves with its output. */
export function run(command: string, timeout = 60): Promise<Output> {
  const sandboxed = wrap(command);
  const child = sandboxed
    ? spawn(sandboxed[0], sandboxed.slice(1), { stdio: ["ignore", "pipe", "pipe"] })
    : spawn(command, { shell: true, stdio: ["ignore", "pipe", "pipe"] });

  return new Promise((done, fail) => {
    let stdout = "";
    let stderr = "";
    let expired = false;
    child.stdout.setEncoding("utf-8");
    child.stderr.setEncoding("utf-8");
    child.stdout.on("data", (chunk: string) => (stdout += chunk));
    child.stderr.on("data", (chunk: string) => (stderr += chunk));
    const timer = setTimeout(() => {
      expired = true;
      kill(child.pid, child);
    }, timeout * 1000);
    child.on("error", (failure) => {
      clearTimeout(timer);
      fail(failure);
    });
    child.on("close", () => {
      clearTimeout(timer);
      if (expired) fail(new TimedOut(timeout));
      else done({ stdout, stderr });
    });
  });
}
