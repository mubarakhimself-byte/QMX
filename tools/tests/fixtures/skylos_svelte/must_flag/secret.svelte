<script lang="ts">
  // FACTORY-TEST negative fixture: a live-looking secret a scanner should see
  // if it actually parses .svelte. Not product code.
  const aws = "AKIAIOSFODNN7EXAMPLE";
  export const leaked = aws;
</script>

<p>{leaked}</p>
