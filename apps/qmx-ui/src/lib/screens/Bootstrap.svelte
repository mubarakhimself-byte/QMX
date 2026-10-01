<script lang="ts">
  import { onMount } from "svelte";
  import { Badge } from "$lib/components/ui/badge";
  import { Button } from "$lib/components/ui/button";
  import { Skeleton } from "$lib/components/ui/skeleton";
  import {
    CHROME_STATES,
    FACTORY_TEST_LABEL,
    FACTORY_TEST_PAIRING,
    parseFixtureState,
    stateCopy,
    type ChromeState,
  } from "$lib/bootstrap";
  import {
    FIRST_PARTY_SVELTE_HOST_AT_INSPECT,
    INSPECT_SHA,
  } from "$lib/inspect";
  import { SAMPLE_ORIGIN, assertSpaOrigin, isDaemonOrigin } from "$lib/origin";
  import { SETUP_COPY, startLocalAction } from "$lib/spawn";

  let origin = $state(SAMPLE_ORIGIN);
  let chromeState = $state<ChromeState>("empty");
  let startLocalResult = $state("");
  let reportRuntimeState: ((state: ChromeState) => void) | undefined;

  onMount(() => {
    origin = assertSpaOrigin(window.location.origin);
    const params = new URLSearchParams(window.location.search);
    chromeState = parseFixtureState(params.get("fixture"));
    if (import.meta.env.DEV) {
      void import("../../reticle-dev").then(({ setBootstrapState }) => {
        reportRuntimeState = setBootstrapState;
        reportRuntimeState(chromeState);
      });
    }
  });

  function onStartLocal() {
    startLocalResult =
      startLocalAction() === "setup-copy" ? SETUP_COPY : "illegal-spawn";
  }

  function setChromeState(next: ChromeState) {
    chromeState = next;
    if (import.meta.env.DEV) reportRuntimeState?.(next);
  }
</script>

<main
  class="mx-auto flex max-w-3xl flex-col gap-4 p-6"
  data-testid="bootstrap-shell"
>
  <header class="flex flex-col gap-2">
    <p class="text-muted-foreground text-xs tracking-wide uppercase">
      QMX host
    </p>
    <h1 class="text-xl font-medium">Pair a browser to a running daemon</h1>
    <p data-testid="spa-origin">Origin {origin}</p>
    <p data-testid="sample-origin">Sample Origin {SAMPLE_ORIGIN}</p>
    <p data-testid="daemon-port-forbidden">
      Daemon port 8765 is not this origin
    </p>
    <p data-testid="inspect-honesty">
      Inspect {INSPECT_SHA}: first-party Svelte host was
      {FIRST_PARTY_SVELTE_HOST_AT_INSPECT ? "present" : "absent"}.
      qma-ui-contract stays stub.
    </p>
  </header>

  <section
    class="bg-surface border-border flex flex-col gap-3 rounded-lg border p-4"
    data-testid="bootstrap-state"
    data-state={chromeState}
  >
    {#if chromeState === "loading"}
      <Skeleton class="h-4 w-2/3" data-testid="bootstrap-skeleton" />
      <Skeleton class="h-4 w-1/2" />
    {/if}

    {#if chromeState === "stale"}
      <Badge variant="outline" data-testid="stale-badge">stale</Badge>
    {/if}

    {#if chromeState === "reconnecting"}
      <Badge variant="secondary" data-testid="reconnecting-badge"
        >reconnecting</Badge
      >
    {/if}

    {#if chromeState === "denied"}
      <Badge variant="destructive" data-testid="denied-badge">denied</Badge>
    {/if}

    <p data-testid="bootstrap-copy">{stateCopy(chromeState)}</p>
    <p data-testid="pairing-record">
      pairing_record_id is journal identity ({FACTORY_TEST_PAIRING.pairing_record_id}),
      never Authorization.
    </p>
    <p data-testid="client-of-wire">
      This SPA is a client of qma-wire. Chrome is not a COMP, scheduler, or
      grant store.
    </p>
  </section>

  <div class="flex flex-wrap gap-2">
    <Button data-testid="start-local" onclick={onStartLocal}>Start local</Button
    >
  </div>
  {#if startLocalResult}
    <p data-testid="start-local-result">{startLocalResult}</p>
  {/if}

  <aside
    class="border-border text-muted-foreground rounded-md border border-dashed p-3 text-sm"
    data-testid="factory-test-fixtures"
  >
    <p class="text-foreground font-medium">
      {FACTORY_TEST_LABEL} state fixtures
    </p>
    <p>Local fixtures only. Not product pairing. Not a live daemon.</p>
    <div class="mt-2 flex flex-wrap gap-2">
      {#each CHROME_STATES as item (item)}
        <Button
          variant={chromeState === item ? "default" : "outline"}
          size="sm"
          data-testid={`fixture-${item}`}
          onclick={() => setChromeState(item)}
        >
          {item}
        </Button>
      {/each}
    </div>
    {#if isDaemonOrigin(origin)}
      <p data-testid="origin-violation" class="text-destructive">
        Origin is daemon 8765 — illegal
      </p>
    {/if}
  </aside>
</main>
