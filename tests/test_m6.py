from app.modules.m6_clearing.rules import evaluate
from decimal import Decimal
def test_real_sample_four_books(result): assert result["stages"][5]["metrics"]["balanced"] is True
def test_real_sample_final_lineage(result):
    m=result["stages"][5]["metrics"];assert m["accepted_inputs"]+m["quarantine_inputs"]+m["excluded"]==m["input"]
def test_real_sample_difference_is_explicit(result):
    rows=result["stages"][5]["rows"];assert any(r["status"]=="差异" for r in rows)
def test_real_sample_totals_exact(result):
    rows=result["stages"][5]["rows"];m=result["stages"][5]["metrics"]
    assert sum((Decimal(r["difference"]) for r in rows),Decimal(0))==Decimal(m["expected_total"])-Decimal(m["reported_total"])
def test_empty_reconcile():
    r=evaluate([],{});assert r["metrics"]["balanced"] is True and r["metrics"]["expected_total"]=="0"
def test_overlap_is_rejected():
    import pytest
    from app.errors import DomainError
    with pytest.raises(DomainError):evaluate([{"_line":1}],{"quarantine":[{"_line":1}]})
def test_real_sample_rejected_have_reason(result):
    assert all(r["reason"] and r["detail"] for r in result["stages"][5]["cumulative_quarantine"])
def test_real_sample_subsidy_split_balances(result):
    m=result["stages"][5]["metrics"]
    assert Decimal(m["subsidy_total"])==Decimal(m["fare_subsidy_total"])+Decimal(m["discount_subsidy_total"])
def test_real_sample_discount_subsidy_within_payable(result):
    rows=result["stages"][5]["rows"]
    assert all(r["subsidy_within_payable"] is True for r in rows)
    assert all(Decimal(r["discount_subsidy"])<=Decimal(r["payable_fare"]) for r in rows)
def test_real_sample_double_identity(result):
    for r in result["stages"][5]["rows"]:
        e=Decimal(r["expected"]);b=Decimal(r["base_fare"]);p=Decimal(r["payable_fare"])
        assert b==e+Decimal(r["fare_subsidy"])+Decimal(r["discount_subsidy"])
        assert p==e+Decimal(r["transfer_discount"])+Decimal(r["cap_discount"])
