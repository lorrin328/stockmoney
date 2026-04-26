# MCP 服务器配置指南

## 已配置的服务器

### 1. Alpha Vantage（股票数据）
- **仓库**: [berlinbra/alpha-vantage-mcp](https://github.com/berlinbra/alpha-vantage-mcp)
- **功能**: 获取股票、加密货币的实时和历史数据
- **API Key**: 需在 [Alpha Vantage](https://www.alphavantage.co/support/#api-key) 免费申请
- **环境变量**: `ALPHA_VANTAGE_API_KEY`

### 2. Investor Agent（Yahoo Finance）
- **仓库**: [ferdousbhai/investor-agent](https://github.com/ferdousbhai/investor-agent)
- **功能**: Yahoo Finance 股票数据，含期权推荐
- **无需 API Key**

### 3. FinBud Data（综合金融数据）
- **仓库**: [glaksmono/finbud-data-mcp](https://github.com/glaksmono/finbud-data-mcp)
- **功能**: 股票、期权、加密货币、外汇实时数据
- **可能需要 API Key**

### 4. Helium（新闻+市场数据）
- **仓库**: [connerlambden/helium-mcp](https://github.com/connerlambden/helium-mcp)
- **功能**: 5000+ 来源的实时新闻、AI 期权定价、市场数据
- **免费 50 次查询，无需注册**

### 5. Katzilla（政府/经济数据）
- **仓库**: [codeislaw101/katzilla](https://github.com/codeislaw101/katzilla)
- **功能**: 300+ 免费数据源
  - 经济: FRED、BLS（美国劳工统计局）
  - 金融: SEC、CFPB
  - 环境: EPA、NOAA
  - 科学: NASA、arXiv
- **无需 API Key**

### 6. Playwright（网页抓取）
- **仓库**: [microsoft/playwright-mcp](https://github.com/microsoft/playwright-mcp)
- **功能**: 自动化浏览器操作，抓取政策网站、财经新闻
- **无需 API Key**

### 7. GitHub MCP Server
- **仓库**: [github/github-mcp-server](https://github.com/github/github-mcp-server)
- **功能**: GitHub 仓库管理、Issue、PR 操作
- **需要 GitHub Token**

## 中国 A 股数据源

目前 MCP 生态中直接支持 A 股的较少，建议通过以下方式：

### 方式 1：Python 脚本调用
```python
# 使用 akshare（免费）
import akshare as ak
stock_zh_a_spot_df = ak.stock_zh_a_spot()

# 使用 tushare（需积分）
import tushare as ts
pro = ts.pro_api('your_token')
```

### 方式 2：Playwright 抓取
- 东方财富网
- 雪球
- 同花顺
- 新浪财经

## 安装与启动

所有 MCP 服务器均通过 `npx` 一键安装，无需本地克隆仓库：

```bash
# 测试 Alpha Vantage MCP
npx -y alpha-vantage-mcp

# 测试 Yahoo Finance MCP
npx -y investor-agent

# 测试 Helium 新闻 MCP
npx -y helium-mcp
```

## Claude Code 中使用

配置完成后，在 Claude Code 中可以直接调用：

```
"获取 Apple 股票最近 30 天的收盘价"
"搜索关于新能源汽车的最新政策"
"分析美联储最新的利率决议"
```
