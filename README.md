# Fund Tracer

记录基金持仓，查询实时估算净值、涨跌幅与持仓收益。

## 安装
在cursor/claude中输入：
```bash
安装这个技能 https://github.com/tangnanxi/fund_tracer.git
```

## 记录持仓
在cursor/claude中输入：
```bash
008114这个基金持仓平均成本1.0，持有份额20份
```


## 查询实时情况

在cursor/claude中输入：
```bash
查询我的基金当前涨跌
```

脚本会输出每只基金的估算涨跌、当日预估收益、持仓市值和累计收益。

## 数据来源

天天基金网公开接口：`https://fundgz.1234567.com.cn/js/{code}.js`
