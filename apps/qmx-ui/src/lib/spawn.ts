/**
 * v1 bootstrap: the browser is a client of an already-running daemon.
 * Start local is setup copy until host verbs exist. Never spawn Python,
 * never import QMB/QML/QMN, never start qma-daemon (DEC-0485).
 */
export const START_LOCAL_MODE = "setup-copy" as const;

export function startLocalAction(): typeof START_LOCAL_MODE {
  return START_LOCAL_MODE;
}

export const SETUP_COPY =
  "Start the daemon, configure pairing TTL, then pair. The browser does not spawn Python. Until host verbs exist, Start local is setup copy, not a spawn. A provider cred:// is not operator login.";
