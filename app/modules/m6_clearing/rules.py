from decimal import Decimal
from app.reasons import sources
from app.errors import DomainError
ZERO=Decimal(0)
def evaluate(rows,context):
    intake=context.get("intake")
    bad=context.get("quarantine",[])
    accepted=set(x for row in rows for x in sources(row))
    rejected=set(x for row in bad for x in sources(row))
    if accepted & rejected: raise DomainError("LINEAGE_OVERLAP","同一来源行被重复裁决")
    m={"accepted_inputs":len(accepted),"quarantine_inputs":len(rejected),"output_records":len(rows)}
    if intake:
        excluded=intake["duplicate"]+intake["blank"]+intake["repeated_headers"]
        m.update(input=intake["input"],excluded=excluded,balanced=intake["input"]==len(accepted)+len(rejected)+excluded)
    else:m.update(input=len(accepted)+len(rejected),excluded=0,balanced=True)
    output=[];subsidy_total=fare_subsidy_total=discount_subsidy_total=ZERO;balanced=m["balanced"]
    for row in rows:
        expected=Decimal(str(row.get("expected","0")));reported=Decimal(str(row.get("reported","0")))
        base=Decimal(str(row.get("base_fare","0")));payable=Decimal(str(row.get("payable_fare",base)))
        transfer=Decimal(str(row.get("transfer_discount","0")));cap_disc=Decimal(str(row.get("cap_discount","0")))
        # 清分补贴拆分：票种让利 + 优惠补贴；优惠补贴受票种实付硬约束
        fare_subsidy=base-payable
        discount_subsidy=transfer+cap_disc
        subsidy=fare_subsidy+discount_subsidy
        if discount_subsidy>payable:
            balanced=False
        # 双恒等：普通票价 = 应收 + 票种让利 + 优惠补贴；票种实付 = 应收 + 换乘减免 + 封顶减免
        if base!=expected+fare_subsidy+discount_subsidy or payable!=expected+transfer+cap_disc:
            balanced=False
        subsidy_total+=subsidy;fare_subsidy_total+=fare_subsidy;discount_subsidy_total+=discount_subsidy
        output.append({**row,"fare_subsidy":str(fare_subsidy),"discount_subsidy":str(discount_subsidy),
                       "subsidy":str(subsidy),"subsidy_within_payable":discount_subsidy<=payable,
                       "difference":str(expected-reported),"status":"通过" if expected==reported else "差异"})
    m.update(expected_total=str(sum((Decimal(str(r.get("expected","0"))) for r in rows),ZERO)),
             reported_total=str(sum((Decimal(str(r.get("reported","0"))) for r in rows),ZERO)),
             subsidy_total=str(subsidy_total),fare_subsidy_total=str(fare_subsidy_total),
             discount_subsidy_total=str(discount_subsidy_total),
             differences=sum(r["status"]=="差异" for r in output),balanced=balanced)
    return {"rows":output,"quarantine":[],"metrics":m}
