from aidalloc.audit import append_record, verify_log


def test_audit_log_hash_chain(tmp_path):
    path = tmp_path / "audit.jsonl"
    append_record(path, {"run": 1, "metric": 0.5})
    append_record(path, {"run": 2, "metric": 0.7})
    result = verify_log(path)
    assert result["exists"] is True
    assert result["records"] == 2
    assert result["valid"] is True
