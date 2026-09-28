import adapter from "@sveltejs/adapter-static";
import { vitePreprocess } from "@sveltejs/vite-plugin-svelte";
import { execFileSync } from "node:child_process";

/** @type {import('@sveltejs/kit').Config} */
const config = {
  preprocess: vitePreprocess(),
  kit: {
    version: {
      name: execFileSync("git", ["rev-parse", "HEAD"], {
        encoding: "utf8",
        timeout: 2000,
        windowsHide: true,
      }).trim(),
    },
    // Public assets live in public/ so committed static/200.html is the
    // story-tree SPA-fallback marker and does not collide with the
    // adapter-generated build/200.html shell.
    files: {
      assets: "public",
    },
    adapter: adapter({
      pages: "build",
      assets: "build",
      fallback: "200.html",
      precompress: false,
      strict: true,
    }),
  },
};

export default config;
