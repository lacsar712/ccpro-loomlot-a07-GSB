<script>
  import { onMount } from 'svelte';
  import { link } from 'svelte-spa-router';
  import { api, VAT_STATUS } from '../lib/api.js';

  let stats = null;
  let vats = [];
  let error = '';

  onMount(async () => {
    try {
      [stats, vats] = await Promise.all([api('/dashboard/stats'), api('/vats')]);
    } catch (e) {
      error = e.message;
    }
  });

  // 与看板统计同条件手数：染程中（dyeing）且尚无合格清缸确认
  $: pendingVats = vats.filter((v) => v.status === 'dyeing' && !v.hasValidConfirmation);
  $: reconciled =
    stats !== null && pendingVats.length === stats.vatDyeingUnconfirmedCount;
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
    <div class="stat warn-stat">
      <div class="n">{stats.vatDyeingUnconfirmedCount}</div>
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
{/if}

{#if stats}
  <div class="panel" style="margin-top:1rem;">
    <h2 style="margin:0 0 0.5rem;font-size:1rem;">清缸确认对账</h2>
    <p style="margin:0 0 0.75rem;color:var(--indigo-mist);font-size:0.9rem;">
      看板统计「染程中且尚无合格确认」缸数为
      <strong>{stats.vatDyeingUnconfirmedCount}</strong>，染缸列表同条件手数为
      <strong>{pendingVats.length}</strong>。
      {#if reconciled}
        <span style="color:var(--ok);">两边一致，对账通过。</span>
      {:else}
        <span class="err">两边不一致，请刷新核对。</span>
      {/if}
    </p>
    {#if pendingVats.length}
      <table>
        <thead>
          <tr>
            <th>ID</th>
            <th>缸号</th>
            <th>纤维</th>
            <th>状态</th>
            <th>合格确认</th>
          </tr>
        </thead>
        <tbody>
          {#each pendingVats as v}
            <tr>
              <td>{v.id}</td>
              <td>{v.vatCode}</td>
              <td>{v.fiberType}</td>
              <td><span class="badge {v.status}">{VAT_STATUS[v.status] || v.status}</span></td>
              <td><span class="badge drain">尚无合格确认</span></td>
            </tr>
          {/each}
        </tbody>
      </table>
    {:else}
      <p style="margin:0;font-size:0.85rem;color:var(--ok);">当前没有染程中待确认的染缸。</p>
    {/if}
  </div>
{/if}

<div class="panel">
  <p style="margin:0 0 0.75rem;color:var(--indigo-mist);font-size:0.9rem;">
    业务约束：仅当染缸为 <strong>ready</strong> 或 <strong>dyeing</strong> 时可新建染程；新建后染缸自动变为 dyeing，进入染程不看清缸确认。排液前必须先有合格清缸确认单（残渣已清、管路已冲均勾“是”且照片至少 2 张），否则排液被 409 拒绝；已排液染缸禁止再开染程或改挂染程。
  </p>
  <div class="toolbar">
    <a class="btn" href="/houses" use:link>进入染坊</a>
    <a class="btn ghost" href="/vats" use:link>管理染缸</a>
    <a class="btn ghost" href="/lots" use:link>登记染程</a>
    <a class="btn ghost" href="/checks" use:link>色牢度抽检</a>
  </div>
</div>

<style>
  .warn-stat .n {
    color: var(--warn);
  }
</style>
