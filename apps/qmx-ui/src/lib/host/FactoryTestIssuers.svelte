<script lang="ts">
  import { onMount } from "svelte";
  import { Badge } from "$lib/components/ui/badge";
  import { Button } from "$lib/components/ui/button";
  import { FACTORY_TEST_LABEL } from "$lib/bootstrap";
  import FactoryTestWidget from "$lib/widgets/FactoryTestWidget.svelte";
  import { claimBrowserProducer } from "./producer";
  import {
    applyMissingCapabilityFixture,
    handleCancelDisplay,
    handleCancelJob,
    handleListMailbox,
    handleRequestInvoke,
    handleSubmitChat,
    handleSubmitInvoke,
    hostState,
    setProducerId,
  } from "./runtime";

  const snapshot = $derived($hostState);

  onMount(() => {
    void claimBrowserProducer().then((claim) => {
      setProducerId(claim.producer_id);
    });
  });
</script>

<div data-testid="factory-test-issuers" data-label={FACTORY_TEST_LABEL}>
  <p class="text-foreground font-medium">{FACTORY_TEST_LABEL} unique issuers</p>
  <p>Widgets emit request_invoke. Host owns the wire.</p>
  <p data-testid="host-producer-id" class="truncate">
    producer_id {snapshot.producerId || "pending"}
  </p>
  <FactoryTestWidget onRequestInvoke={handleRequestInvoke} />
  <div class="mt-1 flex flex-col gap-1">
    <Button
      size="sm"
      variant="outline"
      class="h-6 px-1 text-[10px]"
      data-testid="composer-submit-chat"
      data-emits="submit_chat"
      onclick={handleSubmitChat}
    >
      submit chat
    </Button>
    <Button
      size="sm"
      variant="outline"
      class="h-6 px-1 text-[10px]"
      data-testid="composer-submit-invoke"
      data-emits="submit_invoke"
      onclick={handleSubmitInvoke}
    >
      submit invoke
    </Button>
    <Button
      size="sm"
      variant="outline"
      class="h-6 px-1 text-[10px]"
      data-testid="run-inspector-cancel"
      data-emits="cancel_job"
      onclick={handleCancelJob}
    >
      cancel job
    </Button>
    <Button
      size="sm"
      variant="ghost"
      class="h-6 px-1 text-[10px]"
      data-testid="conversation-cancel-display"
      data-emits="cancel_display"
      onclick={handleCancelDisplay}
    >
      stop display
    </Button>
    <Button
      size="sm"
      variant="ghost"
      class="h-6 px-1 text-[10px]"
      data-testid="query-list-mailbox"
      onclick={handleListMailbox}
    >
      list mailbox
    </Button>
    <Button
      size="sm"
      variant="outline"
      class="h-6 px-1 text-[10px]"
      data-testid="fixture-missing-capability"
      onclick={applyMissingCapabilityFixture}
    >
      missing capability
    </Button>
  </div>
  {#if snapshot.lastCallerEvent}
    <p data-testid="host-last-caller">{snapshot.lastCallerEvent}</p>
  {/if}
  {#if snapshot.lastIssuer}
    <p data-testid="host-last-issuer">{snapshot.lastIssuer}</p>
  {/if}
  {#if snapshot.lastIncompatibility}
    <Badge variant="destructive" data-testid="typed-incompatibility">
      {snapshot.lastIncompatibility}
    </Badge>
  {/if}
  {#if snapshot.chatProceeded}
    <p data-testid="chat-still-proceeds">send_message proceeded</p>
  {/if}
  <p class="sr-only" data-testid="widget-wire-import">forbidden</p>
  <p class="sr-only" data-testid="host-shell-usable">
    {String(snapshot.shellUsable)}
  </p>
</div>
