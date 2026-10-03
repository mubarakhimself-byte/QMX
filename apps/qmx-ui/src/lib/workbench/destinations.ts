import type { Component } from "svelte";
import House from "@lucide/svelte/icons/house";
import MessagesSquare from "@lucide/svelte/icons/messages-square";
import LibraryBig from "@lucide/svelte/icons/library-big";
import FlaskConical from "@lucide/svelte/icons/flask-conical";
import Briefcase from "@lucide/svelte/icons/briefcase-business";
import Settings from "@lucide/svelte/icons/settings";

/**
 * Platform rail destinations (UI EXPERIENCE-AND-LAYOUT §1).
 * Product destinations sit above the divider and exist with zero opened apps.
 * Settings is chrome, pinned to the rail foot.
 */
export type Destination = {
  id: "home" | "copilot" | "library" | "lab" | "portfolio" | "settings";
  label: string;
  href: string;
  icon: Component;
  shortcut: string;
};

export const PRODUCT_DESTINATIONS: readonly Destination[] = [
  { id: "home", label: "Home", href: "/home", icon: House, shortcut: "1" },
  {
    id: "copilot",
    label: "Copilot",
    href: "/copilot",
    icon: MessagesSquare,
    shortcut: "2",
  },
  {
    id: "library",
    label: "Library",
    href: "/library",
    icon: LibraryBig,
    shortcut: "3",
  },
  {
    // Docs name this destination Authoring (DEC-0470); operator ruled the
    // merged Lab on 2026-10-02 and the rename is flagged for the docs.
    id: "lab",
    label: "Lab",
    href: "/lab",
    icon: FlaskConical,
    shortcut: "4",
  },
  {
    // Books, risk, promotions, allocation and live trading (the trading node
    // folded in, operator ruling 2026-10-03). Not yet a docs destination.
    id: "portfolio",
    label: "Portfolio",
    href: "/portfolio",
    icon: Briefcase,
    shortcut: "5",
  },
];

export const SETTINGS_DESTINATION: Destination = {
  id: "settings",
  label: "Settings",
  href: "/settings",
  icon: Settings,
  shortcut: ",",
};

export function isActive(pathname: string, href: string): boolean {
  return pathname === href || pathname.startsWith(href + "/");
}
