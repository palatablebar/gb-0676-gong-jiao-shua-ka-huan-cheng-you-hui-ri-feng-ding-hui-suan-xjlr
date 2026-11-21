from app.modules.m5_discounts.rules import evaluate
from app.errors import DomainError
from decimal import Decimal
import pytest
def ride(id,minute,route="01",base="2.50",payable=None):
    return {"event_id":str(id),"card":"0001","business_day":"2026-11-16","at":f"2026-11-16T{8+minute//60:02d}:{minute%60:02d}:00Z","route":route,"base_fare":base,"payable_fare":payable or base}
def test_real_day_cap(result):
    m=result["stages"][4]["metrics"]
    assert m["expected_total"]=="38.25" and m["alt_expected_total"]=="40.00"
def test_exact_window_excluded():
    "TRAP-23 半开换乘窗"
    r=evaluate([ride(1,0),ride(2,60,"02")],{})["rows"];assert r[1]["transfer_discount"]=="0.00"
def test_within_window_discount(): assert evaluate([ride(1,0),ride(2,59,"02")],{})["rows"][1]["expected"]=="1.50"
def test_same_route_no_transfer(): assert evaluate([ride(1,0),ride(2,10)],{})["rows"][1]["expected"]=="2.50"
def test_zero_paid_not_anchor():
    r=evaluate([ride(1,0,base="1"),ride(2,30,"02",base="1"),ride(3,61,"03",base="1")],{})["rows"]
    assert r[1]["expected"]=="0.00" and r[2]["transfer_discount"]=="0.00"
def test_discount_before_cap_conservation():
    "TRAP-10 Decimal守恒"
    r=evaluate([ride(1,0),ride(2,10,"02"),ride(3,20,"03"),ride(4,90)],{})["rows"]
    assert sum(Decimal(x["expected"]) for x in r)==Decimal("6")
    assert all(Decimal(x["base_fare"])==Decimal(x["expected"])+Decimal(x["transfer_discount"])+Decimal(x["cap_discount"]) for x in r)
def test_negative_parameter_rejected():
    with pytest.raises(DomainError):evaluate([],{"parameters":{"daily_cap":"-1"}})
def test_input_order_invariant():
    rows=[ride(1,0),ride(2,10,"02")];assert evaluate(rows,{})["rows"]==evaluate(list(reversed(rows)),{})["rows"]
# ---- 票种基数裁决（docs/RULING.md） ----
def student(id,minute,route="01"):
    return {"event_id":str(id),"card":"S1","business_day":"2026-11-16",
            "at":f"2026-11-16T{8+minute//60:02d}:{minute%60:02d}:00Z","route":route,
            "base_fare":"2.50","payable_fare":"1.25","ticket_type":"学生"}
def elderly(id,minute,route="01"):
    return {"event_id":str(id),"card":"E1","business_day":"2026-11-16",
            "at":f"2026-11-16T{8+minute//60:02d}:{minute%60:02d}:00Z","route":route,
            "base_fare":"2.50","payable_fare":"0.50","ticket_type":"老年"}
def test_student_transfer_entitlement_on_ordinary_base():
    "权益按普通票价基数：1元换乘资格不缩水"
    r=evaluate([student(1,0),student(2,15,"02")],{})["rows"]
    assert r[1]["transfer_entitlement"]=="1.00"
    assert r[1]["transfer_discount"]=="1.00" and r[1]["transfer_forfeited"]=="0.00"
def test_elderly_discount_never_exceeds_payable():
    "老年实付0.50：固定1元减免被实付封顶，不产生负应收、不放大补贴"
    r=evaluate([elderly(1,0),elderly(2,15,"02"),elderly(3,30,"03")],{})["rows"]
    assert all(Decimal(x["transfer_discount"])+Decimal(x["cap_discount"])<=Decimal(x["payable_fare"]) for x in r)
    assert r[1]["transfer_entitlement"]=="1.00" and r[1]["transfer_discount"]=="0.50"
    assert r[1]["transfer_forfeited"]=="0.50" and r[1]["expected"]=="0.00"
def test_student_two_bases_diverge_and_unique_receivable():
    "同一学生卡连续短途：双口径应收、封顶余量不同，但唯一应收只有一个"
    out=evaluate([student(1,0),student(2,15,"02"),student(3,30,"03"),student(4,110)],{})
    r=out["rows"];day=out["metrics"]["day_accounts"][0]
    assert day["receivable"]=="1.75" and day["alt_receivable"]=="3.00" and day["diff"]=="-1.25"
    assert day["cap_remaining_base"]=="0.00" and day["alt_cap_remaining"]=="3.00"
    assert sum(Decimal(x["expected"]) for x in r)==Decimal(day["receivable"])
    assert len(out["metrics"]["day_accounts"])==1
def test_leg_conservation_for_every_ticket():
    rows=[student(1,0),student(2,15,"02"),elderly(3,40),elderly(4,55,"02")]
    for x in evaluate(rows,{})["rows"]:
        p=Decimal(x["payable_fare"])
        assert p==Decimal(x["expected"])+Decimal(x["transfer_discount"])+Decimal(x["cap_discount"])
def test_basis_fields_exposed():
    r=evaluate([student(1,0),student(2,15,"02")],{})["rows"][1]
    for field in ("basis","alt_expected","alt_day_paid","alt_cap_remaining","basis_diff","cap_remaining"):
        assert field in r
