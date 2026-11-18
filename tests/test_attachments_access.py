"""附件上传/下载 + 访问日志 + 学员分页搜索测试。"""


def _mk_student(session, no, name="学员甲（虚构）", birth="2012-05-01"):
    from app.services import crud_helpers as ch

    return ch.create_student(session, {"student_no": no, "name": name, "birth_date": birth})


def test_upload_and_download_attachment(client, session):
    r = client.post("/api/attachments", files={"file": ("护照扫描件.txt", b"FAKE-PASSPORT-CONTENT", "text/plain")})
    assert r.status_code == 201
    att = r.json()
    assert att["id"] and att["filename"] == "护照扫描件.txt"

    d = client.get(f"/api/attachments/{att['id']}/download")
    assert d.status_code == 200
    assert b"FAKE-PASSPORT-CONTENT" in d.content

    # 上传写审计
    audit = client.get("/api/audit").json()["items"]
    assert any(a["entity"] == "attachment" and a["action"] == "create" for a in audit)
    # 下载写访问日志（内部记录，非审计）
    logs = client.get("/api/access-logs").json()
    assert any(l["access_type"] == "DOWNLOAD_FILE" and l["target"] == str(att["id"]) for l in logs)
    # 访问日志不进哈希链，链仍完整
    assert client.get("/api/audit/verify").json()["valid"] is True


def test_oversized_attachment_rejected(client):
    big = b"x" * (10 * 1024 * 1024 + 1)
    r = client.post("/api/attachments", files={"file": ("big.bin", big, "application/octet-stream")})
    assert r.status_code == 413


def test_view_student_records_writes_access_log(client, session):
    s = _mk_student(session, "STU-VIEW-001")
    client.get(f"/api/students/{s.student_no}/records")
    logs = client.get("/api/access-logs").json()
    assert any(l["access_type"] == "VIEW_STUDENT" and l["target"] == s.student_no for l in logs)

    # 按学员过滤访问记录
    r = client.get(f"/api/access-logs?student_no={s.student_no}")
    assert all(
        l["target"] == s.student_no or (l["detail"] or {}).get("student_no") == s.student_no
        for l in r.json()
    )


def test_students_paged_keyword_search(client, session):
    _mk_student(session, "STU-P-001", name="学员甲（虚构）")
    _mk_student(session, "STU-P-002", name="学员乙（虚构）")
    _mk_student(session, "STU-P-003", name="学员丙（虚构）")

    r = client.get("/api/students/paged?page=1&size=2")
    body = r.json()
    assert body["total"] >= 3 and len(body["items"]) == 2

    r2 = client.get("/api/students/paged?keyword=学员乙")
    assert r2.json()["total"] == 1 and r2.json()["items"][0]["student_no"] == "STU-P-002"

    r3 = client.get("/api/students/paged?keyword=STU-P-003")
    assert r3.json()["total"] == 1 and r3.json()["items"][0]["student_no"] == "STU-P-003"


def test_document_linked_attachment_in_aggregation(client, session):
    s = _mk_student(session, "STU-ATT-001")
    att = client.post(
        "/api/attachments",
        files={"file": ("报名表扫描件.txt", b"FORM-CONTENT", "text/plain")},
    ).json()
    r = client.post("/api/documents", json={
        "student_id": s.id, "doc_type": "报名表", "doc_no": "APP-001",
        "attachment_id": att["id"],
    })
    assert r.status_code == 201
    data = client.get(f"/api/students/{s.student_no}/records").json()
    assert data["documents"][0]["attachment_id"] == att["id"]
    assert data["documents"][0]["attachment_filename"] == "报名表扫描件.txt"
