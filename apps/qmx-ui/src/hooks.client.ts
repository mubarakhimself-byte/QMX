if (import.meta.env.DEV) {
  // Virtual module from @reticlehq/vite-plugin; dev-only inspection bridge.
  // @ts-expect-error served only in vite dev
  void import("/@reticle-connect");
}
