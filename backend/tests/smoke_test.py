from io import BytesIO
from pathlib import Path
import sys
import time

from docx import Document
from fastapi.testclient import TestClient

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.main import app


def make_docx(lines: list[str]) -> bytes:
    doc = Document()
    for line in lines:
        doc.add_paragraph(line)
    output = BytesIO()
    doc.save(output)
    output.seek(0)
    return output.getvalue()


def run() -> None:
    with TestClient(app) as client:
        a_doc = make_docx(
            [
                "第一章 项目概述。本项目建设智慧园区综合管理平台，采用统一数据底座。",
                "技术方案采用微服务架构，支持身份认证、权限管理和日志审计。",
                "实施团队将提供培训、验收和运维支持。",
            ]
        )
        b1_doc = make_docx(
            [
                "第一章 项目概述。本项目建设智慧园区综合管理平台，采用统一数据底座。",
                "技术方案采用微服务架构，支持身份认证、权限管理和日志审计。",
                "售后团队提供培训和运维支持。",
            ]
        )
        b2_doc = make_docx(
            [
                "本项目提供办公用品采购与配送服务。",
                "配送团队保证及时响应和库存管理。",
            ]
        )
        created = client.post(
            "/api/tasks",
            files=[
                ("a_file", ("A.docx", a_doc, "application/vnd.openxmlformats-officedocument.wordprocessingml.document")),
                ("b_files", ("B1.docx", b1_doc, "application/vnd.openxmlformats-officedocument.wordprocessingml.document")),
                ("b_files", ("B2.docx", b2_doc, "application/vnd.openxmlformats-officedocument.wordprocessingml.document")),
            ],
            data={"keywords": "微服务,运维"},
        )
        assert created.status_code == 200, created.text
        task_no = created.json()["data"]["task_no"]
        status = wait_until_done(client, task_no)
        assert status["status"] in {"awaiting_payment", "completed"}, status

        summary = client.get(f"/api/tasks/{task_no}/summary").json()["data"]
        assert summary["mode"] == "multi"
        assert summary["payment_required"] is True
        assert summary["results"][0]["total_similarity"] > 0.8
        compare_id = summary["results"][0]["compare_result_id"]

        preview = client.get(f"/api/tasks/{task_no}/results/{compare_id}/preview").json()["data"]
        assert len(preview["segments"]) > 0

        locked = client.get(f"/api/tasks/{task_no}/results/{compare_id}/detail")
        assert locked.status_code == 402

        order = client.post("/api/orders", json={"task_no": task_no, "contact": "user@example.com"}).json()["data"]
        login = client.post("/api/admin/login", json={"username": "admin", "password": "admin123"}).json()["data"]
        paid = client.post(
            f"/api/admin/orders/{order['order_no']}/mark-paid",
            headers={"Authorization": f"Bearer {login['token']}"},
        ).json()["data"]
        assert paid["status"] == "paid"

        detail = client.get(f"/api/tasks/{task_no}/results/{compare_id}/detail").json()["data"]
        assert len(detail["matches"]) > 0
        assert len(detail["keyword_hits"]) > 0

        configured = client.put(
            "/api/admin/settings",
            json={"free_b_file_limit": 2},
            headers={"Authorization": f"Bearer {login['token']}"},
        )
        assert configured.status_code == 200, configured.text
        assert configured.json()["data"]["free_b_file_limit"] == 2

        free_multi = client.post(
            "/api/tasks",
            files=[
                ("a_file", ("A-free.docx", a_doc, "application/vnd.openxmlformats-officedocument.wordprocessingml.document")),
                ("b_files", ("B1-free.docx", b1_doc, "application/vnd.openxmlformats-officedocument.wordprocessingml.document")),
                ("b_files", ("B2-free.docx", b2_doc, "application/vnd.openxmlformats-officedocument.wordprocessingml.document")),
            ],
        )
        assert free_multi.status_code == 200, free_multi.text
        free_task_no = free_multi.json()["data"]["task_no"]
        free_status = wait_until_done(client, free_task_no)
        assert free_status["status"] == "completed", free_status
        free_summary = client.get(f"/api/tasks/{free_task_no}/summary").json()["data"]
        assert free_summary["mode"] == "multi"
        assert free_summary["payment_required"] is False
        free_compare_id = free_summary["results"][0]["compare_result_id"]
        free_detail = client.get(f"/api/tasks/{free_task_no}/results/{free_compare_id}/detail")
        assert free_detail.status_code == 200, free_detail.text
        free_order = client.post("/api/orders", json={"task_no": free_task_no, "contact": "user@example.com"})
        assert free_order.status_code == 400, free_order.text
        print({"task_no": task_no, "compare_result_id": compare_id, "matches": len(detail["matches"])})


def wait_until_done(client: TestClient, task_no: str) -> dict:
    for _ in range(30):
        payload = client.get(f"/api/tasks/{task_no}/status").json()["data"]
        if payload["status"] in {"awaiting_payment", "completed", "failed"}:
            return payload
        time.sleep(0.2)
    raise AssertionError(f"Task {task_no} did not finish in time")


if __name__ == "__main__":
    run()
