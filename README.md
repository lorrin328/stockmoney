# StockMoney - 投资研究工作区

> 专注投资、股票、政策、市场的研究资料库

## 目录结构

```
stockmoney/
├── data/              # 原始数据与处理后的数据
├── reports/           # 研究报告输出
├── scripts/           # 数据处理脚本
├── policies/          # 政策文件归档
├── .claude/           # Claude Code 配置
└── .github/           # GitHub Actions 工作流
```

## 核心功能

- **股票数据分析**：美股、港股、A股数据获取与分析
- **政策解读**：宏观政策、行业政策的追踪与解读
- **市场研究**：行业趋势、市场情绪、资金流向
- **投资策略**：量化模型、投资组合管理

## MCP 服务器配置

本项目配置了以下 MCP 服务器用于投资研究：

| MCP 服务器 | 用途 | 安装方式 |
|-----------|------|---------|
| alpha-vantage-mcp | 股票/加密货币数据 | `npx -y alpha-vantage-mcp` |
| investor-agent | Yahoo Finance 数据 | `npx -y investor-agent` |
| finbud-data-mcp | 综合金融数据 | `npx -y finbud-data-mcp` |
| helium-mcp | 新闻+市场数据 | `npx -y helium-mcp` |
| katzilla | 政府/经济数据 | `npx -y @katzilla/mcp` |
| playwright-mcp | 网页抓取 | `npx -y @playwright/mcp` |
| github-mcp-server | GitHub 操作 | 内置 |

## Skill 配置

数据处理相关的自动化 Skill 已配置在 `.claude/settings.json` 中。

## 使用方式

1. 使用 Claude Code 打开本项目
2. 通过 MCP 服务器获取实时数据
3. 在 `reports/` 目录生成研究报告
4. 数据自动同步到 GitHub

## 数据来源

- Alpha Vantage（美股/全球股票）
- Yahoo Finance（美股/港股/基金）
- LongPort（港股实时数据）
- FRED（美国经济数据）
- SEC（美国证监会文件）

## License

MIT
