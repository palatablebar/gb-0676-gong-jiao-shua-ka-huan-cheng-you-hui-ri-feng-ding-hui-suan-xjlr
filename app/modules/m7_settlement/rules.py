import hashlib,json
from decimal import Decimal
from app.errors import DomainError
from app.reasons import sources
def evaluate(rows,context):
    stages=[v for v in context.values() if isinstance(v,dict) and "metrics" in v]
    balances=[s["metrics"]["balanced"] for s in stages if "balanced" in s["metrics"]]
    if balances and not all(balances): raise DomainError("UNBALANCED","来源行未对平，不能归档")
    ids=[str(r.get("event_id",r.get("_line",""))) for r in rows]
    if len(ids)!=len(set(ids)): raise DomainError("ARCHIVE_DUPLICATE","归档业务键重复")
    # 每张卡每个业务日只能形成唯一应收：卡日账不得重复登记
    day_accounts=[a for s in stages for a in s.get("metrics",{}).get("day_accounts",[]) if isinstance(a,dict)]
    day_keys=[(a.get("card"),a.get("business_day")) for a in day_accounts]
    if len(day_keys)!=len(set(day_keys)): raise DomainError("DUPLICATE_CARD_DAY","卡日唯一应收重复登记")
    if any(not r.get("subsidy_within_payable",True) for r in rows): raise DomainError("UNBALANCED","清分补贴超过本程票种实付，不能归档")
    encoded=json.dumps(rows,ensure_ascii=False,sort_keys=True,default=str).encode()
    return {"rows":rows,"quarantine":[],"metrics":{"records":len(rows),"source_lines":len(set(x for row in rows for x in sources(row))),"sha256":hashlib.sha256(encoded).hexdigest(),"ready":True,"differences":sum(r.get("status")=="差异" for r in rows)}}
