<script lang="ts">
  /**
   * Safety as controls: safe mode (shared with Apps), the go-live rule per
   * risk class (Touches money locked to your signature), spend caps and the
   * background agents' share of the Claude plan, the kill switch itself,
   * and the standing "always allow" approvals you can revoke.
   */
  import Lock from "@lucide/svelte/icons/lock";
  import ArrowRight from "@lucide/svelte/icons/arrow-right";
  import { resolve } from "$app/paths";
  import { Button } from "$lib/components/ui/button";
  import { Input } from "$lib/components/ui/input";
  import { Slider } from "$lib/components/ui/slider";
  import { Switch } from "$lib/components/ui/switch";
  import { apps, RISK } from "$lib/apps/apps.svelte";
  import {
    kill,
    KILL_LABEL,
    scopeKey,
    type KillState,
  } from "$lib/portfolio/kill.svelte";
  import { cn } from "$lib/utils";
  import { workbench } from "$lib/workbench/workbench.svelte";
  import Choice from "./Choice.svelte";
  import Group from "./Group.svelte";
  import Row from "./Row.svelte";
  import { GO_LIVE, settings, type GoLive } from "./settings.svelte";

  const s = settings.safety;
  const goLiveOptions = Object.entries(GO_LIVE).map(([value, label]) => ({
    value,
    label,
  }));

  const STOPS: {
    to: KillState;
    label: string;
    button: string;
    confirm: string;
    tip: string;
  }[] = [
    {
      to: "no-new",
      label: "Stop new trades",
      button: "Stop everywhere",
      confirm: "Click again to stop",
      tip: "Open positions stay and are managed; no bot opens a new one.",
    },
    {
      to: "halted",
      label: "Close and halt",
      button: "Halt everything",
      confirm: "Click again to halt",
      tip: "Closes every position on every server, then stops every bot.",
    },
  ];
  let armed = $state<KillState | null>(null);
  let armTimer: ReturnType<typeof setTimeout> | undefined;
  const now = $derived(kill.stateOf(scopeKey.all));

  function press(to: KillState, label: string) {
    clearTimeout(armTimer);
    if (armed !== to) {
      armed = to;
      armTimer = setTimeout(() => (armed = null), 5000);
      return;
    }
    armed = null;
    kill.set(scopeKey.all, to);
    workbench.notify(
      `${label} everywhere. Demo only: the real switch goes to every trading server.`,
    );
  }
</script>

<div class="grid items-start gap-group 2xl:grid-cols-2">
  <div class="flex flex-col gap-group">
    <Group
      title="Kill switch"
      meta={workbench.demoMode ? `Now: ${KILL_LABEL[now]}` : "Nothing to stop"}
    >
      {#snippet actions()}
        <a
          href={resolve("/portfolio")}
          class="text-primary inline-flex items-center gap-1 text-sm"
          >Per pod and server<ArrowRight class="size-4" /></a
        >
      {/snippet}
      {#each STOPS as st (st.to)}
        <Row label={st.label} tip={st.tip}>
          <Button
            size="sm"
            variant={st.to === "halted" || armed === st.to
              ? "destructive"
              : "outline"}
            class={cn("min-w-56", armed === st.to && "ring-destructive ring-2")}
            disabled={!workbench.demoMode || now === st.to || now === "halted"}
            onclick={() => press(st.to, st.label)}
            >{armed === st.to ? st.confirm : st.button}</Button
          >
        </Row>
      {/each}
      {#if now !== "active"}
        <Row label="Resume trading">
          <Button
            size="sm"
            variant="outline"
            onclick={() => {
              kill.set(scopeKey.all, "active");
              workbench.notify("Trading resumed everywhere (demo).");
            }}>Resume</Button
          >
        </Row>
      {/if}
    </Group>

    <Group title="Go live">
      <Row
        label="Safe mode"
        tip="Turns off every mini app and add-on that didn't ship with QMX. The same switch as in Apps."
      >
        <Switch bind:checked={apps.safe} aria-label="Safe mode" />
      </Row>
      {#each ["show", "work"] as const as k (k)}
        <Row label={RISK[k].label} tip={RISK[k].rule}>
          <Choice
            label={`${RISK[k].label} goes live`}
            value={s.goLive[k]}
            options={goLiveOptions}
            onchange={(v) => (s.goLive[k] = v as GoLive)}
            class="min-w-56"
          />
        </Row>
      {/each}
      <Row
        label={RISK.money.label}
        tip="No copilot, agent or mini app can move or risk real money. This can't be changed."
      >
        <span
          class="bg-input/50 text-muted-foreground inline-flex h-8 min-w-56 items-center gap-2 rounded-2xl px-3 text-sm"
          aria-label="Touches money: you sign every time (locked)"
          ><Lock class="size-3.5" />You sign every time</span
        >
      </Row>
    </Group>
  </div>

  <div class="flex flex-col gap-group">
    <Group
      title="Budgets"
      tip="Daily caps in USD. When a cap is reached, new work waits until tomorrow and you are alerted."
    >
      <Row label="Agents, per day">
        <span class="text-muted-foreground">$</span>
        <Input
          type="number"
          min={0}
          step={5}
          class="num h-8 w-24 text-right"
          bind:value={s.agentsUsd}
          aria-label="Agents daily cap in USD"
        />
      </Row>
      <Row label="Mini apps, per day">
        <span class="text-muted-foreground">$</span>
        <Input
          type="number"
          min={0}
          step={5}
          class="num h-8 w-24 text-right"
          bind:value={s.appsUsd}
          aria-label="Mini apps daily cap in USD"
        />
      </Row>
      <Row
        label="Background agents' Claude share"
        tip="The most of your Claude plan's 5-hour usage that background agents may use. The rest stays free for you."
      >
        <Slider
          type="single"
          min={0}
          max={100}
          step={5}
          bind:value={s.planShare}
          class="w-48"
          aria-label="Background agents' share of the Claude plan"
        />
        <span class="num w-12 text-right">{s.planShare}%</span>
      </Row>
    </Group>

    <Group
      title="Always allowed"
      tip="Actions you told a copilot it may repeat without asking. Revoke to make it ask again."
      meta={`${workbench.demoMode ? s.sticky.length : 0}`}
    >
      {#each workbench.demoMode ? s.sticky : [] as a (a.id)}
        <div
          class="flex min-h-11 items-center gap-3 border-t py-row first:border-t-0"
        >
          <span class="min-w-0 flex-1"
            >{a.what}<span class="text-muted-foreground block text-sm"
              >{a.who}</span
            ></span
          >
          <Button
            size="sm"
            variant="outline"
            onclick={() => {
              s.sticky = s.sticky.filter((x) => x.id !== a.id);
              workbench.notify(`Revoked: ${a.what}`);
            }}>Revoke</Button
          >
        </div>
      {:else}
        <p class="text-muted-foreground py-row">Nothing always allowed</p>
      {/each}
    </Group>
  </div>
</div>
