from app.modules.m7_settlement.rules import evaluate
from app.errors import DomainError
import pytest
def test_real_sample_archive_ready(result): assert result["stages"][6]["metrics"]["ready"] is True
def test_real_sample_archive_source_count(result): assert result["stages"][6]["metrics"]["source_lines"]==result["stages"][5]["metrics"]["accepted_inputs"]
def test_real_sample_seal_stable(result):
    rows=result["stages"][5]["rows"];assert evaluate(rows,{})["metrics"]["sha256"]==evaluate(rows,{})["metrics"]["sha256"]
def test_unbalanced_blocked():
    with pytest.raises(DomainError) as e:evaluate([],{"reconcile":{"metrics":{"balanced":False}}})
    assert e.value.code=="UNBALANCED"
def test_duplicate_archive_key():
    with pytest.raises(DomainError):evaluate([{"event_id":"1"},{"event_id":"1"}],{})
def test_real_sample_manifest_has_hash(result): assert len(result["manifest"]["input_sha256"])==64
def test_real_sample_export_rows_match(result): assert result["stages"][6]["rows"]==result["stages"][5]["rows"]
def test_subsidy_overrun_blocks_seal():
    rows=[{"event_id":"1","subsidy_within_payable":False}]
    with pytest.raises(DomainError) as e:evaluate(rows,{})
    assert e.value.code=="UNBALANCED"
def test_duplicate_card_day_blocks_seal():
    ctx={"m5":{"metrics":{"day_accounts":[{"card":"S1","business_day":"2026-11-16"},{"card":"S1","business_day":"2026-11-16"}]}}}
    with pytest.raises(DomainError) as e:evaluate([],ctx)
    assert e.value.code=="DUPLICATE_CARD_DAY"
