# 持仓数据目录

此目录由功能 2(持仓截图记录与建议)产生,存储用户实际持仓的快照数据。

## 文件命名

| 文件 | 用途 |
|------|------|
| `positions_{YYYYMMDD}.json` | 单日持仓快照 |
| `positions_history.csv` | 历史持仓变动记录 |

## 隐私

具体持仓 JSON 与历史 CSV 已在 `.gitignore` 中排除,**不会同步到 GitHub**。
