"""Opportunity workflow smoke test — run against localhost:8000."""
import sys

import httpx

BASE = "http://localhost:8000"

# trust_env=False：忽略系统/环境代理，直连本机后端
client = httpx.Client(base_url=BASE, trust_env=False, timeout=30)


def main() -> None:
    ok = fail = 0

    def check(name: str, cond: bool, detail: str = "") -> None:
        nonlocal ok, fail
        if cond:
            ok += 1
            print(f"PASS {name}")
        else:
            fail += 1
            print(f"FAIL {name} :: {detail}")

    # 0. 动态选一个簇（rebuild 会重建 ID，不能硬编码）
    clusters = client.get("/clusters").json()
    if not clusters:
        print("SKIP: no clusters — run POST /clusters/rebuild first")
        sys.exit(1)
    cid = clusters[0]["id"]
    print(f"using cluster #{cid}: {clusters[0]['name']}")

    # 1. list
    r = client.get("/opportunities")
    check("GET /opportunities", r.status_code == 200, f"{r.status_code} {r.text[:100]}")

    # 2. create for picked cluster（409 则复用已有记录，保证脚本可重跑）
    r = client.post(
        "/opportunities",
        json={
            "cluster_id": cid,
            "title": "平台静默行为聚合提醒工具",
            "problem_statement": "多个用户报告平台存在未经授权的静默行为",
            "target_customer": "重度 SaaS 工具使用者",
            "proposed_solution": "浏览器插件聚合并标记平台的静默行为",
        },
    )
    if r.status_code == 409:
        print("SKIP create (already exists) — reusing")
        opp = next(
            o for o in client.get("/opportunities").json()
            if o["cluster_id"] == cid
        )
    elif r.status_code == 200:
        opp = r.json()
        check("create status=DISCOVERED", opp["validation_status"] == "DISCOVERED", str(opp))
        check("market_score field present", "market_score" in opp, str(opp.get("market_score")))
    else:
        check("create", False, f"{r.status_code} {r.text[:200]}")
        return

    oid = opp["id"]

    # 3. duplicate → 409
    r = client.post("/opportunities", json={"cluster_id": cid, "title": "dup"})
    check("duplicate 409", r.status_code == 409, f"{r.status_code} {r.text[:100]}")

    # 4. valid transition → EVIDENCE_GATHERING
    r = client.patch(f"/opportunities/{oid}/status", json={"new_status": "EVIDENCE_GATHERING"})
    check(
        "valid transition",
        r.status_code == 200 and r.json()["validation_status"] == "EVIDENCE_GATHERING",
        f"{r.status_code} {r.text[:150]}",
    )

    # 5. invalid jump → PAID → 422
    r = client.patch(f"/opportunities/{oid}/status", json={"new_status": "PAID"})
    check("invalid jump 422", r.status_code == 422, f"{r.status_code} {r.text[:150]}")

    # 6. reject without note → 422
    r = client.patch(f"/opportunities/{oid}/status", json={"new_status": "REJECTED"})
    check("reject w/o note 422", r.status_code == 422, f"{r.status_code} {r.text[:150]}")

    # 7. reject with note → 200 + note saved
    r = client.patch(
        f"/opportunities/{oid}/status",
        json={"new_status": "REJECTED", "note": "单源信号，等待交叉验证"},
    )
    check(
        "reject with note",
        r.status_code == 200 and r.json()["validation_status"] == "REJECTED",
        f"{r.status_code} {r.text[:150]}",
    )
    check("rejection_note saved", bool(r.json().get("rejection_note")), str(r.json().get("rejection_note")))

    # 8. REJECTED 是终态，再流转应拒绝
    r = client.patch(f"/opportunities/{oid}/status", json={"new_status": "DORMANT"})
    check("REJECTED is terminal 422", r.status_code == 422, f"{r.status_code} {r.text[:150]}")

    # 9. evidence-pack markdown
    r = client.get(f"/clusters/{cid}/evidence-pack")
    check("evidence-pack 200", r.status_code == 200, str(r.status_code))
    check("evidence-pack is brief", "需求决策简报" in r.text, r.text[:80])

    # 10. LLM draft（真实调用一次，验证端到端）
    r = client.post("/opportunities/draft", json={"cluster_id": cid}, timeout=90)
    check("draft 200", r.status_code == 200, f"{r.status_code} {r.text[:150]}")
    if r.status_code == 200:
        d = r.json()
        check(
            "draft fields filled",
            all(d.get(k) for k in ("problem_statement", "target_customer", "proposed_solution")),
            str(d)[:200],
        )

    print(f"\n{ok} passed, {fail} failed")
    sys.exit(1 if fail else 0)


main()
