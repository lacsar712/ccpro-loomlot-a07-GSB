<script>
  import { onMount } from 'svelte';
  import { api, VAT_STATUS, toLocalInput, fromLocalInput } from '../lib/api.js';

  let houses = [];
  let rows = [];
  let confirmations = [];
  let error = '';
  let form = {
    dyeHouseId: '',
    vatCode: '',
    fiberType: '棉',
    capacityL: 500,
    status: 'ready',
  };
  let editing = null;

  let confirmVatId = null;
  let confirmForm = {
    residueCleared: true,
    pipeFlushed: true,
    photoCount: 2,
    confirmedAt: toLocalInput(new Date().toISOString()),
    confirmer: '染程操作员',
  };

  async function load() {
    error = '';
    try {
      [houses, rows, confirmations] = await Promise.all([
        api('/dye-houses'),
        api('/vats'),
        api('/tank-confirmations'),
      ]);
      if (!form.dyeHouseId && houses.length) form.dyeHouseId = String(houses[0].id);
    } catch (e) {
      error = e.message;
    }
  }

  onMount(load);

  function houseName(id) {
    return houses.find((h) => h.id === id)?.name || id;
  }

  // 列表按 id 倒序，每口缸的第一条即最新确认单
  function latestFor(vatId) {
    return confirmations.find((c) => c.vatId === vatId) || null;
  }

  async function save() {
    error = '';
    try {
      const body = {
        dyeHouseId: Number(form.dyeHouseId),
        vatCode: form.vatCode.trim(),
        fiberType: form.fiberType.trim(),
        capacityL: Number(form.capacityL),
        status: form.status,
      };
      if (editing) {
        await api(`/vats/${editing}`, { method: 'PUT', body: JSON.stringify(body) });
      } else {
        await api('/vats', { method: 'POST', body: JSON.stringify(body) });
      }
      editing = null;
      form = {
        dyeHouseId: form.dyeHouseId,
        vatCode: '',
        fiberType: '棉',
        capacityL: 500,
        status: 'ready',
      };
      await load();
    } catch (e) {
      error = e.message;
    }
  }

  function startEdit(row) {
    editing = row.id;
    form = {
      dyeHouseId: String(row.dyeHouseId),
      vatCode: row.vatCode,
      fiberType: row.fiberType,
      capacityL: row.capacityL,
      status: row.status,
    };
  }

  function startConfirm(row) {
    confirmVatId = row.id;
    confirmForm = {
      residueCleared: true,
      pipeFlushed: true,
      photoCount: 2,
      confirmedAt: toLocalInput(new Date().toISOString()),
      confirmer: confirmForm.confirmer || '染程操作员',
    };
    error = '';
  }

  async function submitConfirmation() {
    error = '';
    try {
      await api('/tank-confirmations', {
        method: 'POST',
        body: JSON.stringify({
          vatId: confirmVatId,
          residueCleared: !!confirmForm.residueCleared,
          pipeFlushed: !!confirmForm.pipeFlushed,
          photoCount: Number(confirmForm.photoCount),
          confirmedAt: fromLocalInput(confirmForm.confirmedAt),
          confirmer: confirmForm.confirmer.trim(),
        }),
      });
      confirmVatId = null;
      await load();
    } catch (e) {
      error = e.message;
    }
  }

  async function drain(id) {
    error = '';
    try {
      await api(`/vats/${id}/drain`, { method: 'POST' });
      await load();
    } catch (e) {
      error = e.message;
    }
  }

  async function remove(id) {
    if (!confirm('确认删除该染缸？')) return;
    error = '';
    try {
      await api(`/vats/${id}`, { method: 'DELETE' });
      await load();
    } catch (e) {
      error = e.message;
    }
  }
</script>

<h1 class="page-title">染缸</h1>
<p class="page-sub">
  状态：就绪 / 染色中 / 排液。容量单位为升。排液前必须先填写合格的清缸确认单。
</p>

<div class="panel" style="margin-bottom:1rem;">
  <div class="form-grid">
    <label
      >所属染坊
      <select bind:value={form.dyeHouseId}>
        {#each houses as h}
          <option value={String(h.id)}>{h.name}</option>
        {/each}
      </select>
    </label>
    <label>缸号 <input bind:value={form.vatCode} /></label>
    <label>纤维类型 <input bind:value={form.fiberType} /></label>
    <label>容量 (L) <input type="number" step="0.1" bind:value={form.capacityL} /></label>
    <label
      >状态
      <select bind:value={form.status}>
        <option value="ready">就绪</option>
        <option value="dyeing">染色中</option>
        <option value="drain">排液</option>
      </select>
    </label>
  </div>
  <div class="toolbar">
    <button class="btn" type="button" on:click={save}>{editing ? '保存修改' : '新建染缸'}</button>
    {#if editing}
      <button
        class="btn ghost"
        type="button"
        on:click={() => {
          editing = null;
        }}>取消</button
      >
    {/if}
  </div>
  {#if error}<p class="err">{error}</p>{/if}
</div>

{#if confirmVatId !== null}
  {@const vat = rows.find((r) => r.id === confirmVatId)}
  <div class="panel" style="margin-bottom:1rem;border-color:rgba(107,92,231,0.55);">
    <h2 style="margin:0 0 0.25rem;font-size:1rem;">
      清缸确认单 · {vat ? vat.vatCode : confirmVatId}
    </h2>
    <p style="margin:0 0 0.75rem;color:var(--indigo-mist);font-size:0.85rem;">
      排液前必须先提交本确认单。两项均勾“是”且照片至少 2 张才算合格；同缸可多次确认，以最新一张为准。
    </p>
    <div class="form-grid">
      <label class="check-row">
        <input type="checkbox" bind:checked={confirmForm.residueCleared} />
        <span
          >残渣已清（勾“是”表示缸内残渣、沉淀物已清理干净）</span
        >
      </label>
      <label class="check-row">
        <input type="checkbox" bind:checked={confirmForm.pipeFlushed} />
        <span>管路已冲（勾“是”表示排液管路已用清水冲洗干净）</span>
      </label>
      <label>照片张数（至少 2 张） <input type="number" min="0" bind:value={confirmForm.photoCount} /></label>
      <label
        >确认时刻
        <input type="datetime-local" bind:value={confirmForm.confirmedAt} />
      </label>
      <label>确认人 <input bind:value={confirmForm.confirmer} /></label>
    </div>
    <div class="toolbar">
      <button class="btn" type="button" on:click={submitConfirmation}>提交确认</button>
      <button class="btn ghost" type="button" on:click={() => (confirmVatId = null)}>取消</button>
    </div>
  </div>
{/if}

<div class="panel">
  <table>
    <thead>
      <tr>
        <th>ID</th>
        <th>染坊</th>
        <th>缸号</th>
        <th>纤维</th>
        <th>容量 L</th>
        <th>状态</th>
        <th>清缸确认（最新）</th>
        <th></th>
      </tr>
    </thead>
    <tbody>
      {#each rows as row}
        {@const latest = latestFor(row.id)}
        <tr>
          <td>{row.id}</td>
          <td>{houseName(row.dyeHouseId)}</td>
          <td>{row.vatCode}</td>
          <td>{row.fiberType}</td>
          <td>{row.capacityL}</td>
          <td><span class="badge {row.status}">{VAT_STATUS[row.status] || row.status}</span></td>
          <td>
            {#if latest}
              {#if latest.isValid}
                <span class="badge ready">已合格</span>
              {:else}
                <span class="badge drain">最新不合格</span>
              {/if}
              <span style="font-size:0.75rem;color:var(--indigo-mist);margin-left:0.35rem;">
                {latest.confirmer} · {latest.photoCount} 张 · {new Date(latest.confirmedAt).toLocaleString()}
              </span>
            {:else}
              <span class="badge drain">未确认</span>
            {/if}
          </td>
          <td class="row-actions">
            {#if row.status !== 'drain'}
              <button class="btn ghost small" type="button" on:click={() => startConfirm(row)}
                >清缸确认</button
              >
              <button class="btn ghost small" type="button" on:click={() => drain(row.id)}
                >完成排液</button
              >
            {/if}
            <button class="btn ghost small" type="button" on:click={() => startEdit(row)}>编辑</button>
            <button class="btn danger small" type="button" on:click={() => remove(row.id)}>删除</button>
          </td>
        </tr>
      {/each}
    </tbody>
  </table>
</div>

<style>
  .check-row {
    flex-direction: row;
    align-items: center;
    gap: 0.5rem;
  }
  .check-row input[type='checkbox'] {
    width: auto;
  }
</style>
