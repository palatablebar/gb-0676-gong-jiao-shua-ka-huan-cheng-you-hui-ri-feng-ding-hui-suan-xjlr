# 票种基数裁决（2026-11-21）

## 争议

学生、老年票种实付（学生 50%、老年 20%，均以普通票价为锚）低于普通票价。若把固定 1 元换乘
减免放在票种实付上，低票价行程会出现“减免 > 本程实付”，清分补贴被放大为负值/超额；若把日封顶
也按票种实付计，学生、老年乘客的换乘与封顶权益随票价缩水。

## 裁决：权益与出钱分离，双基数

| 口径 | 采用基数 | 用途 |
|---|---|---|
| 权益口径 | **普通票价统一基数** | 换乘减免、日封顶的资格与额度，保证学生/老年权益不缩水 |
| 出钱口径 | **票种实付统一基数** | 乘客当程应收 `expected`、清分补贴上限 |

同一张卡不允许“混用基数”：权益按普通票价计算，收钱与补贴按票种实付封顶，两张口径并行登记、
一次裁决，形成每张卡每个业务日**唯一应收**（卡日合计 `day_paid` 即唯一应收，落库即占用，重跑
同批幂等不重复占额）。

## 逐程裁决顺序（M5）

记普通票价 `B`、票种实付 `P`、固定换乘减免参数 `d=1.00`、日封顶 `C=6.00`。

1. **换乘权益（普通基数）**：满足跨线 + 半开 60 分钟窗 + 上次实际付费锚点时
   `transfer_entitlement = min(B, d)`，否则 0。锚点只在本程实际有应收（charge>0）时推进，
   零付费行程不延长锚点。
2. **票种实付上的可减免额**：`transfer_discount = min(P, transfer_entitlement)`。
   权益不缩水（仍按普通票价取得资格与 1 元额度），但减免永远不超过本程票种实付，从根上杜绝
   “减免超过实付、清分补贴被放大”。未落到本程的权益差额 `transfer_entitlement -
   transfer_discount` 只登记为放弃额，不折现金、不滚存。
3. **日封顶（普通基数测权益，实付口径收钱）**：
   - 普通基数余量 `cap_remaining_base = max(0, C - spent_base)`，封顶减免先按普通票价测算
     `cap_relief_base = min(cap_remaining_base, B - transfer_entitlement)`；
   - 乘客实际应收 `charge = max(0, P - transfer_discount - cap_relief_base)`，再以
     `cap_discount = P - transfer_discount - charge` 回算实际封顶减免，保证
     `P = charge + transfer_discount + cap_discount` 逐程守恒。
4. 影子口径：同一序列再按**票种实付基数**（`min(P,d)` 减免、按实付累计封顶）平行计算
   `alt_expected / alt_day_paid / alt_cap_remaining`，仅供页面展示两种口径的应收、封顶余量与
   差异，不参与落账。

## 清分补贴（M6）

每程清分补贴 `subsidy = (B - transfer_discount - cap_discount) - expected`，受票种实付硬约束
`subsidy ≤ P`（等价于 `expected ≥ 0`，由第 3 步构造保证）。补贴拆成票种让利
`fare_subsidy = B - P` 与优惠补贴 `discount_subsidy = transfer_discount + cap_discount`，
恒等校验：`B = expected + fare_subsidy + discount_subsidy`，
`P = expected + transfer_discount + cap_discount`。补贴不可能超过本程票种实付。

## 不确定与封存纪律

- 票种不在 {普通, 学生, 老年} 或为空、金额为哨兵/无法解析：该行隔离（`UNKNOWN_TICKET` /
  `EMPTY_VALUE` / `INVALID_NUMBER`），不进应收、不占封顶额度。
- 已发布日账不因重算被覆盖：同输入同参数同规则版本派生同一 run_id，`INSERT OR IGNORE` 幂等
  复用，重跑同批不重复占额；已封存批次的复核提交走版本条件更新，陈旧版本返回 409。
- 清分对账未对平（来源行不平、补贴/守恒校验不过）时 M7 抛 `UNBALANCED`，不得封存。
