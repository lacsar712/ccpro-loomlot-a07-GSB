<script>
  import { onMount } from 'svelte';
  import { link } from 'svelte-spa-router';
  import { api } from '../lib/api.js';

  let stats = null;
  let vats = [];
  let error = '';

  // 列表口径手数：染程中且尚无合格清缸确认（与看板统计须相等）
  $: pendingFromList = vats.filter((v) => v.status === 'dyeing' && !v.hasValidConfirm).length;
  $: reconciled = stats && stats.vatDyeingNoConfirmCount === pendingFromList;

  onMount(async () => {
    try {
      [stats, vats] = await Promise.all([api('/dashboard/stats'), api('/vats')]);
    } catch (e) {
      error = e.message;
    }
  });
</script>

<h1 class="page-title">工艺总览</h1>
<p class="page-sub">按染坊 → 染缸 → 染程 → 色牢度推进；顶部步骤条可跳转各工序。</p>

{#if error}
  <p class="err">{error}</p>
{/if}

{#if stats}
  <div class="grid-stats">
    <div class="stat">
      <div class="n">{stats.dyeHouseTotal}</div>
      <div class="l">染坊</div>
    </div>
    <div class="stat">
      <div class="n">{stats.vatReadyCount}</div>
      <div class="l">就绪染缸</div>
    </div>
    <div class="stat">
      <div class="n">{stats.vatDyeingCount}</div>
      <div class="l">染色中</div>
    </div>
    <div class="stat">
      <div class="n">{stats.vatDyeingNoConfirmCount}</div>
      <div class="l">染程中待清缸确认</div>
    </div>
    <div class="stat">
      <div class="n">{stats.lotsLast7d}</div>
      <div class="l">近 7 日染程</div>
    </div>
    <div class="stat">
      <div class="n">{stats.checksLast24h}</div>
      <div class="l">近 24 时抽检</div>
    </div>
  </div>

  <div class="panel recon-panel">
    {#if reconciled}
      <p class="ok-msg" style="margin:0;">
        对账一致：看板统计染程中待清缸确认 {stats.vatDyeingNoConfirmCount} 缸 =
        染缸列表同条件手数 {pendingFromList}。
      </p>
    {:else}
      <p class="err" style="margin:0;">
        对账异常：看板统计 {stats.vatDyeingNoConfirmCount} 缸 ≠ 列表手数 {pendingFromList}。
      </p>
    {/if}
  </div>
{/if}

<div class="panel">
  <p style="margin:0 0 0.75rem;color:var(--indigo-mist);font-size:0.9rem;">
    业务约束：仅当染缸为 <strong>ready</strong> 或 <strong>dyeing</strong> 时可新建染程，已排液缸禁止再开染程或被改挂（409）；
    排液与<strong>最新一张清缸确认单</strong>绑死——残渣已清、管路已冲都勾是且照片≥2 张才放行，否则 409。从就绪进入染程中不看确认单。
  </p>
  <div class="toolbar">
    <a class="btn" href="/houses" use:link>进入染坊</a>
    <a class="btn ghost" href="/vats" use:link>管理染缸</a>
    <a class="btn ghost" href="/lots" use:link>登记染程</a>
    <a class="btn ghost" href="/checks" use:link>色牢度抽检</a>
  </div>
</div>

<style>
  .recon-panel {
    margin-bottom: 1.25rem;
  }
</style>
