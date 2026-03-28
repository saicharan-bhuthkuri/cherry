<script lang="ts">
  import '../app.css';
  import "leaflet/dist/leaflet.css";
  import type { Snippet } from 'svelte';

  let { children }: { children: Snippet } = $props();
</script>

<svelte:head>
  <title>SafeRoute Peddapalli</title>
</svelte:head>

<div class="font-[Inter] antialiased bg-gray-950 text-white min-h-screen">
  {@render children()}
</div>
