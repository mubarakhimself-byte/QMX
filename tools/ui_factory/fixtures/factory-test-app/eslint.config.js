import svelte from "eslint-plugin-svelte";

export default [
  ...svelte.configs["flat/recommended"],
  { ignores: [".svelte-kit/**", "build/**", "dist/**", "node_modules/**"] },
];
