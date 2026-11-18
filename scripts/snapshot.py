"""导出静态演示快照到 frontend/api-snapshot/（GitHub Pages 只读模式用）。

遍历全部只读 API，把当前数据库的演示数据 dump 成 JSON；前端在检测不到
后端时（如 GitHub Pages）自动回退加载这些快照，浏览完整、写入只读提示。

用法：uv run python scripts/snapshot.py（在 seed 之后执行）
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from fastapi.testclient import TestClient  # noqa: E402

from app.main import app  # noqa: E402

OUT_DIR = Path(__file__).resolve().parent.parent / "frontend" / "api-snapshot"

# (请求URL, 输出文件名)
SNAPSHOTS = [
    ("/api/compliance/overview", "overview.json"),
    ("/api/students/paged?page=1&size=50", "students.json"),
    ("/api/students", "students-all.json"),
    ("/api/students/STU-2027-101/records", "student-STU-2027-101.json"),
    ("/api/students/STU-2027-102/records", "student-STU-2027-102.json"),
    ("/api/students/STU-2027-103/records", "student-STU-2027-103.json"),
    ("/api/students/STU-2027-104/records", "student-STU-2027-104.json"),
    ("/api/students/STU-2027-105/records", "student-STU-2027-105.json"),
    ("/api/schools", "schools.json"),
    ("/api/courses", "courses.json"),
    ("/api/programs", "programs.json"),
    ("/api/contracts", "contracts.json"),
    ("/api/payments", "payments.json"),
    ("/api/quotations", "quotations.json"),
    ("/api/audit?limit=200", "audit.json"),
    ("/api/audit/verify", "audit-verify.json"),
    ("/api/access-logs?limit=200", "access-logs.json"),
    ("/api/agency", "agency.json"),
    ("/api/meta/retention", "meta-retention.json"),
]


def main() -> None:
    client = TestClient(app)
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    for url, filename in SNAPSHOTS:
        resp = client.get(url)
        resp.raise_for_status()
        (OUT_DIR / filename).write_text(
            json.dumps(resp.json(), ensure_ascii=False, indent=1), encoding="utf-8"
        )
        print(f"  {filename} <- {url}")
    # Jekyll 会忽略部分文件，占位确保 Pages 按原样分发
    (OUT_DIR.parent / ".nojekyll").write_text("", encoding="utf-8")
    print(f"快照完成：{len(SNAPSHOTS)} 个文件 → {OUT_DIR}")


if __name__ == "__main__":
    main()
