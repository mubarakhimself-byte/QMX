if (import.meta.env.DEV) {
  // Virtual module from @reticlehq/vite-plugin; pairs with the daemon token.
  // @ts-expect-error served only in vite dev
  void import("/@reticle-connect").then(() => import("./reticle-dev"));
}
