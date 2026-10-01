/**
 * One producer_id per chrome tab (DEC-0490). Sharing a live producer_id
 * across tabs is forbidden. Same-tab reload may reuse the session value.
 */

export const PRODUCER_SESSION_KEY = "qmx.producer_id";

export type ProducerSource = "fresh" | "same-tab-reload" | "cloned-replaced";

export type ProducerClaim = {
  producer_id: string;
  source: ProducerSource;
  sharedLiveForbidden: true;
};

export type ProducerKv = {
  getItem(key: string): string | null;
  setItem(key: string, value: string): void;
};

/** Cross-tab lock table: producer_id → tab token. */
export type ProducerLocks = {
  held: Map<string, string>;
};

export function memoryKv(init: Record<string, string> = {}): ProducerKv {
  const map = new Map(Object.entries(init));
  return {
    getItem: (key) => map.get(key) ?? null,
    setItem: (key, value) => {
      map.set(key, value);
    },
  };
}

export function memoryLocks(): ProducerLocks {
  return { held: new Map() };
}

export function mintProducerId(): string {
  return `producer:${crypto.randomUUID()}`;
}

export function mintTabToken(): string {
  return `tab:${crypto.randomUUID()}`;
}

export function claimProducer(ports: {
  session: ProducerKv;
  locks: ProducerLocks;
  tabToken: string;
  mint?: () => string;
}): ProducerClaim {
  const mint = ports.mint ?? mintProducerId;
  const existing = ports.session.getItem(PRODUCER_SESSION_KEY);
  if (existing) {
    const holder = ports.locks.held.get(existing);
    if (holder && holder !== ports.tabToken) {
      const next = mint();
      ports.session.setItem(PRODUCER_SESSION_KEY, next);
      ports.locks.held.set(next, ports.tabToken);
      return {
        producer_id: next,
        source: "cloned-replaced",
        sharedLiveForbidden: true,
      };
    }
    ports.locks.held.set(existing, ports.tabToken);
    return {
      producer_id: existing,
      source: "same-tab-reload",
      sharedLiveForbidden: true,
    };
  }
  const next = mint();
  ports.session.setItem(PRODUCER_SESSION_KEY, next);
  ports.locks.held.set(next, ports.tabToken);
  return {
    producer_id: next,
    source: "fresh",
    sharedLiveForbidden: true,
  };
}

/** Product-session command_id is unique per psess: across tabs (DEC-0490). */
export function mintCommandId(
  productSessionRef: string,
  producerId: string,
  seq: number,
): string {
  return `${productSessionRef}:${producerId}:cmd:${seq}`;
}

/** Invocation idempotency_key applies only to dispatchInvoke. */
export function mintIdempotencyKey(
  producerId: string,
  logicalInvocationId: string,
): string {
  return `idem:${producerId}:${logicalInvocationId}`;
}

export function mintWireId(producerId: string): string {
  return `${producerId}:wire:${crypto.randomUUID()}`;
}

export function mintLogicalInvocationId(producerId: string): string {
  return `inv:${producerId}:${crypto.randomUUID()}`;
}

const commandSeqByPsess = new Map<string, number>();

export function nextCommandSeq(productSessionRef: string): number {
  const next = (commandSeqByPsess.get(productSessionRef) ?? 0) + 1;
  commandSeqByPsess.set(productSessionRef, next);
  return next;
}

export function resetCommandSeqForTests(): void {
  commandSeqByPsess.clear();
}

const LOCK_NAME_PREFIX = "qmx.producer.";

function holdWebLock(producerId: string): Promise<boolean> {
  const locks = globalThis.navigator?.locks;
  if (!locks?.request) return Promise.resolve(true);
  return new Promise((resolve) => {
    void locks.request(
      `${LOCK_NAME_PREFIX}${producerId}`,
      { ifAvailable: true, mode: "exclusive" },
      (lock) => {
        if (!lock) {
          resolve(false);
          return;
        }
        resolve(true);
        return new Promise<void>(() => {
          /* held until this tab's context is destroyed */
        });
      },
    );
  });
}

/** Browser claim: sessionStorage for reload; Web Locks so clones cannot share live ids. */
export async function claimBrowserProducer(
  session: ProducerKv = globalThis.sessionStorage,
): Promise<ProducerClaim> {
  const existing = session.getItem(PRODUCER_SESSION_KEY);
  if (existing) {
    const held = await holdWebLock(existing);
    if (!held) {
      const next = mintProducerId();
      session.setItem(PRODUCER_SESSION_KEY, next);
      await holdWebLock(next);
      return {
        producer_id: next,
        source: "cloned-replaced",
        sharedLiveForbidden: true,
      };
    }
    return {
      producer_id: existing,
      source: "same-tab-reload",
      sharedLiveForbidden: true,
    };
  }
  const next = mintProducerId();
  session.setItem(PRODUCER_SESSION_KEY, next);
  await holdWebLock(next);
  return {
    producer_id: next,
    source: "fresh",
    sharedLiveForbidden: true,
  };
}
