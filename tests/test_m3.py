from app.modules.m3_fares.rules import evaluate,select_fare,FARES
from app.values import instant,number
from app.errors import DomainError
import pytest
def test_real_fare_version(result): assert result["stages"][2]["rows"][0]["fare_version"]=="F2"
def test_new_version_boundary():
    "TRAP-23"
    assert select_fare(instant("2026-11-01T00:00:00+08:00"),FARES)["amount"]=="2.50"
def test_timezone_equal():
    "TRAP-11"
    assert select_fare(instant("2026-10-31T16:00:00Z"),FARES)["version"]=="F2"
def test_overlap_rejected():
    "TRAP-25"
    with pytest.raises(DomainError):select_fare(instant("2026-11-16T00:00:00Z"),FARES+[FARES[1]])
def test_thousands_and_fullwidth():
    "TRAP-06"
    assert number("１,２３４.５０")==number("1234.50")
def test_real_sentinel_quarantined(result):
    "TRAP-07"
    assert any(r["reason"]=="EMPTY_VALUE" for r in result["stages"][2]["quarantine"])
def test_naive_time_rejected():
    r=evaluate([{"event_time":"2026-11-16T08:00:00","reported":"2","ticket_type":"普通"}],{})
    assert r["quarantine"][0]["reason"]=="INVALID_TIME"
def fare_row(ticket="普通",reported="2.50",at="2026-11-16T08:00:00+08:00"):
    return {"event_time":at,"reported":reported,"ticket_type":ticket,"event_id":"1","card":"c","route":"01"}
def test_ticket_payable_derived():
    rows=evaluate([fare_row("普通"),fare_row("学生"),fare_row("老年")],{})["rows"]
    assert [(r["ticket_type"],r["payable_fare"],r["ticket_rate"]) for r in rows]==[("普通","2.50","1.00"),("学生","1.25","0.50"),("老年","0.50","0.20")]
def test_unknown_ticket_quarantined():
    r=evaluate([fare_row("优待")],{})
    assert r["quarantine"][0]["reason"]=="UNKNOWN_TICKET"
def test_blank_ticket_quarantined():
    r=evaluate([fare_row("")],{})
    assert r["quarantine"][0]["reason"]=="EMPTY_VALUE"
def test_ticket_rate_override_param():
    r=evaluate([fare_row("儿童")],{"parameters":{"ticket_rates":{"儿童":"0.80"}}})["rows"]
    assert r[0]["payable_fare"]=="2.00" and r[0]["ticket_type"]=="儿童"
def test_real_sample_tickets_seen(result):
    assert set(result["stages"][2]["metrics"]["tickets"])=={"普通","学生","老年"}
