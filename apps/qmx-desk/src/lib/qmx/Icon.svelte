<script lang="ts" module>
  import {
    House, Bot, Library, FlaskConical, Workflow, ChartCandlestick, LayoutGrid, Gauge, Settings,
    Inbox, Activity, Loader, ChartLine, Calendar, MessageSquare, PanelRight, ScanEye, Table,
    GitCompare, Scale, FolderKanban, CalendarClock, ListTree, Server, List, Radar, Signal,
    KeyRound, Route, ChartColumn, Maximize2, Minus, Ellipsis, MessageSquarePlus, Search, Plus, X,
    ChevronDown, Laptop, Square, OctagonX, Sparkles, Check, Circle, ArrowUp, PanelLeft, Copy,
    CornerDownLeft, Pause, Play, ArrowLeft, ArrowRight, ArrowDown, ChevronRight, Undo2, Archive,
    RotateCcw, Puzzle, PencilRuler, Download, PanelLeftClose, PanelLeftOpen, Cpu, ArrowUpRight,
    ShieldCheck,
  } from "@lucide/svelte";

  // One icon set for the whole app. Screens name icons; they never import them.
  export const icons = {
    house: House, bot: Bot, library: Library, "flask-conical": FlaskConical, workflow: Workflow,
    candlestick: ChartCandlestick, "layout-grid": LayoutGrid, gauge: Gauge, settings: Settings,
    inbox: Inbox, activity: Activity, loader: Loader, "line-chart": ChartLine, calendar: Calendar,
    "message-square": MessageSquare, "panel-right": PanelRight, "scan-eye": ScanEye, table: Table,
    "git-compare": GitCompare, scale: Scale, "folder-kanban": FolderKanban,
    "calendar-clock": CalendarClock, "list-tree": ListTree, server: Server, list: List,
    radar: Radar, signal: Signal, "key-round": KeyRound, route: Route, "bar-chart-3": ChartColumn,
    expand: Maximize2, minus: Minus, more: Ellipsis, send: MessageSquarePlus, search: Search,
    plus: Plus, x: X, "chevron-down": ChevronDown, laptop: Laptop, square: Square,
    stop: OctagonX, sparkles: Sparkles, check: Check, circle: Circle, "arrow-up": ArrowUp,
    "panel-left": PanelLeft, copy: Copy, enter: CornerDownLeft,
    pause: Pause, play: Play, "arrow-left": ArrowLeft, "arrow-right": ArrowRight, "arrow-up-1": ArrowUp,
    "arrow-down": ArrowDown, "chevron-right": ChevronRight, undo: Undo2, archive: Archive, retry: RotateCcw,
    puzzle: Puzzle, edit: PencilRuler, download: Download, "nav-close": PanelLeftClose, "nav-open": PanelLeftOpen,
    cpu: Cpu, out: ArrowUpRight, shield: ShieldCheck,
  } as const;
  export type IconName = keyof typeof icons;
</script>

<script lang="ts">
  let { name, class: cls = "size-4" }: { name: string; class?: string } = $props();
  const C = $derived(icons[name as IconName] ?? Circle);
</script>

<C class={cls} strokeWidth={1.75} aria-hidden="true" />
