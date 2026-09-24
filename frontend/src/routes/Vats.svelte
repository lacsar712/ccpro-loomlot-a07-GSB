<script>
  import { onMount } from 'svelte';
  import { api, VAT_STATUS, toLocalInput, fromLocalInput } from '../lib/api.js';

  let houses = [];
  let rows = [];
  let confirms = [];
  let error = '';
  let okMsg = '';
  let form = {
    dyeHouseId: '',
    vatCode: '',
    fiberType: '棉',
    capacityL: 500,
    status: 'ready',
  };
  let editing = null;

  // 清缸确认单表单（针对某一口缸）
  let confirmingVatId = null;
  let cfForm = {
    residueCleared: true,
    pipeFlushed: true,
    photoCount: 2,
    confirmedAt: toLocalInput(new Date().toISOString()),
    confirmerName: '',
  };

  async function load() {
    error = '';
    try {
      [houses, rows, confirms] = await Promise.all([
        api('/dye-houses'),
        api('/vats'),
        api('/clean-confirms'),
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

  // 同缸保留历史，以最新一张为准（接口已按 id 倒序）
  let latestByVat = {};
  $: {
    latestByVat = {};
    for (const c of confirms) {
      if (!latestByVat[c.vatId]) latestByVat[c.vatId] = c;
    }
  }

  // 染程中且尚无合格确认（与看板 vatDyeingNoConfirmCount 同口径）
  let pendingVats = [];
  $: pendingVats = rows.filter((v) => v.status === 'dyeing' && !v.hasValidConfirm);

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
    confirmingVatId = row.id;
    error = '';
    okMsg = '';
    cfForm = {
      residueCleared: true,
      pipeFlushed: true,
      photoCount: 2,
      confirmedAt: toLocalInput(new Date().toISOString()),
      confirmerName: '',
    };
  }

  async function submitConfirm() {
    error = '';
    okMsg = '';
    try {
      const body = {
        residueCleared: cfForm.residueCleared,
        pipeFlushed: cfForm.pipeFlushed,
        photoCount: Number(cfForm.photoCount),
        confirmedAt: fromLocalInput(cfForm.confirmedAt),
        confirmerName: cfForm.confirmerName.trim(),
      };
      await api(`/vats/${confirmingVatId}/clean-confirms`, {
        method: 'POST',
        body: JSON.stringify(body),
      });
      confirmingVatId = null;
      okMsg = '清缸确认单已提交';
      await load();
    } catch (e) {
      error = e.message;
    }
  }

  async function drain(id) {
    error = '';
    okMsg = '';
    try {
      await api(`/vats/${id}/drain`, { method: 'POST' });
      okMsg = '染缸已排液';
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

  function confirmingVat() {
    return rows.find((v) => v.id === confirmingVatId);
  }
</script>

<h1 class="page-title">染缸</h1>
<p class="page-sub">
  状态：就绪 / 染色中 / 排液。容量单位为升。排液前必须先提交合格的清缸确认单。
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
  {#if okMsg}<p class="ok-msg">{okMsg}</p>{/if}
</div>

{#if confirmingVat()}
  {@const v = confirmingVat()}
  <div class="panel confirm-panel">
    <h2 class="confirm-title">清缸确认单 · {v.vatCode}（{houseName(v.dyeHouseId)}）</h2>
    <p class="confirm-note">
      排液前填写。勾「残渣已清」表示缸内染料残渣已清理干净；勾「管路已冲」表示进出液管路已冲洗到位；
      两项都必须勾是，并上传至少 2 张现场照片，否则不能提交、排液不予放行。同缸历史确认保留，以最新一张为准。
    </p>
    <div class="confirm-grid">
      <label class="check">
        <input type="checkbox" bind:checked={cfForm.residueCleared} />
        <span>残渣已清</span>
      </label>
      <label class="check">
        <input type="checkbox" bind:checked={cfForm.pipeFlushed} />
        <span>管路已冲</span>
      </label>
      <label>照片张数 <input type="number" min="0" step="1" bind:value={cfForm.photoCount} /></label>
      <label
        >确认时刻
        <input type="datetime-local" bind:value={cfForm.confirmedAt} />
      </label>
      <label>确认人 <input bind:value={cfForm.confirmerName} placeholder="姓名" /></label>
    </div>
    <div class="toolbar">
      <button class="btn" type="button" on:click={submitConfirm}>提交确认单</button>
      <button class="btn ghost" type="button" on:click={() => (confirmingVatId = null)}>取消</button>
    </div>
  </div>
{/if}

<div class="panel">
  <p class="recon">
    看板对账：染程中且尚无合格确认的缸数为
    <strong>{pendingVats.length}</strong> 手（与看板「待清缸确认」一致）。
  </p>
  <table>
    <thead>
      <tr>
        <th>ID</th>
        <th>染坊</th>
        <th>缸号</th>
        <th>纤维</th>
        <th>容量 L</th>
        <th>状态</th>
        <th>清缸确认</th>
        <th></th>
      </tr>
    </thead>
    <tbody>
      {#each rows as row}
        {@const latest = latestByVat[row.id]}
        <tr>
          <td>{row.id}</td>
          <td>{houseName(row.dyeHouseId)}</td>
          <td>{row.vatCode}</td>
          <td>{row.fiberType}</td>
          <td>{row.capacityL}</td>
          <td><span class="badge {row.status}">{VAT_STATUS[row.status] || row.status}</span></td>
          <td>
            {#if !latest}
              <span class="badge no">未确认</span>
            {:else if latest.qualified}
              <span class="badge ok">合格</span>
            {:else}
              <span class="badge no">不合格</span>
            {/if}
            {#if latest}
              <div class="confirm-meta">
                {latest.confirmerName} · {new Date(latest.confirmedAt).toLocaleString()} · 照片
                {latest.photoCount}
              </div>
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
  .confirm-panel {
    margin-bottom: 1rem;
    border-color: rgba(107, 92, 231, 0.55);
  }

  .confirm-title {
    font-family: var(--font-display);
    font-size: 1.1rem;
    margin: 0 0 0.5rem;
    letter-spacing: 0.04em;
  }

  .confirm-note {
    color: var(--indigo-mist);
    font-size: 0.82rem;
    margin: 0 0 0.9rem;
    line-height: 1.6;
  }

  .confirm-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
    gap: 0.75rem;
    margin-bottom: 0.9rem;
    align-items: end;
  }

  label.check {
    flex-direction: row;
    align-items: center;
    gap: 0.5rem;
    color: var(--foam);
  }

  label.check input {
    width: 1.05rem;
    height: 1.05rem;
  }

  .confirm-meta {
    margin-top: 0.3rem;
    font-size: 0.72rem;
    color: var(--indigo-mist);
  }

  .badge.ok {
    color: var(--ok);
    border-color: rgba(76, 175, 130, 0.55);
    background: rgba(76, 175, 130, 0.12);
  }

  .badge.no {
    color: var(--danger);
    border-color: rgba(212, 101, 122, 0.5);
  }

  .recon {
    margin: 0 0 0.85rem;
    font-size: 0.85rem;
    color: var(--indigo-mist);
  }

  .recon strong {
    color: var(--foam);
  }
</style>
