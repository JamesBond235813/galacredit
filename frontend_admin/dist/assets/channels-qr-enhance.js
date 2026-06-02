(function () {
  const SCRIPT_ID = 'channels-qr-enhance-style';
  const MODAL_ID = 'channels-qr-modal';
  const QR_MODULE_URL = '/assets/channelQr-D3drrmT3.js';
  const LOGO_URL = '/favicon.svg';
  const ADMIN_API_BASE = 'https://xhb.juxin.pro/api';
  let channelLinkCache = null;
  let channelLinkCacheAt = 0;

  const ensureStyle = () => {
    if (document.getElementById(SCRIPT_ID)) {
      return;
    }
    const style = document.createElement('style');
    style.id = SCRIPT_ID;
    style.textContent = `
      .channel-qr-button {
        border: 0;
        background: transparent;
        color: #409eff;
        cursor: pointer;
        font: inherit;
        padding: 0;
      }
      .channel-qr-modal-mask {
        position: fixed;
        inset: 0;
        z-index: 3000;
        display: flex;
        align-items: center;
        justify-content: center;
        background: rgba(16, 24, 40, 0.32);
      }
      .channel-qr-modal {
        width: 360px;
        border-radius: 18px;
        background: #ffffff;
        box-shadow: 0 24px 60px rgba(15, 35, 65, 0.22);
        padding: 24px;
      }
      .channel-qr-brand {
        display: flex;
        align-items: baseline;
        justify-content: center;
        gap: 8px;
        color: #1d2f49;
        margin-bottom: 16px;
      }
      .channel-qr-brand strong {
        font-size: 20px;
      }
      .channel-qr-brand span {
        color: #7f8da2;
        font-size: 14px;
      }
      .channel-qr-canvas-wrap {
        display: flex;
        justify-content: center;
        position: relative;
        padding: 18px;
        border: 1px solid #e8eef7;
        border-radius: 12px;
        background: linear-gradient(180deg, #ffffff 0%, #f8fbff 100%);
      }
      .channel-qr-logo {
        position: absolute;
        top: 50%;
        left: 50%;
        width: 54px;
        height: 54px;
        padding: 6px;
        border-radius: 14px;
        background: #ffffff;
        box-shadow: 0 8px 22px rgba(18, 46, 86, 0.14);
        transform: translate(-50%, -50%);
      }
      .channel-qr-actions {
        display: flex;
        justify-content: flex-end;
        gap: 10px;
        margin-top: 18px;
      }
      .channel-qr-actions button {
        min-width: 72px;
        border: 1px solid #d9e4f2;
        border-radius: 8px;
        background: #ffffff;
        color: #26405f;
        cursor: pointer;
        padding: 8px 14px;
      }
      .channel-qr-actions .primary {
        border-color: #2f74ff;
        background: #2f74ff;
        color: #ffffff;
      }
    `;
    document.head.appendChild(style);
  };

  const isChannelsRoute = () => window.location.pathname === '/channels';

  const findHeaderCellIndex = (cells, keyword) => cells.findIndex((cell) => cell.textContent.trim().includes(keyword));

  const getAdminToken = () => localStorage.getItem('admin_token') || '';

  const trimSlash = (value) => String(value || '').trim().replace(/\/+$/, '');

  const buildChannelLink = (prefix, code) => `${trimSlash(prefix)}/${String(code || '').replace(/^\/+/, '')}`;

  const fetchChannelLinkMap = async () => {
    const now = Date.now();
    if (channelLinkCache && now - channelLinkCacheAt < 30000) {
      return channelLinkCache;
    }

    const token = getAdminToken();
    if (!token) {
      return { links: new Map(), prefix: 'https://xhb.juxin.pro' };
    }

    const headers = { Authorization: `Bearer ${token}` };
    const firstResponse = await fetch(`${ADMIN_API_BASE}/admin/channels?status=ALL&skip=0&limit=100`, { headers });
    if (!firstResponse.ok) {
      return { links: new Map(), prefix: 'https://xhb.juxin.pro' };
    }
    const firstPayload = await firstResponse.json();
    const payloadData = firstPayload && firstPayload.data ? firstPayload.data : firstPayload;
    const total = Number(payloadData.total || 0);
    const items = Array.isArray(payloadData.items) ? [...payloadData.items] : [];
    const prefix = payloadData.channel_link_prefix || 'https://xhb.juxin.pro';

    for (let skip = 100; skip < total; skip += 100) {
      const response = await fetch(`${ADMIN_API_BASE}/admin/channels?status=ALL&skip=${skip}&limit=100`, { headers });
      if (!response.ok) {
        break;
      }
      const payload = await response.json();
      const data = payload && payload.data ? payload.data : payload;
      if (Array.isArray(data.items)) {
        items.push(...data.items);
      }
    }

    const links = new Map();
    items.forEach((item) => {
      const inviteCode = String(item.invite_code || '').trim();
      const dailyInviteCode = String(item.daily_invite_code || inviteCode).trim();
      if (inviteCode && dailyInviteCode) {
        links.set(inviteCode, buildChannelLink(prefix, dailyInviteCode));
      }
    });

    channelLinkCache = { links, prefix };
    channelLinkCacheAt = now;
    return channelLinkCache;
  };

  const extractInviteCode = (link) => {
    const value = String(link || '').trim();
    return value.split('/').filter(Boolean).pop() || '';
  };

  const resolveDailyLink = async (link) => {
    const inviteCode = extractInviteCode(link);
    const { links } = await fetchChannelLinkMap();
    return links.get(inviteCode) || link;
  };

  const createHeaderCell = (baseCell) => {
    const cell = document.createElement('th');
    cell.className = baseCell.className;
    cell.setAttribute('colspan', '1');
    cell.setAttribute('rowspan', '1');
    cell.innerHTML = '<div class="cell">二维码</div>';
    return cell;
  };

  const createBodyCell = (baseCell, link, active) => {
    const cell = document.createElement('td');
    cell.className = baseCell.className;
    cell.innerHTML = active
      ? '<div class="cell"><button type="button" class="channel-qr-button">查看</button></div>'
      : '<div class="cell">--</div>';
    if (active) {
      cell.querySelector('button').addEventListener('click', () => showQrModal(link));
    }
    return cell;
  };

  const getRowLink = (row, linkIndex) => {
    const linkCell = row.children[linkIndex];
    const linkNode = linkCell && linkCell.querySelector('.link-cell');
    return linkNode ? linkNode.textContent.trim() : '';
  };

  const copyText = async (text) => {
    try {
      await navigator.clipboard.writeText(text);
    } catch (error) {
      const input = document.createElement('textarea');
      input.value = text;
      document.body.appendChild(input);
      input.select();
      document.execCommand('copy');
      input.remove();
    }
  };

  const copyDailyLink = async (link) => {
    const dailyLink = await resolveDailyLink(link);
    await copyText(dailyLink);
  };

  const closeQrModal = () => {
    const existed = document.getElementById(MODAL_ID);
    if (existed) {
      existed.remove();
    }
  };

  const showQrModal = async (link) => {
    closeQrModal();
    ensureStyle();
    const dailyLink = await resolveDailyLink(link);

    const mask = document.createElement('div');
    mask.id = MODAL_ID;
    mask.className = 'channel-qr-modal-mask';
    mask.innerHTML = `
      <div class="channel-qr-modal" role="dialog" aria-modal="true">
        <div class="channel-qr-brand"><strong>小荷包</strong><span>解生活之所急</span></div>
        <div class="channel-qr-canvas-wrap">
          <canvas width="260" height="260" aria-label="专属链接二维码"></canvas>
          <img src="${LOGO_URL}" class="channel-qr-logo" alt="小荷包 logo" />
        </div>
        <div class="channel-qr-actions">
          <button type="button" data-action="copy">复制链接</button>
          <button type="button" class="primary" data-action="close">关闭</button>
        </div>
      </div>
    `;
    mask.addEventListener('click', (event) => {
      if (event.target === mask || event.target.dataset.action === 'close') {
        closeQrModal();
      }
      if (event.target.dataset.action === 'copy') {
        copyText(dailyLink);
      }
    });
    document.body.appendChild(mask);

    try {
      const module = await import(QR_MODULE_URL);
      await module.t(mask.querySelector('canvas'), dailyLink);
    } catch (error) {
      mask.querySelector('.channel-qr-canvas-wrap').textContent = '二维码生成失败，请复制链接使用。';
    }
  };

  const enhanceTable = (table) => {
    const headerRow = table.querySelector('.el-table__header-wrapper thead tr');
    const bodyRows = Array.from(table.querySelectorAll('.el-table__body-wrapper tbody tr'));
    if (!headerRow || bodyRows.length === 0) {
      return;
    }

    let headerCells = Array.from(headerRow.children);
    const linkIndex = findHeaderCellIndex(headerCells, '专属链接');
    let statusIndex = findHeaderCellIndex(headerCells, '状态');
    let qrIndex = findHeaderCellIndex(headerCells, '二维码');
    if (linkIndex < 0 || statusIndex < 0) {
      return;
    }

    if (qrIndex < 0) {
      headerRow.insertBefore(createHeaderCell(headerCells[statusIndex]), headerCells[statusIndex]);
      headerCells = Array.from(headerRow.children);
      qrIndex = findHeaderCellIndex(headerCells, '二维码');
      statusIndex = findHeaderCellIndex(headerCells, '状态');
    }

    bodyRows.forEach((row) => {
      const cells = Array.from(row.children);
      const rowAlreadyHasQr = cells.length === headerCells.length;
      const bodyQrIndex = rowAlreadyHasQr ? qrIndex : -1;
      const bodyStatusIndex = rowAlreadyHasQr ? statusIndex : qrIndex;

      if (bodyQrIndex >= 0 && cells[bodyQrIndex] && cells[bodyQrIndex].textContent.trim().includes('查看')) {
        return;
      }
      if (bodyQrIndex >= 0 && cells[bodyQrIndex] && cells[bodyQrIndex].textContent.trim() === '--') {
        return;
      }

      const link = getRowLink(row, linkIndex);
      const statusCell = cells[bodyStatusIndex];
      const active = statusCell && statusCell.textContent.includes('启用中') && Boolean(link);
      const copyButton = cells[linkIndex] && cells[linkIndex].querySelector('button');
      if (copyButton && !copyButton.dataset.channelQrEnhanced) {
        copyButton.dataset.channelQrEnhanced = '1';
        copyButton.addEventListener('click', (event) => {
          event.preventDefault();
          event.stopImmediatePropagation();
          copyDailyLink(link);
        }, true);
      }
      row.insertBefore(createBodyCell(statusCell, link, active), statusCell);
    });
  };

  const refreshVisibleDailyLinks = async () => {
    if (!isChannelsRoute()) {
      return;
    }
    const { links } = await fetchChannelLinkMap();
    if (!links.size) {
      return;
    }
    document.querySelectorAll('.link-cell').forEach((node) => {
      const inviteCode = extractInviteCode(node.textContent);
      const dailyLink = links.get(inviteCode);
      if (dailyLink) {
        node.textContent = dailyLink;
      }
    });
  };

  const enhance = () => {
    if (!isChannelsRoute()) {
      return;
    }
    ensureStyle();
    document.querySelectorAll('.el-table').forEach(enhanceTable);
    refreshVisibleDailyLinks();
  };

  let enhanceTimer = null;
  const scheduleEnhance = () => {
    window.clearTimeout(enhanceTimer);
    enhanceTimer = window.setTimeout(enhance, 120);
  };

  window.addEventListener('popstate', scheduleEnhance);
  window.addEventListener('hashchange', scheduleEnhance);
  document.addEventListener('DOMContentLoaded', scheduleEnhance);
  new MutationObserver(scheduleEnhance).observe(document.documentElement, {
    childList: true,
    subtree: true
  });
  scheduleEnhance();
})();
