# Fund Tracer

记录基金持仓，查询实时估算净值、涨跌幅与持仓收益。

## 安装为 Agent 技能

将本项目克隆到 Agent 的技能目录，例如：

```bash
git clone https://github.com/tangnanxi/fund_tracer.git fund-tracker
```

## 记录持仓

安装后，你可以直接对 Agent 说：

```
008114这个基金持仓平均成本1.0，持有份额20份
```

Agent 会帮你更新 `references/holdings.json` 中的持仓信息。

## 查询实时情况

对 Agent 说：

```
查询我的基金当前涨跌
```

脚本会输出每只基金的估算涨跌、当日预估收益、持仓市值和累计收益。

## 数据来源

天天基金网公开接口：`https://fundgz.1234567.com.cn/js/{code}.js`

## 文件说明

| 文件 | 说明 |
| --- | --- |
| `SKILL.md` | 技能说明与触发描述 |
| `scripts/fund_tracker.py` | 查询与收益计算脚本 |
| `references/funds.txt` | 基金代码列表 |
| `references/holdings.json` | 持仓配置 |
| `references/history.json` | 净值历史 |
