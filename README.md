# 指数定投回测工作台

一个本地可运行的指数定投回测网页，用来回测 **标普500**、**纳斯达克100**、**沪深300** 与 **日经225** 的长期定投表现，支持最多四指数对比、价格收益与全收益口径、累计资产曲线、资金年化收益率、最大回撤和年度截面。

## 当前能力

- 资产选择：`S&P 500`、`Nasdaq 100`、`CSI 300`、`Nikkei 225`
- 最多同时选择：`4` 条指数
- 定投频率：`每月`、`每周`、`每个交易日`
- 图表抽样：`月度`、`周度`
- 输出指标：累计投入、账户总资产、累计收益、累计收益率、资金年化收益率、最大回撤、年化波动率
- 对比逻辑：多资产时统一现金流与共同交易日历，保证比较公平
- 口径处理：如果某个指数缺少完整全收益历史，页面会自动回退到统一的价格收益口径，并明确提示
- 跨市场比较：沪深300与日经225按`方案B`的美元投资者口径处理，买入日与估值日均考虑汇率
- 自动更新：启动预览服务时会自动刷新本地数据，页面打开后也会感知后台更新并自动切到最新数据

## 数据源

### 价格收益

- `^SPX`（S&P 500）：`https://stooq.com/q/d/l/?s=^spx&i=d`
- `^NDX`（Nasdaq 100）：`https://stooq.com/q/d/l/?s=^ndx&i=d`

本地文件：

- `web/data/sp500.csv`
- `web/data/nasdaq100.csv`
- `web/data/hs300.csv`
- `web/data/nikkei225.csv`

### 全收益

- `XNDX`（Nasdaq-100 Total Return）：Nasdaq 官方历史页与历史接口
- `^SP500TR`（S&P 500 Total Return）：Yahoo Finance 历史接口
- `SPXT`：S&P Dow Jones Indices 官方总收益符号
- `H00300`（CSI 300 Total Return）：中证指数官方历史接口
- `NK225TR`（Nikkei 225 Total Return）：日经官方日频 CSV、月频 CSV 与官方月报 PDF 锚点混合本地化

本地文件：

- `web/data/nasdaq100-total-return.csv`
- `web/data/sp500-total-return.csv`
- `web/data/hs300-total-return.csv`
- `web/data/nikkei225-total-return.csv`

说明：

- `nasdaq100-total-return.csv` 通过 Nasdaq 官方历史接口本地化。
- `sp500-total-return.csv` 通过 Yahoo Finance 的 `^SP500TR` 历史接口本地化；页面同时保留 `SPXT` 作为官方符号说明，方便你后续替换成严格官方导出文件。
- 标普500、纳斯达克100、沪深300都可直接使用全收益口径。
- 日经225全收益目前已前补到 `2012-12-03`；`2023-01-04` 起使用官方日频全收益，较早区间使用官方月频与官方月报锚点结合日频价格插值。

## 更新本地数据

在仓库根目录执行：

更新价格数据：

```bash
./backend/scripts/localize_market_data.sh
```

更新全收益数据：

```bash
python3 backend/scripts/localize_total_return_data.py
```

更新跨市场与汇率数据：

```bash
python3 backend/scripts/localize_scheme_b_data.py
```

一键刷新全部数据：

```bash
python3 backend/scripts/refresh_backtest_data.py
```

## 启动网页

```bash
python3 preview_server.py
```

然后打开 `http://127.0.0.1:4175`。

如果你想使用其他端口：

```bash
PORT=8080 python3 preview_server.py
```

## 计算口径

- 定投买点：每个周期的首个可交易日
- 买入价格：当日收盘价
- 多资产对比：按共同可交易日期对齐后再模拟
- 最大回撤：基于策略资产净值曲线计算
- 资金年化收益率：基于实际现金流的 `XIRR`
- 年化波动率：基于所用指数序列的日收益率估算
