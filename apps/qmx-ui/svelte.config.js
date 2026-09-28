import adapter from "@sveltejs/adapter-static";
import { vitePreprocess } from "@sveltejs/vite-plugin-svelte";

/** @type {import('@sveltejs/kit').Config} */
const config = {
  preprocess: vitePreprocess(),
  kit: {
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
