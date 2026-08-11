<script lang="ts">
  type FacialBehavior = {
    facial_valence: number;
    facial_activation: number;
    confidence: number;
    expression_evidence: Record<string, number>;
  };

  let { value }: { value: FacialBehavior } = $props();

  const clamp = (n: number, low: number, high: number) => Math.max(low, Math.min(high, n));
  const valence = $derived(clamp(value.facial_valence, -100, 100));
  const valenceLeft = $derived(50 + Math.min(0, valence) / 2);
  const valenceWidth = $derived(Math.abs(valence) / 2);
  const activation = $derived(clamp(value.facial_activation, 0, 100));
  const confidence = $derived(clamp(value.confidence, 0, 100));
  const strongest = $derived(
    Object.entries(value.expression_evidence ?? {}).reduce(
      (best, current) => current[1] > best[1] ? current : best,
      ['none', 0] as [string, number],
    ),
  );
  const evidenceNames: Record<string, string> = {
    smile_like: '微笑', frown_like: '皱眉', surprise_like: '惊讶',
    tension_like: '紧张', engagement_like: '投入', none: '无',
  };
  const evidenceLabel = $derived(evidenceNames[strongest[0]] ?? strongest[0].replace('_like', '').replaceAll('_', ' '));
</script>

<div class="rounded bg-black/70 px-2 py-1.5 text-[8px] text-zinc-300">
  <div class="mb-1 tracking-wide text-zinc-400">面部行为证据</div>
  <div class="grid grid-cols-[44px_1fr_28px] items-center gap-x-1 gap-y-0.5 font-mono">
    <span>效价</span>
    <div class="relative h-1 rounded bg-zinc-800">
      <span class="absolute top-0 h-1 bg-sky-400" style="left: {valenceLeft}%; width: {valenceWidth}%;"></span>
    </div>
    <span class="text-right">{valence.toFixed(0)}</span>
    <span>唤醒度</span>
    <div class="h-1 rounded bg-zinc-800"><div class="h-1 rounded bg-amber-400" style="width: {activation}%;"></div></div>
    <span class="text-right">{activation.toFixed(0)}</span>
    <span>置信度</span>
    <div class="h-1 rounded bg-zinc-800"><div class="h-1 rounded {confidence < 50 ? 'bg-red-400' : 'bg-green-400'}" style="width: {confidence}%;"></div></div>
    <span class="text-right">{confidence.toFixed(0)}</span>
  </div>
  <div class="mt-1 flex justify-between border-t border-zinc-800 pt-1">
    <span>最强：{evidenceLabel}</span><span>{(strongest[1] * 100).toFixed(0)}</span>
  </div>
  {#if confidence < 50}
    <div class="mt-0.5 text-red-300">画面质量低，请勿解读</div>
  {/if}
  <div class="mt-0.5 text-[7px] text-zinc-500">仅表示可观察动作，不代表真实内心情绪</div>
</div>
