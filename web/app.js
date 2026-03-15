const ASSETS = {
  sp500: {
    id: "sp500",
    name: "标普500",
    english: "S&P 500",
    short: "SPX",
    color: "#1e5eff",
    softColor: "rgba(30, 94, 255, 0.14)",
    priceSource: "./data/sp500.csv",
    totalReturnSource: "./data/sp500-total-return.csv",
    priceLabel: "Stooq ^SPX 本地日线",
    totalReturnLabel: "Yahoo Finance ^SP500TR 本地化",
    totalReturnSymbol: "SPXT",
    currency: "USD",
    fxPair: null,
  },
  nasdaq100: {
    id: "nasdaq100",
    name: "纳斯达克100",
    english: "Nasdaq-100",
    short: "NDX",
    color: "#0da38d",
    softColor: "rgba(13, 163, 141, 0.14)",
    priceSource: "./data/nasdaq100.csv",
    totalReturnSource: "./data/nasdaq100-total-return.csv",
    priceLabel: "Stooq ^NDX 本地日线",
    totalReturnLabel: "Nasdaq 官方 XNDX 本地化",
    totalReturnSymbol: "XNDX",
    currency: "USD",
    fxPair: null,
  },
  hs300: {
    id: "hs300",
    name: "沪深300",
    english: "CSI 300",
    short: "CSI300",
    color: "#c9651a",
    softColor: "rgba(201, 101, 26, 0.14)",
    priceSource: "./data/hs300.csv",
    totalReturnSource: "./data/hs300-total-return.csv",
    priceLabel: "东方财富沪深300本地日线",
    totalReturnLabel: "中证指数官方 H00300 本地化",
    totalReturnSymbol: "H00300",
    currency: "CNY",
    fxPair: "usdcny",
  },
  nikkei225: {
    id: "nikkei225",
    name: "日经225",
    english: "Nikkei 225",
    short: "N225",
    color: "#8a5b19",
    softColor: "rgba(138, 91, 25, 0.14)",
    priceSource: "./data/nikkei225.csv",
    totalReturnSource: "./data/nikkei225-total-return.csv",
    priceLabel: "日经官方历史页本地化",
    totalReturnLabel: "日经官方日频+月频+月报锚点+早期回算本地化",
    totalReturnSymbol: "NK225TR",
    currency: "JPY",
    fxPair: "usdjpy",
    totalReturnCoverageStart: "1979-12-28",
    totalReturnInferredUntil: "2012-12-02",
    totalReturnHybridUntil: "2023-01-03",
  },
};

const FX_SERIES = {
  usdcny: {
    id: "usdcny",
    label: "USD/CNY",
    source: "./data/usdcny.csv",
    sourceLabel: "FRED DEXCHUS（人民币/美元）本地化",
  },
  usdjpy: {
    id: "usdjpy",
    label: "USD/JPY",
    source: "./data/usdjpy.csv",
    sourceLabel: "FRED DEXJPUS（日元/美元）本地化",
  },
};

const DEFAULTS = {
  selectedAssets: ["sp500", "nasdaq100"],
  returnMode: "total",
  frequency: "monthly",
  sampling: "weekly",
  amount: 500,
  preset: "20",
};

const DATA_CACHE_BUSTER = "20260316-v36";

const DRAWDOWN_CAUSE_RULES = [
  { start: "1987-08-01", end: "1987-12-31", label: "黑色星期一、程序化交易放大抛压与高估值回吐" },
  { start: "1990-07-01", end: "1991-03-31", label: "海湾战争推升油价、美国衰退担忧与风险资产回撤" },
  { start: "1997-07-01", end: "1998-10-31", label: "亚洲金融危机、俄罗斯违约与 LTCM 危机冲击全球风险偏好" },
  { start: "2000-03-01", end: "2002-10-31", label: "互联网泡沫破裂、盈利下修、美国衰退与 9·11 冲击" },
  { start: "2007-07-01", end: "2009-06-30", label: "次贷链条断裂、雷曼倒闭、信用市场冻结与全球金融危机" },
  { start: "2010-04-01", end: "2010-07-31", label: "希腊债务危机升级、欧洲银行压力与美国闪电崩盘扰动" },
  { start: "2011-07-01", end: "2011-12-31", label: "欧债危机恶化、美国主权评级下调与全球增长担忧" },
  { start: "2015-08-01", end: "2016-02-29", label: "中国汇改与增长担忧升温、原油暴跌、美联储首次加息" },
  { start: "2018-10-01", end: "2018-12-31", label: "美联储继续加息缩表、中美贸易摩擦升级与盈利预期下修" },
  { start: "2020-02-01", end: "2020-05-31", label: "疫情全球大流行、封锁冲击增长，叠加流动性挤兑" },
  { start: "2022-01-01", end: "2022-12-31", label: "俄乌战争推升能源与通胀，美联储激进加息压缩估值" },
  { start: "2023-03-01", end: "2023-05-31", label: "SVB、Signature 与 First Republic 风波触发银行体系与信用收缩担忧" },
  { start: "2024-07-01", end: "2024-08-31", label: "美国增长放缓恐慌、日银加息引发套息交易逆转，拥挤交易回吐" },
  { start: "2024-09-01", end: "2025-02-12", label: "长端利率上行、增长与盈利预期反复，关税预期开始扰动风险偏好" },
  {
    start: "2025-02-13",
    end: "2025-04-30",
    label: "对等关税预期升温，4 月 2 日对等关税落地并引发反制，贸易战与衰退担忧升温",
  },
  { start: "2025-05-01", end: "2026-12-31", label: "关税谈判反复、财政与长端利率扰动、增长前景摇摆" },
  {
    assets: ["hs300"],
    start: "2007-10-01",
    end: "2008-11-30",
    label: "A 股泡沫破裂、大小非减持压力抬升，叠加全球金融危机冲击",
  },
  {
    assets: ["hs300"],
    start: "2009-08-01",
    end: "2010-07-31",
    label: "刺激退坡、地产调控收紧与银行再融资压力压制权重股",
  },
  {
    assets: ["hs300"],
    start: "2011-04-01",
    end: "2012-12-31",
    label: "紧缩后增长放缓、欧债危机拖累外需，周期与金融板块承压",
  },
  {
    assets: ["hs300"],
    start: "2015-06-01",
    end: "2016-02-29",
    label: "场内外配资去杠杆、股灾救市反复、人民币贬值与熔断冲击",
  },
  {
    assets: ["hs300"],
    start: "2018-01-01",
    end: "2019-01-31",
    label: "金融去杠杆、民企信用收缩与中美贸易摩擦压制风险偏好",
  },
  {
    assets: ["hs300"],
    start: "2021-02-01",
    end: "2022-11-30",
    label: "平台监管、房地产去杠杆、疫情封控与内需偏弱拖累核心资产",
  },
  {
    assets: ["hs300"],
    start: "2023-01-01",
    end: "2024-02-29",
    label: "地产链下行、通缩预期与外资流出，政策预期屡次落空",
  },
  {
    assets: ["hs300"],
    start: "2024-10-01",
    end: "2025-02-28",
    label: "政策博弈加剧，地产与内需修复偏慢，盈利预期仍弱",
  },
  {
    assets: ["nikkei225"],
    start: "1990-01-01",
    end: "1992-08-31",
    label: "日银紧缩刺破资产泡沫，地产与银行不良贷款问题集中暴露",
  },
  {
    assets: ["nikkei225"],
    start: "1997-07-01",
    end: "1998-10-31",
    label: "亚洲金融危机、日本银行业危机与山一证券等机构倒闭",
  },
  {
    assets: ["nikkei225"],
    start: "2000-04-01",
    end: "2003-04-30",
    label: "全球科技泡沫破裂、日本通缩延续与银行不良资产出清",
  },
  {
    assets: ["nikkei225"],
    start: "2008-09-01",
    end: "2009-03-31",
    label: "雷曼危机、全球贸易塌陷与日元急升重创出口板块",
  },
  {
    assets: ["nikkei225"],
    start: "2011-03-01",
    end: "2011-05-31",
    label: "东日本大地震、核事故与供应链中断打击日本风险资产",
  },
  {
    assets: ["nikkei225"],
    start: "2024-07-01",
    end: "2024-08-31",
    label: "日银退出超宽松并加息、日元套利交易逆转，叠加美国衰退恐慌",
  },
];

const formatters = {
  currency: new Intl.NumberFormat("en-US", {
    style: "currency",
    currency: "USD",
    maximumFractionDigits: 0,
  }),
  currencyOne: new Intl.NumberFormat("en-US", {
    style: "currency",
    currency: "USD",
    minimumFractionDigits: 1,
    maximumFractionDigits: 1,
  }),
  compactCurrency: new Intl.NumberFormat("en-US", {
    style: "currency",
    currency: "USD",
    notation: "compact",
    maximumFractionDigits: 1,
  }),
  integer: new Intl.NumberFormat("en-US", { maximumFractionDigits: 0 }),
};

const state = {
  data: {},
  fx: {},
  refreshMeta: null,
  refreshPollTimer: null,
  ui: { ...DEFAULTS },
  run: null,
  chartObserver: null,
  chartWindow: { startRatio: 0, endRatio: 1 },
  chartRenderFrame: null,
};

const dom = {};

document.addEventListener("DOMContentLoaded", () => {
  void init();
});

async function init() {
  cacheDom();
  bindEvents();
  applyInitialUiState();
  setStatus("加载数据中", "正在读取价格指数与全收益序列。");

  try {
    await loadAllData();
    renderFeedCards();
    ensureDateWithinAvailableRange();
    rerunBacktest();
    installChartResizeObserver();
  } catch (error) {
    console.error(error);
    setStatus("数据加载失败", "本地数据文件读取异常，请检查 web/data 目录和控制台信息。");
    dom.dataNotice.hidden = false;
    dom.dataNotice.textContent = "未能完成数据加载，页面暂时无法生成回测结果。";
    dom.chartEmpty.hidden = false;
    dom.chartEmpty.textContent = "数据加载失败，请检查本地文件后刷新。";
  }
}

function cacheDom() {
  dom.assetInputs = Array.from(document.querySelectorAll("input[data-asset-id]"));
  dom.startDate = document.querySelector("#start-date");
  dom.amountInput = document.querySelector("#amount-input");
  dom.runButton = document.querySelector("#run-backtest");
  dom.dateRangeHint = document.querySelector("#date-range-hint");
  dom.dataNotice = document.querySelector("#data-notice");
  dom.statusTitle = document.querySelector("#status-title");
  dom.statusText = document.querySelector("#status-text");
  dom.feedCards = document.querySelector("#feed-cards");
  dom.heroStrategy = document.querySelector("#hero-strategy");
  dom.heroLatestDate = document.querySelector("#hero-latest-date");
  dom.effectiveModeChip = document.querySelector("#effective-mode-chip");
  dom.chartCaption = document.querySelector("#chart-caption");
  dom.chartLegend = document.querySelector("#chart-legend");
  dom.detailGrid = document.querySelector("#detail-grid");
  dom.resultsGrid = document.querySelector("#results-grid");
  dom.chartPanel = document.querySelector("#chart-panel");
  dom.overviewCards = document.querySelector("#overview-cards");
  dom.chartShell = document.querySelector("#chart-shell");
  dom.chartSurface = document.querySelector("#chart-surface");
  dom.chartTooltip = document.querySelector("#chart-tooltip");
  dom.timelineStart = document.querySelector("#timeline-start");
  dom.timelineEnd = document.querySelector("#timeline-end");
  dom.timelineRangeFill = document.querySelector("#timeline-range-fill");
  dom.visibleRangeLabel = document.querySelector("#visible-range-label");
  dom.resetVisibleRange = document.querySelector("#reset-visible-range");
  dom.timelineZoom = document.querySelector("#timeline-zoom");
  dom.chartSummary = document.querySelector("#chart-summary");
  dom.chartEmpty = document.querySelector("#chart-empty");
  dom.resultContext = document.querySelector("#result-context");
  dom.insightPanel = document.querySelector("#insight-panel");
  dom.assetMetrics = document.querySelector("#asset-metrics");
  dom.sourceNotes = document.querySelector("#source-notes");
  dom.scheduleSummary = document.querySelector("#schedule-summary");
  dom.drawdownEvents = document.querySelector("#drawdown-events");
  dom.returnSegments = document.querySelectorAll('[data-group="return-mode"] .segment');
  dom.frequencySegments = document.querySelectorAll('[data-group="frequency"] .segment');
  dom.presetButtons = document.querySelectorAll(".preset-button");
  dom.quickAmountButtons = document.querySelectorAll(".quick-amount");
}

function bindEvents() {
  for (const input of dom.assetInputs) {
    input.addEventListener("change", (event) => handleAssetToggle(event, input.dataset.assetId));
  }

  for (const button of dom.returnSegments) {
    button.addEventListener("click", () => {
      state.ui.returnMode = button.dataset.value;
      setActiveButtons(dom.returnSegments, state.ui.returnMode);
      rerunBacktest();
    });
  }

  for (const button of dom.frequencySegments) {
    button.addEventListener("click", () => {
      state.ui.frequency = button.dataset.value;
      setActiveButtons(dom.frequencySegments, state.ui.frequency);
      rerunBacktest();
    });
  }

  for (const button of dom.presetButtons) {
    button.addEventListener("click", () => {
      state.ui.preset = button.dataset.preset;
      setActivePreset(state.ui.preset);
      rerunBacktest();
    });
  }

  dom.startDate.addEventListener("change", () => {
    state.ui.preset = null;
    setActivePreset(null);
    rerunBacktest();
  });

  dom.amountInput.addEventListener("change", () => {
    const parsed = Number(dom.amountInput.value);
    state.ui.amount = Number.isFinite(parsed) && parsed > 0 ? parsed : DEFAULTS.amount;
    dom.amountInput.value = String(Math.round(state.ui.amount));
    syncQuickAmounts();
    rerunBacktest();
  });

  for (const button of dom.quickAmountButtons) {
    button.addEventListener("click", () => {
      state.ui.amount = Number(button.dataset.amount);
      dom.amountInput.value = String(state.ui.amount);
      syncQuickAmounts();
      rerunBacktest();
    });
  }

  dom.runButton.addEventListener("click", () => rerunBacktest());
  dom.timelineStart.addEventListener("input", () => handleTimelineRangeInput("start"));
  dom.timelineEnd.addEventListener("input", () => handleTimelineRangeInput("end"));
  dom.resetVisibleRange.addEventListener("click", () => resetTimelineWindow());
}

function applyInitialUiState() {
  for (const input of dom.assetInputs) {
    input.checked = state.ui.selectedAssets.includes(input.dataset.assetId);
  }
  dom.amountInput.value = String(state.ui.amount);
  setActiveButtons(dom.returnSegments, state.ui.returnMode);
  setActiveButtons(dom.frequencySegments, state.ui.frequency);
  setActivePreset(state.ui.preset);
  syncQuickAmounts();
}

function setActiveButtons(buttons, value) {
  for (const button of buttons) {
    button.classList.toggle("is-active", button.dataset.value === value);
  }
}

function setActivePreset(value) {
  for (const button of dom.presetButtons) {
    button.classList.toggle("is-active", button.dataset.preset === value);
  }
}

function syncQuickAmounts() {
  for (const button of dom.quickAmountButtons) {
    button.classList.toggle("is-active", Number(button.dataset.amount) === Number(state.ui.amount));
  }
}

function handleAssetToggle(event, assetId) {
  const selected = new Set(getSelectedAssetsFromInputs());

  if (selected.size === 0) {
    event.target.checked = true;
    return;
  }

  if (selected.size > 4) {
    event.target.checked = false;
    return;
  }

  state.ui.selectedAssets = Array.from(selected);
  rerunBacktest();
}

function getSelectedAssetsFromInputs() {
  return dom.assetInputs.filter((input) => input.checked).map((input) => input.dataset.assetId);
}

async function loadAllData() {
  const assetEntries = Object.values(ASSETS);
  const tasks = assetEntries.map(async (asset) => {
    const price = await fetchCsvSeries(asset.priceSource);
    const totalReturn = await fetchOptionalCsvSeries(asset.totalReturnSource);

    state.data[asset.id] = {
      price,
      totalReturn,
      priceMap: buildSeriesMap(price),
      totalReturnMap: buildSeriesMap(totalReturn),
    };
  });

  const fxTasks = Object.values(FX_SERIES).map(async (pair) => {
    const series = await fetchCsvSeries(pair.source);
    state.fx[pair.id] = {
      ...pair,
      series,
      map: buildSeriesMap(series),
      resolvedCache: new Map(),
    };
  });

  await Promise.all([...tasks, ...fxTasks]);
  state.refreshMeta = await loadRefreshMeta();
  scheduleRefreshStatusPolling();
}

async function fetchCsvSeries(url) {
  const response = await fetch(`${url}?v=${DATA_CACHE_BUSTER}`, { cache: "no-store" });
  if (!response.ok) {
    throw new Error(`Failed to load ${url}: ${response.status}`);
  }
  const text = await response.text();
  const series = parseCsvSeries(text);
  if (!series.length) {
    throw new Error(`Series is empty: ${url}`);
  }
  return series;
}

async function fetchOptionalCsvSeries(url) {
  try {
    const response = await fetch(`${url}?v=${DATA_CACHE_BUSTER}`, { cache: "no-store" });
    if (!response.ok) return [];
    const text = await response.text();
    return parseCsvSeries(text);
  } catch (_error) {
    return [];
  }
}

async function fetchOptionalJson(url) {
  try {
    const response = await fetch(`${url}?v=${DATA_CACHE_BUSTER}`, { cache: "no-store" });
    if (!response.ok) return null;
    return await response.json();
  } catch (_error) {
    return null;
  }
}

async function loadRefreshMeta() {
  return (await fetchOptionalJson("/api/refresh-status")) || (await fetchOptionalJson("./data/refresh-meta.json"));
}

function parseCsvSeries(text) {
  const lines = String(text).trim().split(/\r?\n/);
  if (lines.length < 2) return [];

  const header = lines[0].split(",").map((item) => item.trim().toLowerCase());
  const dateIndex = header.indexOf("date");
  const closeIndex = header.indexOf("close");
  if (dateIndex < 0 || closeIndex < 0) return [];

  const points = [];
  let skippedInvalidRows = 0;
  for (let index = 1; index < lines.length; index += 1) {
    const row = lines[index].trim();
    if (!row) continue;
    const cells = row.split(",");
    const dateKey = cells[dateIndex];
    const close = Number(cells[closeIndex]);
    if (!dateKey || !Number.isFinite(close) || close <= 0) {
      skippedInvalidRows += 1;
      continue;
    }
    const date = parseUtcDate(dateKey);
    points.push({
      dateKey,
      date,
      dateMs: date.getTime(),
      close,
    });
  }

  if (skippedInvalidRows > 0) {
    console.warn(`Skipped ${skippedInvalidRows} invalid data row(s) while parsing CSV series.`);
  }

  return points.sort((left, right) => left.dateMs - right.dateMs);
}

function buildSeriesMap(series) {
  const map = new Map();
  for (const point of series) {
    map.set(point.dateKey, point);
  }
  return map;
}

function resolveFxPointForDate(pairId, dateKey) {
  if (!pairId) {
    return { dateKey, close: 1 };
  }

  const pair = state.fx[pairId];
  if (!pair?.series?.length) {
    return null;
  }

  if (pair.resolvedCache.has(dateKey)) {
    return pair.resolvedCache.get(dateKey);
  }

  const dateMs = parseUtcDate(dateKey).getTime();
  const series = pair.series;
  let low = 0;
  let high = series.length - 1;
  let match = null;

  while (low <= high) {
    const middle = Math.floor((low + high) / 2);
    const point = series[middle];
    if (point.dateMs <= dateMs) {
      match = point;
      low = middle + 1;
    } else {
      high = middle - 1;
    }
  }

  pair.resolvedCache.set(dateKey, match);
  return match;
}

function parseUtcDate(dateKey) {
  const [year, month, day] = dateKey.split("-").map(Number);
  return new Date(Date.UTC(year, month - 1, day));
}

function rerunBacktest() {
  state.ui.selectedAssets = getSelectedAssetsFromInputs();
  state.ui.amount = Math.max(1, Number(dom.amountInput.value) || DEFAULTS.amount);

  const selectedAssets = state.ui.selectedAssets;
  const effectiveMode = resolveEffectiveMode(selectedAssets, state.ui.returnMode);
  const baseTimeline = buildAlignedTimeline(selectedAssets, effectiveMode.mode);
  const priceTimeline = buildAlignedTimeline(selectedAssets, "price");

  dom.dataNotice.hidden = true;

  if (!baseTimeline.length) {
    setStatus("无可用数据", "当前选择下没有足够的共同历史序列。");
    dom.chartEmpty.hidden = false;
    dom.chartEmpty.textContent = "当前选项下暂无可用数据。";
    dom.chartSurface.innerHTML = "";
    dom.chartLegend.innerHTML = "";
    dom.overviewCards.innerHTML = "";
    dom.chartSummary.innerHTML = "";
    if (dom.assetMetrics) dom.assetMetrics.innerHTML = "";
    if (dom.sourceNotes) dom.sourceNotes.innerHTML = "";
    dom.scheduleSummary.innerHTML = "";
    dom.drawdownEvents.innerHTML = "";
    return;
  }

  const availableRange = {
    start: baseTimeline[0].dateKey,
    end: baseTimeline[baseTimeline.length - 1].dateKey,
  };

  const startDateKey = resolveStartDateKey(baseTimeline, availableRange);
  const timeline = baseTimeline.filter((point) => point.dateKey >= startDateKey);
  const contributions = buildContributionPlan(timeline, state.ui.frequency);
  const contributionDates = contributions.map((item) => item.dateKey);
  const contributionDateSet = new Set(contributionDates);
  const principalSeries = buildPrincipalSeries(timeline, contributionDateSet, state.ui.amount);
  const assetResults = selectedAssets.map((assetId) =>
    simulateAsset({
      assetId,
      timeline,
      principalSeries,
      contributionDateSet,
      amount: state.ui.amount,
      mode: effectiveMode.mode,
    }),
  );

  const sampledTimeline = sampleTimeline(timeline, state.ui.sampling);
  const sampledPrincipal = sampleSeries(principalSeries, sampledTimeline);
  const sampledAssets = assetResults.map((result) => ({
    ...result,
    sampledPoints: sampleSeries(result.points, sampledTimeline),
  }));

  const notices = [...effectiveMode.messages, ...buildRunNotices(selectedAssets, state.ui.returnMode, effectiveMode.mode, priceTimeline, baseTimeline)];
  if (state.ui.returnMode === "total" && effectiveMode.mode === "price") {
    notices.push("为了保持多条指数可比，本次结果已统一切换为价格收益口径。");
  }

  if (state.refreshMeta?.refreshInProgress) {
    notices.unshift("服务器正在后台自动更新本地数据；更新完成后，页面会自动刷新到最新数据。");
  } else if (state.refreshMeta && state.refreshMeta.success === false) {
    notices.unshift("最近一次自动更新未成功完成；当前页面展示的是本地已保存的最近可用数据。");
  }

  if (notices.length) {
    dom.dataNotice.hidden = false;
    dom.dataNotice.innerHTML = notices.map(escapeHtml).join("<br />");
  }

  state.run = {
    selectedAssets,
    requestedMode: state.ui.returnMode,
    effectiveMode: effectiveMode.mode,
    frequency: state.ui.frequency,
    sampling: state.ui.sampling,
    amount: state.ui.amount,
    availableRange,
    startDateKey,
    endDateKey: timeline[timeline.length - 1].dateKey,
    timeline,
    contributions,
    principalSeries,
    assetResults: sampledAssets,
    sampledTimeline,
    sampledPrincipal,
    notices,
  };

  syncTimelineWindowInputs(state.run);

  setStatus(
    "回测完成",
    `回测区间 ${formatDateCompact(startDateKey)} 至 ${formatDateCompact(state.run.endDateKey)}，共 ${formatters.integer.format(
      contributions.length,
    )} 次定投。${buildRefreshStatusCopy()}`,
  );

  renderRun(state.run);
}

function buildRunNotices(selectedAssets, requestedMode, effectiveMode, priceTimeline, effectiveTimeline) {
  const notices = [];
  const foreignAssets = selectedAssets.filter((assetId) => ASSETS[assetId].fxPair);

  if (foreignAssets.length) {
    const fxText = foreignAssets
      .map((assetId) => `${ASSETS[assetId].name} 按 ${FX_SERIES[ASSETS[assetId].fxPair].label}`)
      .join("；");
    notices.push(`方案B美元口径：${fxText}，每次买入按买入日汇率换汇，估值时再按估值日汇率折回美元；若当日缺少官方汇率，则沿用前一可用日。`);
  }

  if (requestedMode === "total" && effectiveMode === "total") {
    for (const assetId of selectedAssets) {
      const priceStart = state.data[assetId]?.price?.[0]?.dateKey;
      const priceEnd = state.data[assetId]?.price?.at(-1)?.dateKey;
      const totalStart = state.data[assetId]?.totalReturn?.[0]?.dateKey;
      const totalEnd = state.data[assetId]?.totalReturn?.at(-1)?.dateKey;

      if (priceStart && totalStart && totalStart > priceStart) {
        notices.push(
          `${ASSETS[assetId].name} 全收益当前接入覆盖自 ${formatDateCompact(totalStart)} 起，因此全收益模式下可选区间会自动收窄。`,
        );
      }

      if (priceEnd && totalEnd && totalEnd < priceEnd) {
        notices.push(
          `${ASSETS[assetId].name} 全收益当前接入覆盖至 ${formatDateCompact(totalEnd)}，晚于该日期的最新区间会自动回退到价格收益或收窄回测终点。`,
        );
      }

      if (assetId === "nikkei225") {
        notices.push(
          `日经225在 ${formatDateCompact(totalStart)} 至 ${formatDateCompact(
            ASSETS[assetId].totalReturnInferredUntil,
          )} 区间，使用日经官方价格日线，并以官方说明书给出的 ${formatDateCompact(
            ASSETS[assetId].totalReturnCoverageStart,
          )} 基点 6,569.47 和 ${formatDateCompact(
            incrementDateKey(ASSETS[assetId].totalReturnInferredUntil, 1),
          )} 官方 TR 锚点 13,440.95 校准回算日频全收益；${formatDateCompact(
            incrementDateKey(ASSETS[assetId].totalReturnInferredUntil, 1),
          )} 至 ${formatDateCompact(
            ASSETS[assetId].totalReturnHybridUntil,
          )} 使用官方月频、官方月报锚点与官方价格日线插值；${formatDateCompact(
            dailyStartForAsset(assetId) || totalStart,
          )} 起使用官方日频全收益。`,
        );
      } else if (ASSETS[assetId].totalReturnApproximateUntil) {
        notices.push(
          `${ASSETS[assetId].name} 在 ${formatDateCompact(totalStart)} 至 ${formatDateCompact(
            ASSETS[assetId].totalReturnApproximateUntil,
          )} 区间，使用官方月频/官方月报锚点与官方价格日线插值生成日频全收益；${formatDateCompact(
            dailyStartForAsset(assetId) || totalStart,
          )} 起使用官方日频全收益。`,
        );
      }
    }

    const priceStart = priceTimeline[0]?.dateKey;
    const totalStart = effectiveTimeline[0]?.dateKey;
    if (priceStart && totalStart && totalStart > priceStart && !selectedAssets.some((assetId) => ASSETS[assetId].totalReturnCoverageStart === totalStart)) {
      notices.push(`统一全收益口径的共同可回测区间起点为 ${formatDateCompact(totalStart)}。`);
    }
  }

  return Array.from(new Set(notices));
}

function resolveEffectiveMode(selectedAssets, requestedMode) {
  if (requestedMode === "price") {
    return { mode: "price", messages: [] };
  }

  const missing = selectedAssets.filter((assetId) => !state.data[assetId]?.totalReturn?.length);
  if (!missing.length) {
    return { mode: "total", messages: [] };
  }

  const names = missing.map((assetId) => ASSETS[assetId].name).join("、");
  const suffix =
    missing.length === 1 && missing[0] === "sp500"
      ? "请运行 total return 本地化脚本，或检查 web/data/sp500-total-return.csv 是否存在有效数据。"
      : "请补充对应的全收益历史文件后再启用。";

  return {
    mode: "price",
    messages: [`${names} 当前未接入完整的全收益历史。${suffix}`],
  };
}

function buildAlignedTimeline(selectedAssets, mode) {
  if (!selectedAssets.length) return [];

  const seriesMaps = selectedAssets.map((assetId) =>
    mode === "total" ? state.data[assetId].totalReturnMap : state.data[assetId].priceMap,
  );

  let dateKeys = [];
  if (selectedAssets.length === 1) {
    dateKeys = Array.from(seriesMaps[0].keys());
  } else {
    dateKeys = Array.from(seriesMaps[0].keys()).filter((dateKey) => seriesMaps.every((map) => map.has(dateKey)));
  }

  dateKeys.sort();

  return dateKeys.map((dateKey) => {
    const referencePoint = seriesMaps[0].get(dateKey);
    const closes = {};
    const fxRates = {};
    const usdCloses = {};
    for (const assetId of selectedAssets) {
      const assetPoint =
        mode === "total" ? state.data[assetId].totalReturnMap.get(dateKey) : state.data[assetId].priceMap.get(dateKey);
      const fxPoint = resolveFxPointForDate(ASSETS[assetId].fxPair, dateKey);
      if (!assetPoint || !fxPoint || !Number.isFinite(fxPoint.close) || fxPoint.close <= 0) {
        return null;
      }
      closes[assetId] = assetPoint.close;
      fxRates[assetId] = fxPoint.close;
      usdCloses[assetId] = assetPoint.close / fxPoint.close;
    }

    return {
      dateKey,
      date: referencePoint.date,
      dateMs: referencePoint.dateMs,
      closes,
      fxRates,
      usdCloses,
    };
  }).filter(Boolean);
}

function resolveStartDateKey(timeline, availableRange) {
  let candidateDate = null;

  if (state.ui.preset) {
    candidateDate = resolvePresetDate(timeline, availableRange.end, state.ui.preset);
  } else if (dom.startDate.value) {
    candidateDate = dom.startDate.value;
  }

  if (!candidateDate) {
    candidateDate = resolvePresetDate(timeline, availableRange.end, DEFAULTS.preset);
  }

  const clamped = findNearestAvailableDateKey(timeline, candidateDate);
  dom.startDate.min = availableRange.start;
  dom.startDate.max = availableRange.end;
  dom.startDate.value = clamped;
  dom.dateRangeHint.textContent = `可选区间：${formatDateCompact(availableRange.start)} 至 ${formatDateCompact(
    availableRange.end,
  )}`;
  return clamped;
}

function ensureDateWithinAvailableRange() {
  const effectiveMode = resolveEffectiveMode(state.ui.selectedAssets, state.ui.returnMode);
  const timeline = buildAlignedTimeline(state.ui.selectedAssets, effectiveMode.mode);
  if (!timeline.length) return;
  const availableRange = {
    start: timeline[0].dateKey,
    end: timeline[timeline.length - 1].dateKey,
  };
  resolveStartDateKey(timeline, availableRange);
}

function resolvePresetDate(timeline, endDateKey, preset) {
  if (preset === "earliest") {
    return timeline[0]?.dateKey || endDateKey;
  }

  const years = Number(preset);
  if (!Number.isFinite(years)) {
    return endDateKey;
  }

  const endDate = parseUtcDate(endDateKey);
  const candidate = new Date(Date.UTC(endDate.getUTCFullYear() - years, endDate.getUTCMonth(), endDate.getUTCDate()));
  const candidateKey = toDateKey(candidate);
  return findNearestAvailableDateKey(timeline, candidateKey);
}

function findNearestAvailableDateKey(timeline, candidateKey) {
  for (const point of timeline) {
    if (point.dateKey >= candidateKey) return point.dateKey;
  }
  return timeline[timeline.length - 1].dateKey;
}

function toDateKey(date) {
  const year = date.getUTCFullYear();
  const month = `${date.getUTCMonth() + 1}`.padStart(2, "0");
  const day = `${date.getUTCDate()}`.padStart(2, "0");
  return `${year}-${month}-${day}`;
}

function buildContributionPlan(timeline, frequency) {
  const plan = [];
  let lastBucket = null;

  for (const point of timeline) {
    const bucket = getBucketKey(point.date, frequency);
    if (frequency === "daily" || bucket !== lastBucket) {
      plan.push({ dateKey: point.dateKey, bucket });
      lastBucket = bucket;
    }
  }

  return plan;
}

function getBucketKey(date, frequency) {
  if (frequency === "monthly") {
    return `${date.getUTCFullYear()}-${String(date.getUTCMonth() + 1).padStart(2, "0")}`;
  }

  if (frequency === "weekly") {
    const { year, week } = getIsoWeek(date);
    return `${year}-W${String(week).padStart(2, "0")}`;
  }

  return toDateKey(date);
}

function getIsoWeek(date) {
  const target = new Date(Date.UTC(date.getUTCFullYear(), date.getUTCMonth(), date.getUTCDate()));
  const dayNumber = target.getUTCDay() || 7;
  target.setUTCDate(target.getUTCDate() + 4 - dayNumber);
  const yearStart = new Date(Date.UTC(target.getUTCFullYear(), 0, 1));
  const week = Math.ceil(((target - yearStart) / 86400000 + 1) / 7);
  return { year: target.getUTCFullYear(), week };
}

function buildPrincipalSeries(timeline, contributionDateSet, amount) {
  let invested = 0;

  return timeline.map((point) => {
    const contribution = contributionDateSet.has(point.dateKey) ? amount : 0;
    invested += contribution;
    return {
      dateKey: point.dateKey,
      dateMs: point.dateMs,
      invested,
      contribution,
    };
  });
}

function simulateAsset({ assetId, timeline, principalSeries, contributionDateSet, amount, mode }) {
  const asset = ASSETS[assetId];
  let units = 0;
  const points = [];
  const cashFlows = [];

  for (let index = 0; index < timeline.length; index += 1) {
    const point = timeline[index];
    const close = point.closes[assetId];
    const fxRate = point.fxRates[assetId] || 1;
    const usdClose = point.usdCloses[assetId] || close;

    if (contributionDateSet.has(point.dateKey)) {
      units += (amount * fxRate) / close;
      cashFlows.push({ dateMs: point.dateMs, amount: -amount });
    }

    const principal = principalSeries[index].invested;
    const localValue = units * close;
    const value = localValue / fxRate;
    points.push({
      dateKey: point.dateKey,
      dateMs: point.dateMs,
      close,
      fxRate,
      usdClose,
      units,
      principal,
      localValue,
      value,
    });
  }

  const lastPoint = points[points.length - 1];
  cashFlows.push({ dateMs: lastPoint.dateMs, amount: lastPoint.value });

  const invested = lastPoint.principal;
  const totalValue = lastPoint.value;
  const gain = totalValue - invested;
  const totalReturn = invested > 0 ? (gain / invested) * 100 : 0;
  const annualizedReturn = computeXirr(cashFlows);
  const drawdown = computeDrawdownAnalysis(points);
  const volatility = computeAnnualizedVolatility(points);

  return {
    assetId,
    asset,
    points,
    sourceLabel: mode === "total" ? asset.totalReturnLabel : asset.priceLabel,
    effectiveMode: mode,
    invested,
    totalValue,
    gain,
    totalReturn,
    annualizedReturn: Number.isFinite(annualizedReturn) ? annualizedReturn * 100 : null,
    volatility,
    contributionCount: cashFlows.length - 1,
    drawdown,
  };
}

function computeAnnualizedVolatility(points) {
  if (points.length < 2) return null;
  const returns = [];

  for (let index = 1; index < points.length; index += 1) {
    const previous = points[index - 1].usdClose ?? points[index - 1].close;
    const current = points[index].usdClose ?? points[index].close;
    if (!previous || !current) continue;
    returns.push((current - previous) / previous);
  }

  if (!returns.length) return null;

  const mean = returns.reduce((sum, value) => sum + value, 0) / returns.length;
  const variance = returns.reduce((sum, value) => sum + (value - mean) ** 2, 0) / returns.length;
  return Math.sqrt(variance) * Math.sqrt(252) * 100;
}

function computeDrawdownAnalysis(points) {
  if (!points.length) return null;

  const events = [];
  let peakPoint = points[0];
  let peakIndex = 0;
  let worstPoint = points[0];
  let worstIndex = 0;
  let worstDrawdown = 0;

  for (let index = 1; index < points.length; index += 1) {
    const point = points[index];

    if (point.value >= peakPoint.value) {
      if (worstDrawdown < 0) {
        events.push(
          buildDrawdownEvent({
            peakPoint,
            peakIndex,
            troughPoint: worstPoint,
            troughIndex: worstIndex,
            recoveryPoint: point,
            recoveryIndex: index,
            maxDrawdown: worstDrawdown,
          }),
        );
      }

      peakPoint = point;
      peakIndex = index;
      worstPoint = point;
      worstIndex = index;
      worstDrawdown = 0;
      continue;
    }

    const drawdown = peakPoint.value > 0 ? ((point.value - peakPoint.value) / peakPoint.value) * 100 : 0;
    if (drawdown < worstDrawdown) {
      worstDrawdown = drawdown;
      worstPoint = point;
      worstIndex = index;
    }
  }

  if (worstDrawdown < 0) {
    events.push(
      buildDrawdownEvent({
        peakPoint,
        peakIndex,
        troughPoint: worstPoint,
        troughIndex: worstIndex,
        recoveryPoint: null,
        recoveryIndex: null,
        maxDrawdown: worstDrawdown,
      }),
    );
  }

  const rankedEvents = events
    .slice()
    .sort((left, right) => left.maxDrawdown - right.maxDrawdown || left.peakDateKey.localeCompare(right.peakDateKey))
    .slice(0, 5)
    .map((event, index) => ({ ...event, rank: index + 1 }));

  const primary = rankedEvents[0];
  if (!primary) {
    return {
      maxDrawdown: 0,
      peakDateKey: points[0].dateKey,
      troughDateKey: points[0].dateKey,
      recoveryDateKey: points[0].dateKey,
      peakValue: points[0].value,
      troughValue: points[0].value,
      calendarRecoveryDays: 0,
      tradingRecoveryDays: 0,
      topEvents: [],
      eventCount: 0,
    };
  }

  return {
    maxDrawdown: primary.maxDrawdown,
    peakDateKey: primary.peakDateKey,
    troughDateKey: primary.troughDateKey,
    recoveryDateKey: primary.recoveryDateKey,
    peakValue: primary.peakValue,
    troughValue: primary.troughValue,
    calendarRecoveryDays: primary.calendarRecoveryDays,
    tradingRecoveryDays: primary.tradingRecoveryDays,
    topEvents: rankedEvents,
    eventCount: events.length,
  };
}

function buildDrawdownEvent({ peakPoint, peakIndex, troughPoint, troughIndex, recoveryPoint, recoveryIndex, maxDrawdown }) {
  return {
    peakDateKey: peakPoint.dateKey,
    troughDateKey: troughPoint.dateKey,
    recoveryDateKey: recoveryPoint ? recoveryPoint.dateKey : null,
    peakValue: peakPoint.value,
    troughValue: troughPoint.value,
    maxDrawdown,
    peakToTroughTradingDays: troughIndex - peakIndex,
    calendarRecoveryDays: recoveryPoint ? Math.round((recoveryPoint.dateMs - troughPoint.dateMs) / 86400000) : null,
    tradingRecoveryDays: recoveryPoint && recoveryIndex != null ? recoveryIndex - troughIndex : null,
  };
}

function computeXirr(cashFlows) {
  if (cashFlows.length < 2) return null;

  let rate = 0.12;
  for (let iteration = 0; iteration < 80; iteration += 1) {
    const value = xnpv(rate, cashFlows);
    const derivative = dxnpv(rate, cashFlows);
    if (!Number.isFinite(value) || !Number.isFinite(derivative) || derivative === 0) break;
    const next = rate - value / derivative;
    if (!Number.isFinite(next) || next <= -0.999999) break;
    if (Math.abs(next - rate) < 1e-8) return next;
    rate = next;
  }

  let low = -0.9999;
  let high = 10;
  let lowValue = xnpv(low, cashFlows);
  let highValue = xnpv(high, cashFlows);

  if (!Number.isFinite(lowValue) || !Number.isFinite(highValue) || lowValue * highValue > 0) {
    return null;
  }

  for (let iteration = 0; iteration < 100; iteration += 1) {
    const mid = (low + high) / 2;
    const midValue = xnpv(mid, cashFlows);
    if (!Number.isFinite(midValue)) return null;
    if (Math.abs(midValue) < 1e-7) return mid;
    if (lowValue * midValue <= 0) {
      high = mid;
      highValue = midValue;
    } else {
      low = mid;
      lowValue = midValue;
    }
  }

  return (low + high) / 2;
}

function xnpv(rate, cashFlows) {
  const baseDate = cashFlows[0].dateMs;
  const oneYear = 365.25 * 86400000;

  return cashFlows.reduce((sum, flow) => {
    const years = (flow.dateMs - baseDate) / oneYear;
    return sum + flow.amount / (1 + rate) ** years;
  }, 0);
}

function dxnpv(rate, cashFlows) {
  const baseDate = cashFlows[0].dateMs;
  const oneYear = 365.25 * 86400000;

  return cashFlows.reduce((sum, flow) => {
    const years = (flow.dateMs - baseDate) / oneYear;
    return sum + (-years * flow.amount) / (1 + rate) ** (years + 1);
  }, 0);
}

function sampleTimeline(timeline, sampling) {
  if (timeline.length <= 2) return timeline.slice();
  if (sampling === "weekly") return sampleByBucket(timeline, (point) => getBucketKey(point.date, "weekly"));
  return sampleByBucket(timeline, (point) => getBucketKey(point.date, "monthly"));
}

function sampleByBucket(items, getBucket) {
  const sampled = [];
  for (let index = 0; index < items.length; index += 1) {
    const current = items[index];
    const previous = items[index - 1];
    const next = items[index + 1];
    const isFirst = index === 0;
    const isLast = index === items.length - 1;
    const bucket = getBucket(current);
    const nextBucket = next ? getBucket(next) : null;
    const previousBucket = previous ? getBucket(previous) : null;

    if (isFirst || isLast || bucket !== previousBucket || bucket !== nextBucket) {
      sampled.push(current);
    }
  }

  return dedupeByDateKey(sampled);
}

function dedupeByDateKey(items) {
  const result = [];
  const seen = new Set();
  for (const item of items) {
    if (seen.has(item.dateKey)) continue;
    seen.add(item.dateKey);
    result.push(item);
  }
  return result;
}

function sampleSeries(series, timelineSample) {
  const byDate = new Map(series.map((item) => [item.dateKey, item]));
  return timelineSample.map((point) => byDate.get(point.dateKey)).filter(Boolean);
}

function renderRun(run) {
  dom.chartEmpty.hidden = true;
  dom.effectiveModeChip.textContent = run.effectiveMode === "total" ? "全收益" : "价格收益";
  if (dom.heroLatestDate) {
    dom.heroLatestDate.textContent = formatDateCompact(run.endDateKey);
  }
  if (dom.heroStrategy) {
    dom.heroStrategy.textContent = `${describeFrequency(run.frequency)} · ${describeSelection(run.selectedAssets)} · ${
      run.effectiveMode === "total" ? "全收益" : "价格收益"
    }`;
  }
  dom.chartCaption.textContent =
    run.selectedAssets.length === 1
      ? "浅色虚线为累计本金，实线与面积为策略总资产。"
      : "浅色虚线为统一累计本金，多条彩色曲线代表相同现金流下的总资产表现。";
  if (dom.resultContext) {
    const fxContext = run.selectedAssets.some((assetId) => ASSETS[assetId].fxPair)
      ? " · 方案B美元投资者口径"
      : "";
    dom.resultContext.textContent = `回测区间：${formatDateCompact(run.startDateKey)} 至 ${formatDateCompact(
      run.endDateKey,
    )} · ${describeFrequency(run.frequency)} · ${describeSampling(run.sampling)} · ${
      run.effectiveMode === "total" ? "全收益" : "价格收益"
    }${fxContext}`;
  }
  if (dom.detailGrid) {
    dom.detailGrid.classList.toggle("detail-grid--multi-asset", run.selectedAssets.length > 1);
    dom.detailGrid.classList.toggle("detail-grid--single-asset", run.selectedAssets.length <= 1);
    dom.detailGrid.classList.toggle("detail-grid--three-plus", run.selectedAssets.length >= 3);
  }
  if (dom.resultsGrid) {
    dom.resultsGrid.classList.toggle("results-grid--three-plus", run.selectedAssets.length >= 3);
  }
  if (dom.insightPanel) {
    dom.insightPanel.classList.toggle("insight-panel--full", run.selectedAssets.length >= 3);
  }
  if (dom.assetMetrics) {
    dom.assetMetrics.dataset.count = String(run.selectedAssets.length);
  }

  renderOverviewCards(run);
  renderLegend(run);
  renderChartSummary(run);
  renderAssetMetrics(run);
  renderSourceNotes(run);
  renderScheduleSummary(run);
  renderDrawdownEvents(run);
  scheduleChartRender();
}

function renderFeedCards() {
  const latestPriceDate = getLatestCommonPriceDate();
  if (dom.heroLatestDate) {
    dom.heroLatestDate.textContent = latestPriceDate ? formatDateCompact(latestPriceDate) : "未加载";
  }
  if (!dom.feedCards) {
    return;
  }

  dom.feedCards.innerHTML = Object.values(ASSETS)
    .map((asset) => {
      const priceSeries = state.data[asset.id].price;
      const totalReturnSeries = state.data[asset.id].totalReturn;
      const priceRange = `${formatDateCompact(priceSeries[0].dateKey)} - ${formatDateCompact(
        priceSeries[priceSeries.length - 1].dateKey,
      )}`;
      const totalReturnText = totalReturnSeries.length
        ? `${formatDateCompact(totalReturnSeries[0].dateKey)} - ${formatDateCompact(
            totalReturnSeries[totalReturnSeries.length - 1].dateKey,
          )}`
        : "未导入";
      const totalReturnStatus = totalReturnSeries.length ? "已接入全收益" : "仅价格收益";
      const statusClass = totalReturnSeries.length ? "" : " feed-card__status--muted";

      return `
        <article class="feed-card">
          <div class="feed-card__top">
            <div>
              <p class="feed-card__eyebrow">${escapeHtml(asset.english)}</p>
              <strong>${escapeHtml(asset.name)}</strong>
            </div>
            <span class="metric-chip">${escapeHtml(asset.short)}</span>
          </div>
          <div class="feed-card__body">
            <p>价格序列：${escapeHtml(priceRange)}</p>
            <p>全收益：${escapeHtml(totalReturnText)}</p>
          </div>
          <span class="feed-card__status${statusClass}">${escapeHtml(totalReturnStatus)}</span>
        </article>
      `;
    })
    .join("");
}

function getLatestCommonPriceDate() {
  const selected = Object.values(ASSETS).map((asset) => state.data[asset.id].price.at(-1)?.dateKey).filter(Boolean);
  if (!selected.length) return null;
  return selected.sort()[0];
}

function renderOverviewCards(run) {
  const totalInvested = run.principalSeries.at(-1)?.invested || 0;
  const leadingAsset = [...run.assetResults].sort((left, right) => right.totalValue - left.totalValue)[0];
  const trailingAsset = [...run.assetResults].sort((left, right) => left.totalValue - right.totalValue)[0];
  const leadGap = leadingAsset && trailingAsset ? leadingAsset.totalValue - trailingAsset.totalValue : 0;
  const pointsCount = run.sampledTimeline.length;

  const cards = [
    {
      className: "overview-card overview-card--range",
      label: "回测区间",
      valueClassName: "overview-card__value overview-card__value--date",
      value: `${formatDateCompact(run.startDateKey)} - ${formatDateCompact(run.endDateKey)}`,
      copy: `可选区间 ${formatDateCompact(run.availableRange.start)} 至 ${formatDateCompact(run.availableRange.end)}`,
    },
    {
      className: "overview-card overview-card--capital",
      label: "累计投入",
      valueClassName: "overview-card__value overview-card__value--money",
      value: formatters.currency.format(totalInvested),
      copy: `${formatters.integer.format(run.contributions.length)} 次定投 · 单次 ${formatters.currency.format(run.amount)}`,
    },
    {
      className: "overview-card overview-card--points",
      label: "可视点位",
      valueClassName: "overview-card__value overview-card__value--number",
      value: formatters.integer.format(pointsCount),
      copy: `${describeSampling(run.sampling)}抽样，回测本体仍按日线推进`,
    },
    {
      className: "overview-card overview-card--lead",
      label: run.selectedAssets.length === 1 ? "当前结果" : "领先差距",
      valueClassName: "overview-card__value overview-card__value--money",
      value:
        run.selectedAssets.length === 1
          ? formatPercent(leadingAsset.totalReturn)
          : formatters.currency.format(Math.abs(leadGap)),
      copy:
        run.selectedAssets.length === 1
          ? `${leadingAsset.asset.name} 的累计收益率`
          : `${leadingAsset.asset.name} 相对 ${trailingAsset.asset.name} 的终值差`,
    },
  ];

  dom.overviewCards.innerHTML = cards
    .map(
      (card) => `
        <article class="${escapeHtml(card.className || "overview-card")}">
          <span>${escapeHtml(card.label)}</span>
          <strong class="${escapeHtml(card.valueClassName || "overview-card__value")}">${escapeHtml(card.value)}</strong>
          <p>${escapeHtml(card.copy)}</p>
        </article>
      `,
    )
    .join("");
}

function renderLegend(run) {
  const principalLegend = `
    <span class="legend-chip legend-chip--principal">
      <span class="legend-chip__dot"></span>
      累计本金
    </span>
  `;

  const assetLegends = run.assetResults
    .map(
      (result) => `
        <span class="legend-chip">
          <span class="legend-chip__dot" style="background:${escapeHtml(result.asset.color)};"></span>
          ${escapeHtml(result.asset.name)}
        </span>
      `,
    )
    .join("");

  dom.chartLegend.innerHTML = principalLegend + assetLegends;
}

function renderChartSummary(run) {
  const leadingAsset = [...run.assetResults].sort((left, right) => right.totalValue - left.totalValue)[0];
  const summary = [
    {
      label: "最新交易日",
      value: formatDateCompact(run.endDateKey),
    },
    {
      label: "资金口径",
      value: run.effectiveMode === "total" ? "全收益" : "价格收益",
    },
    {
      label: "定投次数",
      value: formatters.integer.format(run.contributions.length),
    },
    {
      label: "当前领先",
      value: run.assetResults.length === 1 ? "单指数" : leadingAsset ? leadingAsset.asset.name : "-",
    },
  ];

  dom.chartSummary.innerHTML = summary
    .map(
      (item) => `
        <article class="chart-summary__item">
          <span>${escapeHtml(item.label)}</span>
          <strong>${escapeHtml(item.value)}</strong>
        </article>
      `,
    )
    .join("");
}

function renderAssetMetrics(run) {
  if (!dom.assetMetrics) return;

  dom.assetMetrics.innerHTML = run.assetResults
    .map((result) => {
      const rows = [
        ["累计投入", formatters.currency.format(result.invested), ""],
        ["账户总资产", formatters.currency.format(result.totalValue), ""],
        ["累计收益", formatters.currency.format(result.gain), result.gain >= 0 ? "is-positive" : "is-negative"],
        ["累计收益率", formatPercent(result.totalReturn), result.totalReturn >= 0 ? "is-positive" : "is-negative"],
        [
          "资金年化收益率",
          result.annualizedReturn == null ? "—" : formatPercent(result.annualizedReturn),
          result.annualizedReturn != null && result.annualizedReturn >= 0 ? "is-positive" : "is-negative",
        ],
        [
          "最大回撤",
          result.drawdown ? formatPercent(result.drawdown.maxDrawdown) : "—",
          result.drawdown && result.drawdown.maxDrawdown <= 0 ? "is-negative" : "",
        ],
        ["年化波动率", result.volatility == null ? "—" : formatPercent(result.volatility), ""],
      ];

      return `
        <article class="metric-card">
          <div class="metric-card__head">
            <div>
              <strong>${escapeHtml(result.asset.name)}</strong>
            </div>
            <span class="metric-chip">${escapeHtml(result.asset.short)}</span>
          </div>
          ${rows
            .map(
              ([label, value, cls]) => `
                <div class="metric-row">
                  <span>${escapeHtml(label)}</span>
                  <strong class="${escapeHtml(cls)}">${escapeHtml(value)}</strong>
                </div>
              `,
            )
            .join("")}
        </article>
      `;
    })
    .join("");
}

function renderSourceNotes(run) {
  if (!dom.sourceNotes) return;

  const notes = [];

  for (const result of run.assetResults) {
    if (result.effectiveMode === "total") {
      notes.push(`${result.asset.name} 全收益使用 ${result.sourceLabel}。`);
    } else {
      notes.push(`${result.asset.name} 当前使用 ${result.sourceLabel}。`);
    }
  }

  notes.push(`定投规则：按${describeFrequency(run.frequency)}的首个可交易日买入 ${formatters.currency.format(run.amount)}。`);
  notes.push(`图表显示按${describeSampling(run.sampling)}抽样，但回测引擎按完整交易日序列计算。`);

  if (run.requestedMode === "total" && run.effectiveMode === "price") {
    notes.push("本次未能使用统一全收益口径，系统已自动回退为价格收益，避免跨资产口径不一致。");
  }

  dom.sourceNotes.innerHTML = notes.map((note) => `<li>${escapeHtml(note)}</li>`).join("");
}

function renderScheduleSummary(run) {
  const firstContribution = run.contributions[0]?.dateKey || run.startDateKey;
  const lastContribution = run.contributions.at(-1)?.dateKey || run.endDateKey;
  const totalInvested = run.principalSeries.at(-1)?.invested || 0;
  const durationYears =
    (parseUtcDate(run.endDateKey).getTime() - parseUtcDate(run.startDateKey).getTime()) / (365.25 * 86400000) || 1;
  const averageAnnualDeployment = totalInvested / durationYears;

  const items = [
    ["统一定投频率", describeFrequency(run.frequency)],
    ["首次买入", formatDateCompact(firstContribution)],
    ["最后一次买入", formatDateCompact(lastContribution)],
    ["买入次数", `${formatters.integer.format(run.contributions.length)} 次`],
    ["平均年度投入", formatters.currency.format(Math.round(averageAnnualDeployment))],
    ["回测时长", `${round(durationYears, 1)} 年`],
  ];

  dom.scheduleSummary.innerHTML = items
    .map(
      ([label, value]) => `
        <article class="schedule-item">
          <span>${escapeHtml(label)}</span>
          <strong>${escapeHtml(value)}</strong>
        </article>
      `,
    )
    .join("");
}

function renderDrawdownEvents(run) {
  const assetCount = run.assetResults.length;
  dom.drawdownEvents.dataset.count = String(assetCount);
  dom.drawdownEvents.classList.toggle("drawdown-events--single", assetCount <= 1);
  dom.drawdownEvents.classList.toggle("drawdown-events--double", assetCount === 2);
  dom.drawdownEvents.classList.toggle("drawdown-events--multi", assetCount > 1);
  dom.drawdownEvents.classList.toggle("drawdown-events--three-plus", assetCount >= 3);

  dom.drawdownEvents.innerHTML = run.assetResults
    .map((result) => {
      const drawdown = result.drawdown;
      if (!drawdown) return "";
      const topEvents = drawdown.topEvents || [];

      return `
        <article class="drawdown-item" style="--drawdown-accent:${escapeHtml(result.asset.color)}; --drawdown-soft:${escapeHtml(
          result.asset.softColor,
        )};">
          <div class="drawdown-item__top">
            <div class="drawdown-item__title">
              <strong>${escapeHtml(result.asset.name)}</strong>
              <p class="drawdown-item__meta">共识别 ${escapeHtml(
                String(drawdown.eventCount || topEvents.length),
              )} 次回撤事件</p>
            </div>
            <span class="drawdown-badge">最大 ${escapeHtml(formatPercent(drawdown.maxDrawdown))}</span>
          </div>
          <div class="drawdown-rank-list">
            ${topEvents
              .map((event) => {
                const recoveryText = event.recoveryDateKey
                  ? `${formatDateCompact(event.recoveryDateKey)} 恢复，历时 ${event.calendarRecoveryDays} 天 / ${
                      event.tradingRecoveryDays
                    } 个交易日`
                  : "截至回测终点仍未恢复前高";

                return `
                  <div class="drawdown-rank-row">
                    <span class="drawdown-rank-index">#${escapeHtml(String(event.rank))}</span>
                    <div class="drawdown-rank-body">
                      <div class="drawdown-rank-head">
                        <strong>${escapeHtml(formatPercent(event.maxDrawdown))}</strong>
                        <span>${escapeHtml(
                          `峰值 ${formatDateCompact(event.peakDateKey)} · 谷底 ${formatDateCompact(event.troughDateKey)}`,
                        )}</span>
                      </div>
                      <p class="drawdown-copy">
                        ${escapeHtml(
                          `峰谷历时 ${event.peakToTroughTradingDays} 个交易日 · ${recoveryText}`,
                        )}
                      </p>
                      <p class="drawdown-cause">${escapeHtml(`市场背景：${inferDrawdownCause(event, result.assetId)}`)}</p>
                    </div>
                  </div>
                `;
              })
              .join("")}
          </div>
        </article>
      `;
    })
    .join("");
}

function renderChart(run) {
  const visibleWindow = getVisibleWindow(run);
  const visibleTimeline = visibleWindow.timeline;
  const visiblePrincipal = visibleWindow.principal;
  const visibleAssetResults = visibleWindow.assets;
  const width = Math.max(dom.chartSurface.clientWidth || 980, 320);
  const compactChart = width < 720;
  const viewportHeight = Math.max(window.innerHeight || 0, 720);
  const labelReserve = visibleAssetResults.length ? (width < 860 ? 32 : 48) : 0;
  const naturalHeight = compactChart
    ? clamp(Math.round(Math.min(width * 0.66, viewportHeight * 0.46)), 360, 520)
    : clamp(Math.round(Math.min(width * 0.52, viewportHeight * 0.56)), 460, 760);
  const height = naturalHeight;
  const padding = compactChart
    ? { top: 24, right: 18 + labelReserve, bottom: 52, left: 62 }
    : { top: 30, right: 24 + labelReserve, bottom: 62, left: 82 };
  const plotWidth = width - padding.left - padding.right;
  const plotHeight = height - padding.top - padding.bottom;
  const plotRight = padding.left + plotWidth;
  const hoverWidth = width - padding.left;

  const allSeries = [
    visiblePrincipal.map((point) => point.invested),
    ...visibleAssetResults.map((result) => result.sampledPoints.map((point) => point.value)),
  ].flat();
  const valueRange = resolveVisibleValueRange(allSeries);
  const yMin = valueRange.min;
  const yMax = valueRange.max;
  const xMin = visibleTimeline[0].dateMs;
  const xMax = visibleTimeline[visibleTimeline.length - 1].dateMs;

  const scaleX = (dateMs) => padding.left + ((dateMs - xMin) / Math.max(1, xMax - xMin)) * plotWidth;
  const scaleY = (value) => padding.top + plotHeight - ((value - yMin) / Math.max(1, yMax - yMin)) * plotHeight;

  const yTicks = valueRange.ticks;
  const xTicks = buildDateTicks(visibleTimeline, width < 720 ? 4 : 6);

  const principalPath = linePath(
    visiblePrincipal.map((point) => ({
      x: scaleX(findTimelinePoint(visibleTimeline, point.dateKey).dateMs),
      y: scaleY(point.invested),
    })),
  );

  const assetPaths = visibleAssetResults.map((result) => {
    const linePoints = result.sampledPoints.map((point) => ({
      x: scaleX(point.dateMs),
      y: scaleY(point.value),
      value: point.value,
      dateKey: point.dateKey,
    }));

    return {
      result,
      linePoints,
      linePath: linePath(linePoints),
      areaPath: areaPath(linePoints, padding.top + plotHeight),
    };
  });

  const defs = assetPaths
    .map(
      ({ result }) => `
        <linearGradient id="gradient-${escapeHtml(result.assetId)}" x1="0" y1="0" x2="0" y2="1">
          <stop offset="0%" stop-color="${escapeHtml(result.asset.color)}" stop-opacity="0.42"></stop>
          <stop offset="100%" stop-color="${escapeHtml(result.asset.color)}" stop-opacity="0.02"></stop>
        </linearGradient>
      `,
    )
    .join("");

  const yGrid = yTicks
    .map((tick, index) => {
      const y = scaleY(tick);
      return `
        <line class="grid-line ${index === 0 ? "is-strong" : ""}" x1="${padding.left}" x2="${padding.left + plotWidth}" y1="${y}" y2="${y}"></line>
        <text class="tick-label" x="${padding.left - 10}" y="${y + 4}" text-anchor="end">${escapeHtml(
          formatCompactMoney(tick),
        )}</text>
      `;
    })
    .join("");

  const xGrid = xTicks
    .map((point) => {
      const x = scaleX(point.dateMs);
      return `
        <line class="grid-line" x1="${x}" x2="${x}" y1="${padding.top}" y2="${padding.top + plotHeight}"></line>
        <text class="tick-label" x="${x}" y="${padding.top + plotHeight + 24}" text-anchor="middle">${escapeHtml(
          formatAxisDate(point.dateKey, run.sampling),
        )}</text>
      `;
    })
    .join("");

  const assetMarkup = assetPaths
    .map(
      ({ result, areaPath: filledAreaPath, linePath: filledLinePath }) => `
        <path class="asset-area" fill="url(#gradient-${escapeHtml(result.assetId)})" d="${escapeHtml(filledAreaPath)}"></path>
        <path class="asset-line" stroke="${escapeHtml(result.asset.color)}" d="${escapeHtml(filledLinePath)}"></path>
      `,
    )
    .join("");

  const endLabels = buildChartEndLabels(assetPaths, {
    width,
    top: padding.top,
    bottom: padding.top + plotHeight,
    plotRight: padding.left + plotWidth,
  });
  const endLabelMarkup = endLabels
    .map(
      (label) => `
        <g class="chart-end-label">
          <line
            class="chart-end-label__line"
            x1="${round(label.anchorX, 2)}"
            x2="${round(label.lineEndX, 2)}"
            y1="${round(label.anchorY, 2)}"
            y2="${round(label.labelY, 2)}"
            stroke="${escapeHtml(label.color)}"
          ></line>
          <circle
            class="chart-end-label__dot"
            cx="${round(label.anchorX, 2)}"
            cy="${round(label.anchorY, 2)}"
            r="3.5"
            fill="${escapeHtml(label.color)}"
          ></circle>
          <text
            class="chart-end-label__text"
            x="${round(label.textX, 2)}"
            y="${round(label.labelY + 4, 2)}"
            fill="${escapeHtml(label.color)}"
            text-anchor="start"
          >${escapeHtml(label.text)}</text>
        </g>
      `,
    )
    .join("");

  dom.chartSurface.innerHTML = `
    <svg class="chart-svg" viewBox="0 0 ${width} ${height}" style="height:${height}px" role="img" aria-label="指数定投资产曲线">
      <defs>${defs}</defs>
      ${yGrid}
      ${xGrid}
      <line class="axis-line" x1="${padding.left}" x2="${padding.left}" y1="${padding.top}" y2="${padding.top + plotHeight}"></line>
      <line class="axis-line" x1="${padding.left}" x2="${padding.left + plotWidth}" y1="${padding.top + plotHeight}" y2="${
        padding.top + plotHeight
      }"></line>
      <path class="principal-line" d="${escapeHtml(principalPath)}"></path>
      ${assetMarkup}
      ${endLabelMarkup}
      <g id="chart-focus" hidden>
        <line class="chart-focus-line" x1="0" x2="0" y1="${padding.top}" y2="${padding.top + plotHeight}"></line>
      </g>
      <rect class="chart-overlay" x="${padding.left}" y="${padding.top}" width="${hoverWidth}" height="${plotHeight}"></rect>
    </svg>
  `;

  const svg = dom.chartSurface.querySelector("svg");
  const overlay = dom.chartSurface.querySelector(".chart-overlay");
  const focusGroup = dom.chartSurface.querySelector("#chart-focus");
  const focusLine = focusGroup.querySelector("line");

  const lookup = visibleTimeline.map((point, index) => ({
    dateKey: point.dateKey,
    dateMs: point.dateMs,
    principal: visiblePrincipal[index]?.invested || 0,
    assets: Object.fromEntries(
      visibleAssetResults.map((result) => [result.assetId, result.sampledPoints[index]?.value || 0]),
    ),
  }));

  const focusDotsMarkup = visibleAssetResults
    .map(
      (result) =>
        `<circle class="chart-focus-dot" data-asset="${escapeHtml(result.assetId)}" r="6" fill="${escapeHtml(
          result.asset.color,
        )}"></circle>`,
    )
    .join("");

  focusGroup.insertAdjacentHTML("beforeend", focusDotsMarkup);

  const handlePointerMove = (event) => {
    const rect = svg.getBoundingClientRect();
    if (!rect.width || !rect.height) return;
    const ratioX = width / rect.width;
    const pointerX = (event.clientX - rect.left) * ratioX;
    const clampedX = Math.min(Math.max(pointerX, padding.left), plotRight);
    const targetMs = xMin + ((clampedX - padding.left) / plotWidth) * (xMax - xMin);
    const nearest = findNearestLookupPoint(lookup, targetMs);
    if (!nearest) return;

    const focusX = scaleX(nearest.dateMs);
    focusGroup.hidden = false;
    focusLine.setAttribute("x1", String(focusX));
    focusLine.setAttribute("x2", String(focusX));

    for (const result of visibleAssetResults) {
      const dot = focusGroup.querySelector(`[data-asset="${result.assetId}"]`);
      if (!dot) continue;
      dot.setAttribute("cx", String(focusX));
      dot.setAttribute("cy", String(scaleY(nearest.assets[result.assetId])));
    }

    renderTooltip(event, nearest, run);
  };

  const clearPointerFocus = () => {
    focusGroup.hidden = true;
    dom.chartTooltip.hidden = true;
  };

  overlay.onpointermove = handlePointerMove;
  overlay.onpointerleave = clearPointerFocus;
  dom.chartShell.onpointermove = handlePointerMove;
  dom.chartShell.onpointerleave = clearPointerFocus;
}

function getVisibleWindow(run) {
  const totalPoints = run.sampledTimeline.length;
  const startIndex = clamp(Math.floor((totalPoints - 1) * state.chartWindow.startRatio), 0, Math.max(0, totalPoints - 2));
  const endIndex = clamp(Math.ceil((totalPoints - 1) * state.chartWindow.endRatio), startIndex + 1, totalPoints - 1);

  return {
    startIndex,
    endIndex,
    timeline: run.sampledTimeline.slice(startIndex, endIndex + 1),
    principal: run.sampledPrincipal.slice(startIndex, endIndex + 1),
    assets: run.assetResults.map((result) => ({
      ...result,
      sampledPoints: result.sampledPoints.slice(startIndex, endIndex + 1),
    })),
  };
}

function syncTimelineWindowInputs(run) {
  if (!run || !dom.timelineStart || !dom.timelineEnd) return;
  const max = Number(dom.timelineStart.max) || 1000;
  const minGap = getMinimumWindowGap();
  let startValue = Math.round(state.chartWindow.startRatio * max);
  let endValue = Math.round(state.chartWindow.endRatio * max);

  startValue = clamp(startValue, 0, max - minGap);
  endValue = clamp(endValue, minGap, max);
  if (endValue - startValue < minGap) {
    endValue = Math.min(max, startValue + minGap);
    startValue = Math.max(0, endValue - minGap);
  }

  dom.timelineStart.value = String(startValue);
  dom.timelineEnd.value = String(endValue);
  state.chartWindow = { startRatio: startValue / max, endRatio: endValue / max };
  updateTimelineRangeUi(run);
}

function handleTimelineRangeInput(activeHandle) {
  if (!state.run) return;
  const max = Number(dom.timelineStart.max) || 1000;
  const minGap = getMinimumWindowGap();
  let startValue = Number(dom.timelineStart.value);
  let endValue = Number(dom.timelineEnd.value);

  if (endValue - startValue < minGap) {
    if (activeHandle === "start") {
      startValue = endValue - minGap;
    } else {
      endValue = startValue + minGap;
    }
  }

  startValue = clamp(startValue, 0, max - minGap);
  endValue = clamp(endValue, minGap, max);
  dom.timelineStart.value = String(startValue);
  dom.timelineEnd.value = String(endValue);
  state.chartWindow = { startRatio: startValue / max, endRatio: endValue / max };
  updateTimelineRangeUi(state.run);
  scheduleChartRender();
}

function resetTimelineWindow() {
  state.chartWindow = { startRatio: 0, endRatio: 1 };
  if (state.run) {
    syncTimelineWindowInputs(state.run);
    renderChart(state.run);
  }
}

function updateTimelineRangeUi(run) {
  if (!run || !dom.visibleRangeLabel || !dom.timelineRangeFill) return;
  const visible = getVisibleWindow(run);
  const max = Number(dom.timelineStart.max) || 1000;
  const startValue = Math.round(state.chartWindow.startRatio * max);
  const endValue = Math.round(state.chartWindow.endRatio * max);

  dom.visibleRangeLabel.textContent = `${formatDateCompact(visible.timeline[0].dateKey)} - ${formatDateCompact(
    visible.timeline[visible.timeline.length - 1].dateKey,
  )} · ${formatters.integer.format(visible.timeline.length)} 点`;
  dom.timelineRangeFill.style.left = `${(startValue / max) * 100}%`;
  dom.timelineRangeFill.style.width = `${((endValue - startValue) / max) * 100}%`;
}

function scheduleChartRender() {
  if (!state.run) return;
  if (state.chartRenderFrame != null) {
    cancelAnimationFrame(state.chartRenderFrame);
  }
  state.chartRenderFrame = requestAnimationFrame(() => {
    state.chartRenderFrame = null;
    renderChart(state.run);
  });
}

function getMinimumWindowGap() {
  return 12;
}

function renderTooltip(event, nearest, run) {
  const rows = [
    `
      <div class="tooltip-row">
        <span>累计本金</span>
        <strong>${escapeHtml(formatters.currency.format(nearest.principal))}</strong>
      </div>
    `,
    ...run.assetResults.map(
      (result) => `
        <div class="tooltip-row">
          <span>${escapeHtml(result.asset.name)}</span>
          <strong>${escapeHtml(formatters.currency.format(nearest.assets[result.assetId]))}</strong>
        </div>
      `,
    ),
  ].join("");

  dom.chartTooltip.innerHTML = `
    <strong>${escapeHtml(formatDateCompact(nearest.dateKey))}</strong>
    ${rows}
  `;
  dom.chartTooltip.hidden = false;

  const shellRect = dom.chartSurface.parentElement.getBoundingClientRect();
  const tooltipRect = dom.chartTooltip.getBoundingClientRect();
  let left = event.clientX - shellRect.left;
  const top = event.clientY - shellRect.top;

  if (left < tooltipRect.width / 2 + 12) {
    left = tooltipRect.width / 2 + 12;
  }

  if (left > shellRect.width - tooltipRect.width / 2 - 12) {
    left = shellRect.width - tooltipRect.width / 2 - 12;
  }

  dom.chartTooltip.style.left = `${left}px`;
  dom.chartTooltip.style.top = `${top}px`;
}

function installChartResizeObserver() {
  if (state.chartObserver) return;
  state.chartObserver = new ResizeObserver(() => {
    if (state.run) renderChart(state.run);
  });
  state.chartObserver.observe(dom.chartSurface);
}

function findTimelinePoint(timeline, dateKey) {
  return timeline.find((point) => point.dateKey === dateKey) || timeline[0];
}

function findNearestLookupPoint(points, targetMs) {
  if (!points.length) return null;
  let low = 0;
  let high = points.length - 1;

  while (low < high) {
    const mid = Math.floor((low + high) / 2);
    if (points[mid].dateMs < targetMs) {
      low = mid + 1;
    } else {
      high = mid;
    }
  }

  const current = points[low];
  const previous = points[Math.max(0, low - 1)];
  return Math.abs(current.dateMs - targetMs) < Math.abs(previous.dateMs - targetMs) ? current : previous;
}

function linePath(points) {
  if (!points.length) return "";
  return points.map((point, index) => `${index === 0 ? "M" : "L"} ${round(point.x, 2)} ${round(point.y, 2)}`).join(" ");
}

function areaPath(points, baselineY) {
  if (!points.length) return "";
  const head = `M ${round(points[0].x, 2)} ${round(baselineY, 2)}`;
  const body = points.map((point) => `L ${round(point.x, 2)} ${round(point.y, 2)}`).join(" ");
  const tail = `L ${round(points[points.length - 1].x, 2)} ${round(baselineY, 2)} Z`;
  return `${head} ${body} ${tail}`;
}

function buildChartEndLabels(assetPaths, { width, top, bottom, plotRight }) {
  const rawLabels = assetPaths
    .map(({ result, linePoints }) => {
      const anchor = linePoints[linePoints.length - 1];
      if (!anchor) return null;
      return {
        assetId: result.assetId,
        color: result.asset.color,
        text: width < 860 ? result.asset.short : result.asset.name,
        anchorX: anchor.x,
        anchorY: anchor.y,
        labelY: anchor.y,
      };
    })
    .filter(Boolean)
    .sort((left, right) => left.labelY - right.labelY);

  if (!rawLabels.length) return [];

  const minGap = width < 860 ? 16 : 20;
  const topBound = top + 12;
  const bottomBound = bottom - 12;

  rawLabels[0].labelY = clamp(rawLabels[0].labelY, topBound, bottomBound);
  for (let index = 1; index < rawLabels.length; index += 1) {
    rawLabels[index].labelY = Math.max(rawLabels[index].labelY, rawLabels[index - 1].labelY + minGap);
  }

  const overflow = rawLabels[rawLabels.length - 1].labelY - bottomBound;
  if (overflow > 0) {
    rawLabels[rawLabels.length - 1].labelY -= overflow;
    for (let index = rawLabels.length - 2; index >= 0; index -= 1) {
      rawLabels[index].labelY = Math.min(rawLabels[index].labelY, rawLabels[index + 1].labelY - minGap);
    }
  }

  for (let index = 0; index < rawLabels.length; index += 1) {
    rawLabels[index].labelY = clamp(rawLabels[index].labelY, topBound, bottomBound);
  }

  return rawLabels.map((label) => ({
    ...label,
    lineEndX: plotRight + 8,
    textX: plotRight + 12,
  }));
}

function resolveVisibleValueRange(values) {
  const finiteValues = values.filter(Number.isFinite);
  if (!finiteValues.length) {
    return buildNiceAxis(0, 1, 5, true);
  }

  let rawMin = Math.min(...finiteValues);
  let rawMax = Math.max(...finiteValues);

  if (rawMin === rawMax) {
    const pad = Math.max(1, rawMax * 0.08);
    return buildNiceAxis(Math.max(0, rawMin - pad), rawMax + pad, 4, rawMin <= 0);
  }

  const span = rawMax - rawMin;
  const anchorZero = rawMin <= 0 || (rawMin > 0 && rawMin / rawMax < 0.18);
  if (anchorZero) {
    return buildNiceAxis(0, rawMax, 5, true);
  }

  const upperPad = Math.max(span * 0.08, rawMax * 0.015);
  const lowerPad = Math.max(span * 0.08, rawMax * 0.01);
  const min = Math.max(0, rawMin - lowerPad);
  const max = rawMax + upperPad;
  return buildNiceAxis(min, max, 5, false);
}

function buildDateTicks(timeline, count) {
  if (timeline.length <= count) return timeline;
  const step = (timeline.length - 1) / (count - 1);
  const ticks = [];
  for (let index = 0; index < count; index += 1) {
    ticks.push(timeline[Math.round(step * index)]);
  }
  return dedupeByDateKey(ticks);
}

function buildNiceAxis(minValue, maxValue, targetIntervals = 5, forceZeroMin = false) {
  const safeMin = Number.isFinite(minValue) ? minValue : 0;
  const safeMax = Number.isFinite(maxValue) ? maxValue : 1;
  const min = forceZeroMin ? 0 : safeMin;
  const max = safeMax <= min ? min + 1 : safeMax;
  const roughStep = (max - min) / Math.max(1, targetIntervals);
  const step = chooseNiceStep(roughStep);
  const axisMin = forceZeroMin ? 0 : Math.floor(min / step) * step;
  const axisMax = Math.ceil(max / step) * step;
  const ticks = [];

  for (let value = axisMin; value <= axisMax + step * 0.5; value += step) {
    ticks.push(round(value, 6));
  }

  return {
    min: axisMin,
    max: axisMax,
    ticks,
    step,
  };
}

function chooseNiceStep(rawStep) {
  if (!Number.isFinite(rawStep) || rawStep <= 0) return 1;
  const magnitude = 10 ** Math.floor(Math.log10(rawStep));
  const normalized = rawStep / magnitude;
  const factors = [1, 1.2, 1.5, 2, 2.5, 3, 4, 5, 6, 7.5, 8, 10];

  for (const factor of factors) {
    if (normalized <= factor) {
      return factor * magnitude;
    }
  }

  return 10 * magnitude;
}

function describeFrequency(frequency) {
  if (frequency === "daily") return "每个交易日定投";
  if (frequency === "weekly") return "每周定投";
  return "每月定投";
}

function describeSampling(sampling) {
  return sampling === "weekly" ? "周度" : "月度";
}

function describeSelection(selectedAssets) {
  if (selectedAssets.length === 1) {
    return `${ASSETS[selectedAssets[0]].name} 单资产`;
  }
  return `${selectedAssets.length} 指数对比`;
}

function dailyStartForAsset(assetId) {
  if (assetId !== "nikkei225") return null;
  return "2023-01-04";
}

function incrementDateKey(dateKey, dayOffset) {
  const dateValue = new Date(`${dateKey}T00:00:00`);
  dateValue.setDate(dateValue.getDate() + dayOffset);
  return [
    dateValue.getFullYear(),
    `${dateValue.getMonth() + 1}`.padStart(2, "0"),
    `${dateValue.getDate()}`.padStart(2, "0"),
  ].join("-");
}

function formatDateCompact(dateKey) {
  return dateKey.replaceAll("-", "/");
}

function formatDateTimeCompact(value) {
  if (!value) return "";
  const dateValue = new Date(value);
  if (!Number.isFinite(dateValue.getTime())) return "";
  const year = dateValue.getFullYear();
  const month = `${dateValue.getMonth() + 1}`.padStart(2, "0");
  const day = `${dateValue.getDate()}`.padStart(2, "0");
  const hour = `${dateValue.getHours()}`.padStart(2, "0");
  const minute = `${dateValue.getMinutes()}`.padStart(2, "0");
  return `${year}/${month}/${day} ${hour}:${minute}`;
}

function buildRefreshStatusCopy() {
  if (!state.refreshMeta?.success || !state.refreshMeta.finishedAt) {
    return "";
  }
  return ` 本地数据自动更新于 ${formatDateTimeCompact(state.refreshMeta.finishedAt)}。`;
}

function scheduleRefreshStatusPolling() {
  if (!state.refreshMeta?.refreshInProgress) {
    if (state.refreshPollTimer != null) {
      clearTimeout(state.refreshPollTimer);
      state.refreshPollTimer = null;
    }
    return;
  }

  if (state.refreshPollTimer != null) {
    clearTimeout(state.refreshPollTimer);
  }

  state.refreshPollTimer = window.setTimeout(async () => {
    const latest = await fetchOptionalJson("/api/refresh-status");
    if (!latest) {
      scheduleRefreshStatusPolling();
      return;
    }
    state.refreshMeta = latest;
    if (latest.refreshInProgress) {
      scheduleRefreshStatusPolling();
      return;
    }
    window.location.reload();
  }, 5000);
}

function formatAxisDate(dateKey, sampling) {
  const [year, month] = dateKey.split("-");
  return sampling === "weekly" ? `${year}/${month}` : `${year}/${month}`;
}

function formatPercent(value) {
  if (!Number.isFinite(value)) return "—";
  return `${round(value, Math.abs(value) >= 100 ? 1 : 2)}%`;
}

function inferDrawdownCause(event, assetId) {
  if (!event?.peakDateKey && !event?.troughDateKey) {
    return "流动性、政策预期与风险偏好同步转弱";
  }

  const eventStart = event.peakDateKey || event.troughDateKey;
  const eventEnd = event.troughDateKey || event.peakDateKey;
  const matchedRule = DRAWDOWN_CAUSE_RULES
    .filter((rule) => {
      const assetMatched = !rule.assets || rule.assets.includes(assetId);
      return assetMatched && dateRangesOverlap(eventStart, eventEnd, rule.start, rule.end);
    })
    .sort((left, right) => {
      const leftSpecific = left.assets ? 1 : 0;
      const rightSpecific = right.assets ? 1 : 0;
      if (leftSpecific !== rightSpecific) return rightSpecific - leftSpecific;
      return dateRangeLength(left.start, left.end) - dateRangeLength(right.start, right.end);
    })[0];

  return matchedRule ? matchedRule.label : "估值回吐、政策预期转弱与流动性扰动共振";
}

function dateRangesOverlap(startA, endA, startB, endB) {
  return startA <= endB && endA >= startB;
}

function dateRangeLength(startDateKey, endDateKey) {
  return Math.abs(parseUtcDate(endDateKey).getTime() - parseUtcDate(startDateKey).getTime());
}

function formatCompactMoney(value) {
  if (!Number.isFinite(value)) return "$0";
  return formatters.compactCurrency.format(value);
}

function setStatus(title, text) {
  dom.statusTitle.textContent = title;
  dom.statusText.textContent = text;
}

function escapeHtml(value) {
  return String(value)
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#39;");
}

function round(value, digits = 2) {
  const factor = 10 ** digits;
  return Math.round(value * factor) / factor;
}

function clamp(value, min, max) {
  return Math.min(Math.max(value, min), max);
}
