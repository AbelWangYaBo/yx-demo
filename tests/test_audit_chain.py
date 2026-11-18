"""审计日志链测试：追加写、哈希链、篡改检测。"""
import pytest


def test_record_audit_chains_hashes(session):
    from app.services.audit import record_audit

    l1 = record_audit(session, "测试员", "create", "student", "S001", {"name": "学员甲"})
    l2 = record_audit(session, "测试员", "update", "student", "S001", {"name": "学员乙"})
    assert l1.hash != l2.hash
    assert l2.prev_hash == l1.hash


def test_verify_chain_ok(session):
    from app.services.audit import record_audit, verify_chain

    for i in range(5):
        record_audit(session, "测试员", "create", "student", f"S{i:03d}", {"i": i})
    result = verify_chain(session)
    assert result["valid"] is True
    assert result["checked"] == 5
    assert result["broken_at"] is None


def test_tamper_detection(session):
    from sqlalchemy import update

    from app.models.audit_log import AuditLog
    from app.services.audit import record_audit, verify_chain

    for i in range(3):
        record_audit(session, "测试员", "create", "payment", f"P{i:03d}", {"amount": i})

    # 模拟绕过审计服务直接改库（伪造 payload 不改 hash）
    session.execute(
        update(AuditLog).where(AuditLog.entity_id == "P001").values(payload={"amount": 99999})
    )
    session.commit()
    result = verify_chain(session)
    assert result["valid"] is False
    assert result["broken_at"] is not None


def test_no_update_or_delete_endpoints_on_audit(client):
    # 审计接口只读：PUT/DELETE 必须是 405
    assert client.put("/api/audit/1", json={}).status_code == 405
    assert client.delete("/api/audit/1").status_code == 405
