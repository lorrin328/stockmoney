

## 研究更新闭环

当用户发送 `研究更新`、`迭代`、`research update` 时，执行研究迭代流程：

```bash
bash /opt/stockmoney/scripts/run_research.sh
```

该流程会自动：
1. 收集当前系统各模块状态
2. 调用 CC CLI (Claude Code) 分析并修改代码中的过时判断
3. 验证修改后的系统能正常运行
4. 自动 git commit/push 到 GitHub
5. 生成更新报告

**注意**：研究更新耗时较长（2-5分钟），请耐心等待。CC CLI 使用 qwen3.5-plus 模型驱动。

## 定时任务汇总

| 时间 | 任务 | 脚本 |
|------|------|------|
| 工作日 9:25 | 盘前监控 | run_monitor.sh |
| 工作日 15:05 | 盘后监控 | run_monitor.sh |
| 每日 20:00 | 策略摘要 | run_strategy.sh |
| 每周一 9:30 | 周度报告 | run_full_report.sh |
| 每月1日 9:00 | 政策分析 | run_policy.sh |
| 每周三 20:00 | 研究更新 | run_research.sh |
