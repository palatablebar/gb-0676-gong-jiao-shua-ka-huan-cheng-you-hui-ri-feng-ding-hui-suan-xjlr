from decimal import Decimal
from app.values import number,instant,money
from app.errors import DomainError
ZERO=Decimal(0)
def evaluate(rows,context):
    """票种基数裁决（docs/RULING.md）：权益按普通票价基数，应收与补贴按票种实付基数。"""
    params=context.get("parameters",{});cap=number(params.get("daily_cap","6.00"));off=number(params.get("transfer_discount","1.00"));window=number(params.get("transfer_minutes","60"))
    if cap<0 or off<0 or window<0:raise DomainError("BAD_DISCOUNT","优惠参数不能为负")
    spent_pay={};spent_base={};alt_spent={};anchor={};alt_anchor={};day_order=[];day_meta={}
    good=[]
    for row in sorted(rows,key=lambda r:(r["card"],instant(r["at"]),r["event_id"])):
        key=(row["card"],row["business_day"])
        if key not in day_meta:
            day_order.append(key);day_meta[key]={"legs":0}
        base=number(row["base_fare"]);payable=number(row.get("payable_fare",row["base_fare"]));previous=anchor.get(key)
        # 1) 换乘权益：普通票价基数，半开窗口、跨线、锚点为上次实际付费行程
        eligible=False
        if previous:
            delta=Decimal(str((instant(row["at"])-instant(previous["at"])).total_seconds()))/60
            eligible=previous["route"]!=row["route"] and Decimal(0)<=delta<window
        entitlement=min(base,off) if eligible else ZERO
        # 2) 票种实付硬约束：减免不得超过本程票种实付
        transfer=min(payable,entitlement)
        forfeited=entitlement-transfer
        # 3) 日封顶：普通基数测余量与减免，实付口径回算唯一应收
        base_net=base-entitlement
        remaining_base=max(ZERO,cap-spent_base.get(key,ZERO))
        base_charge=min(base_net,remaining_base)
        cap_relief_base=base_net-base_charge
        cap_discount=min(cap_relief_base,max(ZERO,payable-transfer))
        charge=payable-transfer-cap_discount
        spent_pay[key]=spent_pay.get(key,ZERO)+charge
        spent_base[key]=spent_base.get(key,ZERO)+base_charge
        if charge>0:anchor[key]=row
        # 4) 影子口径：票种实付统一基数（仅展示，不落账）
        prev_alt=alt_anchor.get(key);eligible_alt=False
        if prev_alt:
            delta=Decimal(str((instant(row["at"])-instant(prev_alt["at"])).total_seconds()))/60
            eligible_alt=prev_alt["route"]!=row["route"] and Decimal(0)<=delta<window
        alt_entitlement=min(payable,off) if eligible_alt else ZERO
        alt_remaining=max(ZERO,cap-alt_spent.get(key,ZERO))
        alt_charge=min(payable-alt_entitlement,alt_remaining)
        alt_cap_discount=payable-alt_entitlement-alt_charge
        alt_spent[key]=alt_spent.get(key,ZERO)+alt_charge
        if alt_charge>0:alt_anchor[key]=row
        # 守恒断言：票种实付 = 应收 + 换乘减免 + 封顶减免；优惠补贴不超实付
        if payable!=charge+transfer+cap_discount:raise DomainError("CONSERVATION","票种实付分币不守恒")
        if transfer+cap_discount>payable:raise DomainError("SUBSIDY_EXCEEDED","清分补贴超过本程票种实付")
        day_meta[key]["legs"]+=1
        good.append({**row,"basis":"普通票价基数(权益)/票种实付基数(应收)","transfer_anchor":previous["event_id"] if eligible else "—",
                     "transfer_entitlement":money(entitlement),"transfer_discount":money(transfer),"transfer_forfeited":money(forfeited),
                     "cap_remaining":money(remaining_base),"cap_discount":money(cap_discount),
                     "expected":money(charge),"day_paid":money(spent_pay[key]),
                     "alt_transfer_discount":money(alt_entitlement),"alt_cap_remaining":money(alt_remaining),"alt_cap_discount":money(alt_cap_discount),
                     "alt_expected":money(alt_charge),"alt_day_paid":money(alt_spent[key]),
                     "basis_diff":money(charge-alt_charge)})
    # 每张卡每个业务日唯一应收（双口径对照）
    day_accounts=[]
    for key in day_order:
        card,day=key
        day_accounts.append({"card":card,"business_day":day,"legs":day_meta[key]["legs"],
                             "basis":"权益=普通票价基数；应收/补贴=票种实付基数",
                             "receivable":money(spent_pay[key]),"cap_remaining_base":money(max(ZERO,cap-spent_base[key])),
                             "alt_receivable":money(alt_spent[key]),"alt_cap_remaining":money(max(ZERO,cap-alt_spent[key])),
                             "diff":money(spent_pay[key]-alt_spent[key])})
    metrics={"expected_total":money(sum((number(r["expected"]) for r in good),ZERO)),
             "alt_expected_total":money(sum((number(r["alt_expected"]) for r in good),ZERO)),
             "daily_caps":len(day_accounts),"transfer_hits":sum(r["transfer_anchor"]!="—" for r in good),
             "subsidy_capped_rows":sum(number(r["transfer_forfeited"])>0 for r in good),
             "day_accounts":day_accounts}
    return {"rows":good,"quarantine":[],"metrics":metrics}
