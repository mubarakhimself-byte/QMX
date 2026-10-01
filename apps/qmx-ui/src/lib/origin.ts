/** Daemon HTTP bind (CT-40). The SPA origin must never be this port. */
export const DAEMON_PORT = 8765;

/** Sample bootstrap Origin from the UI lens (DEC-0469). */
export const SPA_DEV_PORT = 5173;
export const SPA_PREVIEW_PORT = 4173;
export const SAMPLE_ORIGIN = "http://127.0.0.1:5173";

export function portOfOrigin(origin: string): string {
  try {
    return new URL(origin).port;
  } catch {
    return "";
  }
}

export function isDaemonOrigin(origin: string): boolean {
  return portOfOrigin(origin) === String(DAEMON_PORT);
}

export function assertSpaOrigin(origin: string): string {
  if (isDaemonOrigin(origin)) {
    throw new Error(`SPA origin must not be daemon port ${DAEMON_PORT}`);
  }
  return origin;
}
