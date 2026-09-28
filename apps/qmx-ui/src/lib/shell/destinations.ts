/**
 * Client-local platform destinations (DEC-0470, UX-DR-UI-01).
 * Order is not a `psess:` field. Settings is chrome, not a fifth product.
 * No third ProductSessionProfile.
 */

export const PRODUCT_DESTINATION_IDS = [
  "home",
  "copilot",
  "library",
  "authoring",
] as const;

export type ProductDestinationId = (typeof PRODUCT_DESTINATION_IDS)[number];

/** Closed set. Home/Authoring use authoring; in-app copilot uses app-use. */
export const PRODUCT_SESSION_PROFILES = ["authoring", "app-use"] as const;
export type ProductSessionProfile = (typeof PRODUCT_SESSION_PROFILES)[number];

export type DestinationKind = "product" | "chrome";

export type ProductDestination = {
  id: ProductDestinationId;
  label: string;
  href: `/${ProductDestinationId}`;
  kind: "product";
  purpose: string;
  profile?: ProductSessionProfile;
};

export type ChromeDestination = {
  id: "settings";
  label: "Settings";
  href: "/settings";
  kind: "chrome";
  purpose: "host chrome, not a fifth product destination";
};

export const PRODUCT_DESTINATIONS: readonly ProductDestination[] = [
  {
    id: "home",
    label: "Home",
    href: "/home",
    kind: "product",
    purpose: "work / attention / resume",
    profile: "authoring",
  },
  {
    id: "copilot",
    label: "Copilot",
    href: "/copilot",
    kind: "product",
    purpose: "conversation workspace",
  },
  {
    id: "library",
    label: "Library",
    href: "/library",
    kind: "product",
    purpose: "typed hits without collapsing kinds",
  },
  {
    id: "authoring",
    label: "Authoring",
    href: "/authoring",
    kind: "product",
    purpose: "graph/code/detail family, reachable with zero apps",
    profile: "authoring",
  },
];

export const SETTINGS_CHROME: ChromeDestination = {
  id: "settings",
  label: "Settings",
  href: "/settings",
  kind: "chrome",
  purpose: "host chrome, not a fifth product destination",
};

export const PRODUCT_DESTINATION_COUNT = 4 as const;

export function isProductDestination(id: string): id is ProductDestinationId {
  return (PRODUCT_DESTINATION_IDS as readonly string[]).includes(id);
}

export function destinationFromPath(
  pathname: string,
): ProductDestinationId | "settings" | null {
  const trimmed = pathname.replace(/\/+$/, "") || "/";
  if (trimmed === "/settings") return "settings";
  const match = PRODUCT_DESTINATIONS.find((item) => item.href === trimmed);
  return match?.id ?? null;
}

export function profileForDestination(
  id: ProductDestinationId,
): ProductSessionProfile | undefined {
  return PRODUCT_DESTINATIONS.find((item) => item.id === id)?.profile;
}
