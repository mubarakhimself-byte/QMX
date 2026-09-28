<script lang="ts">
  import { Button } from "$lib/components/ui/button";
  import { FACTORY_TEST_LABEL } from "$lib/bootstrap";

  let { onRequestInvoke }: { onRequestInvoke: () => void } = $props();
</script>

<div
  class="flex flex-col gap-1"
  data-testid="factory-test-widget"
  data-wire-client="forbidden"
  data-emits="request_invoke"
>
  <p class="text-[10px] leading-tight">
    {FACTORY_TEST_LABEL} widget. Bind and display only. Never owns invoke.
  </p>
  <Button
    size="sm"
    variant="outline"
    class="h-6 px-1 text-[10px]"
    data-testid="widget-request-invoke"
    data-wire-client="forbidden"
    onclick={() => onRequestInvoke()}
  >
    request invoke
  </Button>
</div>
