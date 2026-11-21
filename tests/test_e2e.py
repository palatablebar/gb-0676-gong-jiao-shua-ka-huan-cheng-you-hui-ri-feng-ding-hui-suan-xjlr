import csv,io
from app.pipeline import execute,load_sample
from app import store
def test_full_sample_flow(client):
    r=client.post("/api/runs",json={"sample":"dirty.csv"});assert r.status_code==200
    p=r.get_json();assert len(p["stages"])==7
    assert p["stages"][5]["metrics"]["balanced"] is True
def test_idempotent_real_input(sample):
    a=execute(sample);b=execute(sample)
    assert a["run_id"]==b["run_id"] and len(store.history())==1
def test_stale_review_409(client):
    "TRAP-26 陈旧复核不得覆盖新版本"
    p=client.post("/api/runs",json={"sample":"dirty.csv"}).get_json();u="/api/runs/"+p["run_id"]+"/review"
    assert client.post(u,json={"version":1,"decision":"已复核"}).status_code==200
    assert client.post(u,json={"version":1,"decision":"退回复核"}).status_code==409
def test_export_has_manifest_and_quarantine(client):
    p=client.post("/api/runs",json={"sample":"dirty.csv"}).get_json()
    r=client.get("/api/runs/"+p["run_id"]+"/archive")
    rows=list(csv.reader(io.StringIO(r.data.decode("utf-8-sig"))))
    assert rows[0][1]=="input_sha256" and any(x[3]=="quarantine" for x in rows[1:])
def test_failed_import_is_atomic(client):
    assert client.post("/api/runs",json={"csv":"bad"}).status_code==422
    assert store.history()==[]
def test_module_entrances(client):
    from app.config import MODULES
    for slug,name in MODULES:
        assert client.get("/api/"+slug).status_code==200
        assert client.get("/"+slug).status_code==200
def test_missing_run_404(client): assert client.get("/api/runs/missing").status_code==404
def test_rerun_does_not_double_quota(sample):
    "同批重跑幂等：同一run_id、唯一一条批次，卡日应收不重复占额"
    a=execute(sample);b=execute(sample)
    assert a["run_id"]==b["run_id"]
    assert len(store.history())==1
    days_a=a["stages"][4]["metrics"]["day_accounts"];days_b=b["stages"][4]["metrics"]["day_accounts"]
    assert days_a==days_b and len({(d["card"],d["business_day"]) for d in days_a})==len(days_a)
def test_unconfirmed_ticket_keeps_published_ledger(client):
    "票种无法确认的行被隔离，已发布日账不受影响，对账不平不得封存由规则版本与批次保证"
    p=client.post("/api/runs",json={"sample":"dirty.csv"}).get_json()
    reasons=[q["reason"] for q in p["stages"][6]["cumulative_quarantine"]]
    assert "UNKNOWN_TICKET" in reasons and "EMPTY_VALUE" in reasons
    # 已发布批次可重复读取且封存状态保持
    rid=p["run_id"]
    again=client.post("/api/runs",json={"sample":"dirty.csv"}).get_json()
    assert again["run_id"]==rid and again["stages"][6]["metrics"]["ready"] is True
    assert client.get("/api/runs/"+rid).status_code==200
def test_ticket_type_unknown_quarantined_not_billed(client):
    header="event_id,card,route,event_time,result,reported,ticket_type,note\n"
    csv=header+"1,0001,01,2026-11-16T08:00:00+08:00,success,2.50,优待,x\n"
    p=client.post("/api/runs",json={"csv":csv}).get_json()
    assert p["stages"][2]["quarantine"][0]["reason"]=="UNKNOWN_TICKET"
    assert p["stages"][4]["rows"]==[]
    assert p["stages"][5]["metrics"]["balanced"] is True
