<script lang="ts">
  import { onMount } from "svelte";
  import { Badge } from "$lib/components/ui/badge";
  import { Button } from "$lib/components/ui/button";
  import { FACTORY_TEST_LABEL } from "$lib/bootstrap";
  import { HOME_CHROME_AT_INSPECT, INSPECT_SHA } from "$lib/inspect";
  import AttentionList from "$lib/shell/AttentionList.svelte";
  import {
    HOME_CHROME_STATES,
    HOME_PRODUCT_SESSION_REF,
    HOME_SESSION,
    applyHomeFixture,
    cancelHomeJob,
    homeState,
    homeStateCopy,
    reconnectHome,
    resumeHome,
    sendHomeChat,
    setHomeChromeState,
    submitHomeInvoke,
  } from "./homeState";

  const snapshot = $derived($homeState);
  let chatDraft = $state(`${FACTORY_TEST_LABEL} home chat without instance`);

  onMount(() => {
    applyHomeFixture(
      new URLSearchParams(window.location.search).get("fixture"),
    );
  });
</script>

<svelte:head>
  <title>Home</title>
</svelte:head>

<main
  class="flex flex-col gap-4 p-6"
  data-testid="destination-home"
  data-profile={HOME_SESSION.profile}
  data-is-copilot="false"
  data-observation-product="false"
>
  <p class="text-muted-foreground text-xs tracking-wide uppercase">Home</p>
  <h1 class="text-xl font-medium">Work / attention / resume</h1>
  <p data-testid="home-purpose">
    Independent of Copilot. Profile authoring. No third ProductSessionProfile.
    Observation is not a fourth product.
  </p>
  <p data-testid="home-inspect-honesty">
    Inspect {INSPECT_SHA}: first-party Svelte host was absent. Home chrome was
    {HOME_CHROME_AT_INSPECT ? "present" : "absent"}.
  </p>
  <p
    class="text-muted-foreground text-sm"
    data-testid="disconnected-vs-attention"
  >
    Disconnected vs attention stay distinct. A reconnecting badge is not failed
    attention. unknown is not painted as failed.
  </p>

  <AttentionList
    chromeState={snapshot.chromeState}
    rows={snapshot.rows}
    copy={homeStateCopy(snapshot.chromeState)}
    onResume={resumeHome}
    onCancel={cancelHomeJob}
  />

  {#if snapshot.chromeState === "reconnecting"}
    <div class="flex flex-wrap gap-2">
      <Button
        variant="outline"
        data-testid="home-run-reconnect"
        onclick={() => reconnectHome()}
      >
        Run reconnect query
      </Button>
    </div>
  {/if}

  <section
    class="bg-surface border-border flex flex-col gap-3 rounded-lg border p-4"
    data-testid="home-chat"
    data-product-session-ref={HOME_PRODUCT_SESSION_REF}
    data-app-instance-id=""
    data-mints-instance="false"
    data-independent-of-copilot="true"
    data-emits="submit_chat"
  >
    <p class="text-sm font-medium">Optional Home chat</p>
    <p class="text-muted-foreground text-sm">
      send_message via dispatchChat. app_instance_id absent. Does not mint a
      synthetic instance. Not Copilot.
    </p>
    <label class="flex flex-col gap-1 text-sm">
      <span class="text-muted-foreground">Message</span>
      <input
        class="border-input bg-background h-8 rounded-md border px-2 text-sm"
        data-testid="home-chat-input"
        bind:value={chatDraft}
      />
    </label>
    <Button
      data-testid="home-submit-chat"
      data-emits="submit_chat"
      onclick={() => sendHomeChat(chatDraft)}
    >
      Send Home chat
    </Button>
    {#if snapshot.chatProceeded}
      <p data-testid="home-chat-no-instance">
        send_message with no instance. Did not mint a synthetic instance.
      </p>
    {/if}
  </section>

  <section
    class="bg-surface border-border flex flex-col gap-3 rounded-lg border p-4"
    data-testid="home-invoke"
    data-emits="submit_invoke"
  >
    <p class="text-sm font-medium">Invoke</p>
    <p class="text-muted-foreground text-sm">
      Needs exactly one selected_refs kind instance_id. Envelope instance_id
      remains required. Zero or many is INVALID_INPUT. Host does not guess
      latest, first, or all. instance refs={snapshot.selectedInstanceRefCount}.
    </p>
    <Button
      variant="outline"
      data-testid="home-submit-invoke"
      data-emits="submit_invoke"
      onclick={() => submitHomeInvoke()}
    >
      Invoke
    </Button>
    {#if snapshot.lastIncompatibilityCode === "INVALID_INPUT"}
      <Badge variant="destructive" data-testid="home-invoke-refusal">
        INVALID_INPUT. Zero or many instance_id refs. Host does not guess
        latest, first, or all.
      </Badge>
    {/if}
  </section>

  {#if snapshot.lastIncompatibility}
    <Badge variant="destructive" data-testid="home-typed-incompatibility">
      {snapshot.lastIncompatibility}
    </Badge>
  {/if}
  {#if snapshot.lastIncompatibilityCode === "query_unavailable"}
    <p data-testid="home-mailbox-incompatibility">
      {snapshot.lastIncompatibility}
    </p>
  {/if}
  {#if snapshot.lastIssuer}
    <p data-testid="home-last-issuer">{snapshot.lastIssuer}</p>
  {/if}
  {#if snapshot.lastResumeTarget}
    <p data-testid="home-last-resume">{snapshot.lastResumeTarget}</p>
  {/if}

  <aside
    class="border-border text-muted-foreground rounded-md border border-dashed p-3 text-sm"
    data-testid="factory-test-home-fixtures"
  >
    <p class="text-foreground font-medium">
      {FACTORY_TEST_LABEL} Home fixtures
    </p>
    <p>Local fixtures only. Observation is not a product destination.</p>
    <div class="mt-2 flex flex-wrap gap-2">
      {#each HOME_CHROME_STATES as item (item)}
        <Button
          variant={snapshot.chromeState === item ? "default" : "outline"}
          size="sm"
          data-testid={`fixture-home-${item}`}
          onclick={() => setHomeChromeState(item)}
        >
          {item}
        </Button>
      {/each}
      <Button
        variant="outline"
        size="sm"
        data-testid="fixture-selected-refs-many"
        onclick={() => applyHomeFixture("selected-refs-many")}
      >
        many instance_ids
      </Button>
      <Button
        variant="outline"
        size="sm"
        data-testid="fixture-selected-refs-one"
        onclick={() => applyHomeFixture("selected-refs-one")}
      >
        one instance_id
      </Button>
    </div>
  </aside>
</main>
