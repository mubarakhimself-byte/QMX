<script lang="ts">
  import "../app.css";
  import { untrack } from "svelte";
  import * as Tooltip from "$lib/components/ui/tooltip";
  import PlatformRail from "$lib/workbench/PlatformRail.svelte";
  import StatusBar from "$lib/workbench/StatusBar.svelte";
  import InkBackground from "$lib/workbench/InkBackground.svelte";
  import { workbench, THEMES } from "$lib/workbench/workbench.svelte";
  import { SURFACES, ROTATE_EVERY } from "$lib/workbench/look";
  import { ART_STYLES } from "$lib/workbench/art";
  import { page } from "$app/state";
  import { resolve } from "$app/paths";

  let { children } = $props();

  // `?demo=off` / `?demo=on` on any URL switches demo mode and remembers it.
  $effect(() => {
    const asked = page.url.searchParams.get("demo");
    if (asked === "off" || asked === "on")
      untrack(() => workbench.setDemo(asked === "on"));
  });

  // Theme classes live on <html> so popovers and portals inherit them.
  $effect(() => {
    const root = document.documentElement;
    for (const t of THEMES) root.classList.remove(`theme-${t}`);
    root.classList.add(`theme-${workbench.theme}`);
    // Surface style: glass and liquid blur the frame; solid and brutalist don't.
    for (const s of SURFACES) root.classList.remove(`surface-${s.id}`);
    root.classList.add(`surface-${workbench.surface}`);
    root.classList.toggle(
      "glass",
      workbench.surface === "glass" || workbench.surface === "liquid",
    );
    // Paper is the one light theme.
    root.classList.toggle("dark", workbench.theme !== "paper");
  });

  // The operator's own theme, layered over the chosen one.
  const CUSTOM_PROPS = [
    "--primary",
    "--ring",
    "--sidebar-primary",
    "--background",
    "--panel",
    "--radius",
    "font-size",
  ];
  $effect(() => {
    const st = document.documentElement.style;
    const c = workbench.custom;
    for (const k of CUSTOM_PROPS) st.removeProperty(k);
    st.setProperty("font-size", `${workbench.textSize}px`);
    if (!c.on) return;
    st.setProperty("--primary", c.accent);
    st.setProperty("--ring", c.accent);
    st.setProperty("--sidebar-primary", c.accent);
    st.setProperty("--background", c.background);
    st.setProperty(
      "--panel",
      `color-mix(in oklab, color-mix(in oklab, ${c.background} 88%, white) ${Math.round(c.panel * 100)}%, transparent)`,
    );
    st.setProperty("--radius", `${c.radius}px`);
    st.setProperty("font-size", `${c.text}px`);
  });

  // Background art that changes on its own: each visit, hourly or daily.
  $effect(() => {
    const mode = workbench.artRotate;
    if (mode === "off") return;
    const rotate = () => {
      const style =
        ART_STYLES[Math.floor(Math.random() * ART_STYLES.length)].id;
      workbench.setArt({
        ...workbench.art,
        style,
        seed: Math.floor(Math.random() * 99999),
      });
      try {
        localStorage.setItem("qmx.art.rotatedAt", String(Date.now()));
      } catch {
        /* storage unavailable */
      }
    };
    const every = ROTATE_EVERY[mode];
    // untrack: rotating writes the art, which must not re-run this effect.
    if (every === null) {
      untrack(rotate);
      return;
    }
    const check = () => {
      let last = 0;
      try {
        last = Number(localStorage.getItem("qmx.art.rotatedAt") ?? 0);
      } catch {
        /* storage unavailable */
      }
      if (Date.now() - last >= every) rotate();
    };
    untrack(check);
    const t = setInterval(check, 60_000);
    return () => clearInterval(t);
  });
  // Trading surfaces never get the decorative background.
  const showInk = $derived(workbench.inkEnabled);
</script>

<Tooltip.Provider delayDuration={300}>
  <div class="text-foreground flex h-svh flex-col overflow-hidden">
    {#if showInk}<InkBackground />{/if}
    <div class="flex min-h-0 flex-1">
      <PlatformRail />
      <main class="min-w-0 flex-1 overflow-hidden">{@render children()}</main>
    </div>
    <StatusBar />
    {#if workbench.notice}
      <div
        role="status"
        class="surface fixed right-4 bottom-10 z-50 flex max-w-md items-center gap-3 rounded-lg px-4 py-2.5 text-sm"
      >
        <span class="min-w-0 flex-1 truncate">{workbench.notice.text}</span>
        {#if workbench.notice.href}
          <a
            class="text-primary shrink-0 font-medium hover:underline"
            href={resolve(workbench.notice.href as "/")}
            >{workbench.notice.action ?? "Open"}</a
          >
        {/if}
      </div>
    {/if}
  </div>
</Tooltip.Provider>
