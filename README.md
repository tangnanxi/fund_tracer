# Fund Tracer

一个用于查看基金实时估算涨跌和持仓收益的 Agent Skill。

## 功能

- 查询多只基金的实时估算净值、估算涨跌幅和估值时间
- 根据持仓份额与成本价计算当日预估收益、持仓市值和累计收益
- 将每日估算净值保存到历史记录，方便持续追踪

## 使用

1. 在 references/funds.txt 中填写基金代码，每行一个。
2. 如需计算持仓收益，编辑 references/holdings.json，填写份额和成本价。
3. 在技能目录执行：

   python scripts/fund_tracker.py

也可以直接对 Agent 说：**“查一下我的基金”**。

## 文件说明

- SKILL.md：技能说明与调用规则
- scripts/fund_tracker.py：查询与收益计算脚本
- references/：基金列表、持仓配置和历史数据

> 数据来自天天基金公开接口，返回的是实时估算净值，仅供参考，实际净值以基金公司公布为准。
