(function () {
  const ROUTE_RE = /\/ecard-pool(?:\/|$)/;
  const PAGE_SIZE = 100;
  const MAX_PAGES = 30;
  let cache = { stats: null, itemsById: new Map(), total: 0, loadedPages: 0 };
  let loading = null;
  let timer = null;

  function isEcardPoolPage() {
    return ROUTE_RE.test(window.location.pathname || "");
  }

  function getToken() {
    return window.localStorage ? window.localStorage.getItem("admin_token") : "";
  }

  function normalizeResponse(payload) {
    return payload && payload.data && Array.isArray(payload.data.items) ? payload.data : payload;
  }

  async function fetchPoolPage(skip) {
    const token = getToken();
    if (!token) return null;
    const query = new URLSearchParams({ status: "ALL", skip: String(skip), limit: String(PAGE_SIZE) });
    const response = await fetch(`/api/admin/ecard-pool?${query.toString()}`, {
      headers: { Authorization: `Bearer ${token}` },
      credentials: "same-origin",
      cache: "no-store",
    });
    if (!response.ok) return null;
    return normalizeResponse(await response.json());
  }

  function mergeItems(data) {
    if (!data) return;
    cache.stats = data.stats || cache.stats;
    cache.total = Number(data.total || cache.total || 0);
    (data.items || []).forEach((item) => {
      if (item && item.id != null) cache.itemsById.set(String(item.id), item);
    });
  }

  function getVisibleIds() {
    return getBodyRows()
      .map((row) => {
        const firstCell = row.querySelector("td:not(.xhb-ecard-extra-cell) .cell");
        return firstCell ? firstCell.textContent.trim() : "";
      })
      .filter(Boolean);
  }

  async function ensureDataForVisibleRows() {
    if (loading) return loading;
    loading = (async () => {
      const visibleIds = getVisibleIds();
      if (!cache.loadedPages) {
        mergeItems(await fetchPoolPage(0));
        cache.loadedPages = 1;
      }
      for (let page = cache.loadedPages; page < MAX_PAGES; page += 1) {
        const missing = visibleIds.filter((id) => !cache.itemsById.has(id));
        if (!missing.length) break;
        if (cache.total && page * PAGE_SIZE >= cache.total) break;
        mergeItems(await fetchPoolPage(page * PAGE_SIZE));
        cache.loadedPages = page + 1;
      }
    })().finally(() => {
      loading = null;
    });
    return loading;
  }

  function formatMoney(value) {
    const amount = Number(value || 0);
    return `￥${amount.toLocaleString("zh-CN", { minimumFractionDigits: amount % 1 === 0 ? 0 : 2, maximumFractionDigits: 2 })}`;
  }

  function formatDateTime(value) {
    if (!value) return "--";
    const date = new Date(value);
    return Number.isNaN(date.getTime()) ? "--" : date.toLocaleString("zh-CN", { hour12: false });
  }

  function valueText(item, col) {
    if (!item) return "--";
    return col.type === "datetime" ? formatDateTime(item[col.key]) : item[col.key] || "--";
  }

  function getCellText(cell) {
    return (cell && cell.textContent ? cell.textContent : "").trim();
  }

  function renderStats() {
    const page = document.querySelector(".admin-page");
    const filterCard = document.querySelector(".admin-page .filter-card");
    if (!page || !filterCard) return;
    let panel = document.querySelector(".xhb-ecard-stats");
    if (!panel) {
      panel = document.createElement("section");
      panel.className = "xhb-ecard-stats";
    }
    if (panel.nextElementSibling !== filterCard) filterCard.insertAdjacentElement("beforebegin", panel);
    const stats = cache.stats || {};
    const cards = [
      ["累计发放", stats.cumulative_assigned_count, stats.cumulative_assigned_amount],
      ["在库可用", stats.available_count, stats.available_amount],
      ["今日入库", stats.today_stock_in_count, stats.today_stock_in_amount],
      ["今日发卡", stats.today_assigned_count, stats.today_assigned_amount],
    ];
    const html = cards
      .map(([title, count, amount]) => `<div class="xhb-ecard-stat-card"><span>${title}</span><strong>${Number(count || 0).toLocaleString("zh-CN")} 张</strong><p>总金额 ${formatMoney(amount)}</p></div>`)
      .join("");
    if (panel.innerHTML !== html) panel.innerHTML = html;
  }

  function getTable() {
    const tables = Array.from(document.querySelectorAll(".admin-page .el-table"));
    return tables.find((table) => table.querySelector(".el-table__header-wrapper") && table.querySelector(".el-table__body-wrapper"));
  }

  function getBodyRows() {
    const table = getTable();
    if (!table) return [];
    return Array.from(table.querySelectorAll(".el-table__body-wrapper tbody tr.el-table__row"));
  }

  function getColumnIndex(label, fallbackClass) {
    const table = getTable();
    const row = table && table.querySelector(".el-table__header-wrapper thead tr");
    const cells = row ? Array.from(row.children) : [];
    return cells.findIndex((cell) => getCellText(cell) === label || (fallbackClass && cell.classList.contains(fallbackClass)));
  }

  function cleanupInsertedColumns() {
    const table = getTable();
    if (!table) return;
    table.querySelectorAll(".xhb-ecard-extra-head,.xhb-ecard-extra-cell").forEach((node) => node.remove());
  }

  function renderHeader() {
    const table = getTable();
    const row = table && table.querySelector(".el-table__header-wrapper thead tr");
    if (!row) return;
    const phoneIndex = getColumnIndex("绑定订单", "xhb-ecard-phone-head");
    const timeIndex = getColumnIndex("备注", "xhb-ecard-time-head");
    const phoneHead = row.children[phoneIndex];
    const timeHead = row.children[timeIndex];
    if (phoneHead) {
      phoneHead.classList.add("xhb-ecard-phone-head");
      const inner = phoneHead.querySelector(".cell");
      if (inner) inner.textContent = "领取人手机号";
    }
    if (timeHead) {
      timeHead.classList.add("xhb-ecard-time-head");
      const inner = timeHead.querySelector(".cell");
      if (inner) inner.textContent = "发放/拷贝密码时间";
    }
  }

  function renderRows() {
    const phoneIndex = getColumnIndex("领取人手机号", "xhb-ecard-phone-head");
    const timeIndex = getColumnIndex("发放/拷贝密码时间", "xhb-ecard-time-head");
    getBodyRows().forEach((row) => {
      const idCell = row.querySelector("td:not(.xhb-ecard-extra-cell) .cell");
      const id = idCell ? idCell.textContent.trim() : "";
      const item = cache.itemsById.get(id);
      const phoneCell = row.children[phoneIndex];
      const timeCell = row.children[timeIndex];
      if (phoneCell) {
        phoneCell.classList.add("xhb-ecard-phone-cell");
        const inner = phoneCell.querySelector(".cell");
        if (inner) inner.textContent = valueText(item, { key: "recipient_phone" });
      }
      if (timeCell) {
        timeCell.classList.add("xhb-ecard-time-cell");
        const inner = timeCell.querySelector(".cell");
        if (inner) {
          inner.innerHTML = `<div>发放：${valueText(item, { key: "assigned_at", type: "datetime" })}</div><div>拷贝密码：${valueText(item, { key: "secret_copied_at", type: "datetime" })}</div>`;
        }
      }
    });
  }

  async function enhance() {
    if (!isEcardPoolPage()) return;
    await ensureDataForVisibleRows();
    renderStats();
    cleanupInsertedColumns();
    renderHeader();
    renderRows();
  }

  function schedule() {
    window.clearTimeout(timer);
    timer = window.setTimeout(enhance, 250);
  }

  function hookHistory(name) {
    const original = window.history[name];
    window.history[name] = function () {
      const result = original.apply(this, arguments);
      schedule();
      return result;
    };
  }

  hookHistory("pushState");
  hookHistory("replaceState");
  window.addEventListener("popstate", schedule);
  window.addEventListener("load", schedule);
  new MutationObserver(schedule).observe(document.documentElement, { childList: true, subtree: true });
  schedule();
})();
