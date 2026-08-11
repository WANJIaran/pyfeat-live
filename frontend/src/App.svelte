<script lang="ts">
  import TopNav from './lib/components/TopNav.svelte';
  import UpdateBanner from './lib/components/UpdateBanner.svelte';
  import Live from './routes/Live.svelte';
  import Analyze from './routes/Analyze.svelte';
  import Viewer from './routes/Viewer.svelte';
  import LogsDrawer from './lib/components/LogsDrawer.svelte';
  import type { View } from './lib/types';

  let view: View = $state('live');
  let showLogs = $state(false);
  // Session the next Viewer mount should preselect (set by Analyze's
  // "Open in Viewer" and Live's recording-saved toast; cleared on manual
  // tab navigation so it doesn't go stale).
  let pendingSession: string | null = $state(null);

</script>

<div class="h-screen flex flex-col">
  <UpdateBanner />
  <TopNav {view} onViewChange={(v) => { pendingSession = null; view = v; }} logsOpen={showLogs} onToggleLogs={() => (showLogs = !showLogs)} />
  <div class="flex-1 flex min-h-0">
    <main class="flex-1 flex flex-col min-w-0 min-h-0">
      {#if view === 'live'}
        <Live onSwitchView={(v, sid) => { pendingSession = sid ?? null; view = v; }} />
      {:else if view === 'analyze'}
        <Analyze onSwitchView={(v, sid) => { pendingSession = sid ?? null; view = v; }} />
      {:else if view === 'viewer'}
        <Viewer initialSessionId={pendingSession} />
      {/if}
    </main>
    <!-- Logs drawer lives at the app level (flex sibling of the view) so the
         Logs toggle works on every tab, not just Live. -->
    {#if showLogs}
      <LogsDrawer onClose={() => (showLogs = false)} />
    {/if}
  </div>
</div>
