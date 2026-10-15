from __future__ import annotations

from collections import Counter, defaultdict
from pathlib import Path
import html
import json
import statistics

SUMMARY_PATH = Path("data/output/summary.json")
RESULTS_PATH = Path("data/output/results.json")
OUTPUT_PATH = Path("docs/index.html")


def pct(n: int | float, d: int | float) -> float:
    return 0.0 if not d else 100.0 * n / d


def money(v: float | None) -> str:
    if v is None:
        return "—"
    if abs(v) >= 1_000_000:
        return f"£{v / 1_000_000:.2f}m"
    if abs(v) >= 1_000:
        return f"£{v / 1_000:.1f}k"
    return f"£{v:,.2f}"


def titleize(value: str) -> str:
    return value.replace("_", " ").title()


def routing_reason(r: dict) -> str:
    errors = r.get("validation_errors") or []
    if r["decision"] == "reject":
        if "negative_amount" in errors:
            return "Hard fail: negative amount"
        if "invalid_date" in errors:
            return "Hard fail: invalid date"
        return "Hard validation fail"
    if errors:
        return "Validation hit: " + ", ".join(titleize(x) for x in errors)
    c = r["classification"]
    if c["priority"] == "high":
        return "High priority"
    if c["confidence"] < 0.80:
        return "Low confidence"
    return "Auto checks passed"


def bar_rows(counter: Counter, value_label=lambda v: str(v), max_value: float | None = None) -> str:
    if not counter:
        return '<div class="empty">No data</div>'
    m = max_value or max(counter.values()) or 1
    rows = []
    for key, value in counter.most_common():
        width = 100 * value / m
        rows.append(
            f'<div class="barrow"><span>{html.escape(titleize(str(key)))}</span>'
            f'<div class="track"><div class="fill" style="width:{width:.2f}%"></div></div>'
            f'<b>{html.escape(value_label(value))}</b></div>'
        )
    return "".join(rows)


def build() -> str:
    s = json.loads(SUMMARY_PATH.read_text())
    results = json.loads(RESULTS_PATH.read_text())

    docs = len(results)
    decisions = Counter(r["decision"] for r in results)
    doc_types = Counter(r["extracted"]["document_type"] for r in results)
    categories = Counter(r["classification"]["category"] for r in results)
    priorities = Counter(r["classification"]["priority"] for r in results)
    validation = Counter(e for r in results for e in r.get("validation_errors", []))
    reasons = Counter(routing_reason(r) for r in results if r["decision"] != "auto_process")

    amounts = [r["extracted"]["amount_gbp"] for r in results if r["extracted"].get("amount_gbp") is not None]
    total_value = sum(amounts)
    median_value = statistics.median(amounts) if amounts else 0.0
    high_value_count = sum(v >= 100_000 for v in amounts)
    extraction_conf = [r["extracted"]["confidence"] for r in results]
    class_conf = [r["classification"]["confidence"] for r in results]
    avg_extraction_conf = statistics.mean(extraction_conf) if extraction_conf else 0.0
    avg_class_conf = statistics.mean(class_conf) if class_conf else 0.0

    auto = decisions["auto_process"]
    review = decisions["human_review"]
    reject = decisions["reject"]
    non_auto = review + reject
    total_cost = sum(r["estimated_cost_usd"] for r in results)
    avg_cost = total_cost / docs if docs else 0.0
    avg_latency = statistics.mean(r["latency_ms"] for r in results) if results else 0.0

    value_by_type = defaultdict(float)
    supplier_count = Counter()
    supplier_value = defaultdict(float)
    for r in results:
        ex = r["extracted"]
        amount = ex.get("amount_gbp") or 0.0
        value_by_type[ex["document_type"]] += amount
        supplier = ex.get("supplier") or "Missing supplier"
        supplier_count[supplier] += 1
        supplier_value[supplier] += amount

    cost_by_decision = defaultdict(float)
    for r in results:
        cost_by_decision[r["decision"]] += r["estimated_cost_usd"]

    validation_rules = [
        "missing_supplier", "unknown_document_type", "low_extraction_confidence",
        "negative_amount", "missing_invoice_number", "missing_po_number",
        "invalid_date", "date_out_of_policy_range",
    ]

    val_rows = "".join(
        f'<tr><td>{html.escape(titleize(rule))}</td><td>{validation.get(rule, 0)}</td>'
        f'<td><span class="pill {"danger" if rule in {"negative_amount", "invalid_date"} else "warn"}">'
        f'{"Reject" if rule in {"negative_amount", "invalid_date"} else "Review"}</span></td></tr>'
        for rule in validation_rules
    )

    all_rows = []
    for r in results:
        ex = r["extracted"]
        cl = r["classification"]
        errors = ", ".join(titleize(e) for e in r.get("validation_errors", [])) or "—"
        reason = routing_reason(r)
        supplier = ex.get("supplier") or "—"
        amount = ex.get("amount_gbp")
        search = " ".join([
            r["document_id"], ex["document_type"], supplier, cl["category"], cl["priority"],
            r["decision"], errors, reason
        ]).lower()
        all_rows.append(
            '<tr '
            f'data-decision="{html.escape(r["decision"])}" '
            f'data-type="{html.escape(ex["document_type"])}" '
            f'data-priority="{html.escape(cl["priority"])}" '
            f'data-search="{html.escape(search)}">'
            f'<td class="mono">{html.escape(r["document_id"])}</td>'
            f'<td>{html.escape(titleize(ex["document_type"]))}</td>'
            f'<td>{html.escape(supplier)}</td>'
            f'<td class="num">{money(amount)}</td>'
            f'<td class="num">{ex["confidence"]*100:.0f}%</td>'
            f'<td>{html.escape(titleize(cl["category"]))}</td>'
            f'<td><span class="pill priority-{cl["priority"]}">{html.escape(titleize(cl["priority"]))}</span></td>'
            f'<td><span class="pill decision-{r["decision"]}">{html.escape(titleize(r["decision"]))}</span></td>'
            f'<td>{html.escape(reason)}</td>'
            f'<td>{html.escape(errors)}</td>'
            f'<td class="num">${r["estimated_cost_usd"]:.4f}</td>'
            '</tr>'
        )
    rows_html = "".join(all_rows)

    supplier_rows = "".join(
        f'<tr><td>{html.escape(name)}</td><td>{supplier_count[name]}</td><td class="num">{money(value)}</td></tr>'
        for name, value in sorted(supplier_value.items(), key=lambda kv: kv[1], reverse=True)[:10]
    )

    embedded = json.dumps({
        "counts": {
            "documents": docs, "auto": auto, "review": review, "reject": reject,
            "validation_documents": sum(bool(r.get("validation_errors")) for r in results),
            "high_priority": priorities["high"], "high_value": high_value_count,
        },
        "doc_types": doc_types,
        "categories": categories,
        "priorities": priorities,
        "decisions": decisions,
        "validation": validation,
    }).replace("</", "<\\/")

    return f'''<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Document Ops Workflow + GCP Prototype</title>
<style>
:root{{--bg:#07101f;--bg2:#0b1424;--panel:#101c2e;--panel2:#0d1828;--line:#26364d;--text:#e8eef7;--muted:#9fb0c5;--cyan:#42c8ff;--blue:#7c8cff;--violet:#a78bfa;--green:#34d399;--amber:#fbbf24;--red:#fb7185}}
*{{box-sizing:border-box}}html{{scroll-behavior:smooth}}body{{margin:0;font-family:Inter,ui-sans-serif,system-ui,-apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif;background:radial-gradient(circle at 20% -10%,#17345c 0,transparent 35%),var(--bg);color:var(--text)}}
a{{color:inherit}}.shell{{max-width:1480px;margin:auto;padding:0 28px 56px}}.topbar{{position:sticky;top:0;z-index:30;background:rgba(7,16,31,.9);backdrop-filter:blur(16px);border-bottom:1px solid rgba(148,163,184,.16)}}.topbar-inner{{max-width:1480px;margin:auto;padding:12px 28px;display:flex;align-items:center;justify-content:space-between;gap:18px}}.brand{{display:flex;align-items:center;gap:12px;font-weight:800}}.logo{{width:34px;height:34px;border-radius:10px;background:linear-gradient(135deg,var(--cyan),var(--violet));box-shadow:0 0 35px rgba(66,200,255,.22)}}.nav{{display:flex;gap:5px;overflow:auto}}.nav a{{text-decoration:none;color:var(--muted);font-size:13px;padding:8px 10px;border-radius:8px;white-space:nowrap}}.nav a:hover{{background:#152238;color:white}}
.hero{{padding:54px 0 32px;display:grid;grid-template-columns:1.5fr .9fr;gap:28px;align-items:end}}.eyebrow{{color:var(--cyan);font-size:12px;text-transform:uppercase;letter-spacing:.16em;font-weight:800}}h1{{font-size:clamp(34px,5vw,66px);line-height:.98;letter-spacing:-.045em;margin:12px 0 16px;max-width:950px}}.lead{{font-size:17px;line-height:1.7;color:#bfd0e4;max-width:900px}}.truth{{background:linear-gradient(145deg,rgba(66,200,255,.09),rgba(167,139,250,.08));border:1px solid #2e4765;border-radius:18px;padding:19px;line-height:1.55;color:#c6d5e6}}.truth b{{display:block;color:#f6fbff;margin-bottom:5px}}.truth .ok{{color:var(--green)}}
.section{{scroll-margin-top:72px;margin-top:28px}}.section-head{{display:flex;justify-content:space-between;gap:20px;align-items:end;margin:0 0 14px}}.section-head h2{{font-size:24px;margin:0;letter-spacing:-.02em}}.section-head p{{margin:0;color:var(--muted);max-width:760px;line-height:1.55;font-size:14px}}.cards{{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:12px}}.card,.panel{{background:linear-gradient(180deg,rgba(16,28,46,.97),rgba(12,23,39,.97));border:1px solid var(--line);border-radius:16px;box-shadow:0 16px 35px rgba(0,0,0,.13)}}.card{{padding:18px;min-height:112px}}.card .label{{font-size:11px;text-transform:uppercase;letter-spacing:.09em;color:var(--muted);font-weight:700}}.card .metric{{font-size:29px;font-weight:850;letter-spacing:-.03em;margin-top:10px}}.card .foot{{font-size:12px;color:var(--muted);margin-top:4px}}.accent{{color:var(--cyan)}}.good{{color:var(--green)}}.warn-text{{color:var(--amber)}}
.grid2{{display:grid;grid-template-columns:1fr 1fr;gap:14px}}.grid3{{display:grid;grid-template-columns:repeat(3,1fr);gap:14px}}.panel{{padding:20px;min-width:0}}.panel h3{{margin:0 0 5px;font-size:16px}}.panel .hint{{font-size:12px;color:var(--muted);line-height:1.5;margin-bottom:16px}}.wide{{grid-column:1/-1}}.barrow{{display:grid;grid-template-columns:155px 1fr 65px;gap:11px;align-items:center;margin:12px 0;font-size:13px}}.barrow>b{{font-size:12px;text-align:right}}.track{{height:11px;background:#1a293e;border-radius:999px;overflow:hidden}}.fill{{height:100%;background:linear-gradient(90deg,var(--cyan),var(--violet));border-radius:inherit}}
.funnel{{display:grid;gap:11px}}.funnel-row{{display:grid;grid-template-columns:145px 1fr 90px;align-items:center;gap:12px}}.funnel-bar{{height:36px;background:#15263d;border-radius:8px;overflow:hidden;position:relative}}.funnel-fill{{height:100%;display:flex;align-items:center;padding-left:12px;font-size:12px;font-weight:800;color:#07101f;background:linear-gradient(90deg,#67e8f9,#60a5fa)}}.funnel-fill.review{{background:linear-gradient(90deg,#fde68a,#fbbf24)}}.funnel-fill.reject{{background:linear-gradient(90deg,#fda4af,#fb7185)}}.funnel-num{{text-align:right;font-weight:800}}.policy{{display:grid;grid-template-columns:repeat(3,1fr);gap:9px;margin-top:16px}}.policy>div{{background:#0a1525;border:1px solid #24364d;padding:13px;border-radius:11px;font-size:12px;line-height:1.55;color:#b9c9da}}.policy b{{display:block;color:white;margin-bottom:3px}}
.table-wrap{{overflow:auto;border:1px solid #26364d;border-radius:12px}}table{{width:100%;border-collapse:collapse;font-size:12px;min-width:720px}}th,td{{padding:10px 11px;border-bottom:1px solid #223249;text-align:left;vertical-align:top}}th{{position:sticky;top:0;background:#132036;color:#8fdcff;text-transform:uppercase;font-size:10px;letter-spacing:.06em;z-index:2}}tbody tr:hover{{background:#122037}}.num{{text-align:right;font-variant-numeric:tabular-nums}}.mono{{font-family:ui-monospace,SFMono-Regular,Menlo,monospace}}.pill{{display:inline-block;padding:3px 7px;border-radius:999px;font-size:10px;font-weight:800;white-space:nowrap;background:#22324a;color:#d7e5f5}}.decision-auto_process,.priority-low{{background:rgba(52,211,153,.13);color:#6ee7b7}}.decision-human_review,.priority-medium,.warn{{background:rgba(251,191,36,.13);color:#fcd34d}}.decision-reject,.priority-high,.danger{{background:rgba(251,113,133,.14);color:#fda4af}}
.filters{{display:grid;grid-template-columns:2fr repeat(3,1fr);gap:8px;margin-bottom:12px}}input,select{{width:100%;background:#0a1525;border:1px solid #2b3c55;color:#e7eef8;border-radius:9px;padding:10px 11px;font:inherit;font-size:12px;outline:none}}input:focus,select:focus{{border-color:#38bdf8}}.table-count{{font-size:12px;color:var(--muted);margin:8px 0 0}}.empty{{color:var(--muted);font-size:13px;padding:15px 0}}
.arch{{display:grid;grid-template-columns:repeat(7,1fr);align-items:center;gap:7px;margin-top:16px}}.node{{min-height:74px;background:#0b1728;border:1px solid #2a3c55;border-radius:11px;padding:11px;display:flex;flex-direction:column;justify-content:center;text-align:center;font-size:11px;line-height:1.35}}.node b{{font-size:12px;margin-bottom:4px}}.arrow{{text-align:center;color:var(--cyan);font-size:20px}}.truth-grid{{display:grid;grid-template-columns:1fr 1fr;gap:12px}}.truth-list{{margin:8px 0 0;padding:0;list-style:none}}.truth-list li{{padding:6px 0;border-bottom:1px solid #223249;font-size:12px;color:#c6d5e6}}.truth-list li::before{{content:"✓";color:var(--green);font-weight:900;margin-right:8px}}.truth-list.future li::before{{content:"○";color:var(--amber)}}
@media(max-width:1000px){{.hero{{grid-template-columns:1fr}}.cards{{grid-template-columns:repeat(2,1fr)}}.grid2,.grid3{{grid-template-columns:1fr}}.wide{{grid-column:auto}}.arch{{grid-template-columns:1fr}}.arrow{{transform:rotate(90deg)}}.truth-grid{{grid-template-columns:1fr}}}}@media(max-width:660px){{.shell,.topbar-inner{{padding-left:14px;padding-right:14px}}.cards{{grid-template-columns:1fr 1fr}}.filters{{grid-template-columns:1fr 1fr}}.barrow{{grid-template-columns:110px 1fr 45px}}.policy{{grid-template-columns:1fr}}.nav{{display:none}}}}
</style></head><body>
<div class="topbar"><div class="topbar-inner"><div class="brand"><div class="logo"></div><span>Document Ops</span></div><div class="nav"><a href="#overview">Overview</a><a href="#workflow">Workflow</a><a href="#intelligence">Docs</a><a href="#controls">Checks</a><a href="#review">Queue</a><a href="#finops">Cost</a><a href="#platform">Build</a></div></div></div>
<main class="shell">
<section class="hero"><div><h1>Document Ops Workflow + GCP Prototype</h1><div class="lead">Built at home to get a better feel for document-heavy finance and commercial ops: extract key fields, classify the document, run a few checks, route edge cases to review and keep an audit trail. I kept the working version local, then added the GCP pieces I would use to take it further.</div></div><aside class="truth"><b>Current build</b><span class="ok">Working locally:</span> FastAPI, Pydantic models, extraction/classification logic, validation + routing, SQLite audit log, Docker/CI and the dashboard.<br><br><span class="warn-text">Not wired up yet:</span> Document AI, Vertex AI, BigQuery, Cloud Run and Apigee. The repo has the config/IaC needed for that next step.</aside></section>

<section class="section" id="overview"><div class="section-head"><div><div class="eyebrow">01 / Overview</div><h2>242 docs through the local pipeline</h2></div></div>
<div class="cards">
<div class="card"><div class="label">Docs processed</div><div class="metric">{docs:,}</div><div class="foot">Local sample</div></div>
<div class="card"><div class="label">Auto-processed</div><div class="metric good">{pct(auto, docs):.1f}%</div><div class="foot">{auto} docs</div></div>
<div class="card"><div class="label">Manual review</div><div class="metric warn-text">{pct(review, docs):.1f}%</div><div class="foot">{review} docs</div></div>
<div class="card"><div class="label">Rejected</div><div class="metric">{reject}</div><div class="foot">No hard failures in this run</div></div>
<div class="card"><div class="label">Doc value</div><div class="metric accent">{money(total_value)}</div><div class="foot">Synthetic sample</div></div>
<div class="card"><div class="label">High-value cases</div><div class="metric">{high_value_count}</div><div class="foot">Amount ≥ £100k</div></div>
<div class="card"><div class="label">Validation hits</div><div class="metric">{sum(bool(r.get('validation_errors')) for r in results)}</div><div class="foot">{sum(validation.values())} rule triggers</div></div>
<div class="card"><div class="label">Est. run cost</div><div class="metric">${total_cost:.4f}</div><div class="foot">${avg_cost:.5f} / doc</div></div>
</div></section>

<section class="section" id="workflow"><div class="section-head"><div><div class="eyebrow">02 / Workflow</div><h2>Where each doc ended up</h2></div></div>
<div class="grid2"><div class="panel"><h3>Routing split</h3><div class="funnel">
<div class="funnel-row"><span>Received</span><div class="funnel-bar"><div class="funnel-fill" style="width:100%">100%</div></div><div class="funnel-num">{docs}</div></div>
<div class="funnel-row"><span>Auto-process</span><div class="funnel-bar"><div class="funnel-fill" style="width:{pct(auto,docs):.1f}%">{pct(auto,docs):.1f}%</div></div><div class="funnel-num">{auto}</div></div>
<div class="funnel-row"><span>Human review</span><div class="funnel-bar"><div class="funnel-fill review" style="width:{pct(review,docs):.1f}%">{pct(review,docs):.1f}%</div></div><div class="funnel-num">{review}</div></div>
<div class="funnel-row"><span>Reject</span><div class="funnel-bar"><div class="funnel-fill reject" style="width:{max(1,pct(reject,docs)):.1f}%">{pct(reject,docs):.1f}%</div></div><div class="funnel-num">{reject}</div></div>
</div><div class="policy"><div><b>Auto</b>Checks pass, priority is not high and confidence is ≥ 0.80.</div><div><b>Review</b>Validation hit, high priority or confidence &lt; 0.80.</div><div><b>Reject</b>Negative amount or invalid date.</div></div></div>
<div class="panel"><h3>Why docs went to review</h3>{bar_rows(reasons)}</div></div></section>

<section class="section" id="intelligence"><div class="section-head"><div><div class="eyebrow">03 / Docs</div><h2>What came out</h2></div></div>
<div class="grid3"><div class="panel"><h3>Document mix</h3>{bar_rows(doc_types)}</div><div class="panel"><h3>Category</h3>{bar_rows(categories)}</div><div class="panel"><h3>Priority</h3>{bar_rows(priorities)}</div></div>
<div class="cards" style="margin-top:14px"><div class="card"><div class="label">Avg. extraction confidence</div><div class="metric">{avg_extraction_conf*100:.1f}%</div><div class="foot">Local score</div></div><div class="card"><div class="label">Avg. classification confidence</div><div class="metric">{avg_class_conf*100:.1f}%</div><div class="foot">Local score</div></div><div class="card"><div class="label">Median document value</div><div class="metric">{money(median_value)}</div><div class="foot">Docs with an amount</div></div><div class="card"><div class="label">High priority</div><div class="metric">{priorities['high']}</div><div class="foot">Sent to review</div></div></div>
<div class="grid2" style="margin-top:14px"><div class="panel"><h3>Document value by type</h3>{bar_rows(Counter(value_by_type), value_label=money)}</div><div class="panel"><h3>Top suppliers by value</h3><div class="table-wrap"><table><thead><tr><th>Supplier</th><th>Documents</th><th class="num">Value</th></tr></thead><tbody>{supplier_rows}</tbody></table></div></div></div></section>

<section class="section" id="controls"><div class="section-head"><div><div class="eyebrow">04 / Checks</div><h2>Validation + review rules</h2></div></div>
<div class="grid2"><div class="panel"><h3>Rule hits</h3><div class="table-wrap"><table><thead><tr><th>Rule</th><th>Triggered</th><th>Action</th></tr></thead><tbody>{val_rows}</tbody></table></div></div><div class="panel"><h3>What happens to each doc</h3><div class="policy" style="grid-template-columns:1fr"><div><b>1. Extract</b>Pull the fields I need into a typed record.</div><div><b>2. Classify</b>Set category, priority + confidence.</div><div><b>3. Check</b>Type, supplier, amount, IDs, dates + confidence.</div><div><b>4. Route</b>Reject hard failures, review edge cases, auto-process the rest.</div><div><b>5. Log</b>Save the result, latency + rough cost in SQLite.</div></div></div></div></section>

<section class="section" id="review"><div class="section-head"><div><div class="eyebrow">05 / Queue</div><h2>All processed docs</h2></div></div>
<div class="panel"><div class="filters"><input id="q" placeholder="Search ID, supplier, category, reason…"><select id="decision"><option value="">All decisions</option><option value="human_review">Human review</option><option value="auto_process">Auto process</option><option value="reject">Reject</option></select><select id="dtype"><option value="">All document types</option>{''.join(f'<option value="{html.escape(k)}">{html.escape(titleize(k))}</option>' for k in sorted(doc_types))}</select><select id="priority"><option value="">All priorities</option><option value="high">High</option><option value="medium">Medium</option><option value="low">Low</option></select></div>
<div class="table-wrap" style="max-height:560px"><table id="queue"><thead><tr><th>ID</th><th>Type</th><th>Supplier</th><th class="num">Amount</th><th class="num">Extract conf.</th><th>Category</th><th>Priority</th><th>Decision</th><th>Routing reason</th><th>Validation</th><th class="num">Cost</th></tr></thead><tbody>{rows_html}</tbody></table></div><div class="table-count" id="count"></div></div></section>

<section class="section" id="finops"><div class="section-head"><div><div class="eyebrow">06 / Cost</div><h2>Run cost</h2></div></div>
<div class="cards"><div class="card"><div class="label">Est. local cost</div><div class="metric">${total_cost:.4f}</div><div class="foot">Simple local estimate</div></div><div class="card"><div class="label">Avg. cost / doc</div><div class="metric">${avg_cost:.5f}</div><div class="foot">{docs} requests</div></div><div class="card"><div class="label">Avg. latency</div><div class="metric">{avg_latency:.1f} ms</div><div class="foot">Local run</div></div><div class="card"><div class="label">GCP spend</div><div class="metric">Not wired up</div><div class="foot">Local run only</div></div></div>
<div class="grid2" style="margin-top:14px"><div class="panel"><h3>Cost by route</h3>{bar_rows(Counter(cost_by_decision), value_label=lambda v:f'${v:.4f}')}</div><div class="panel"><h3>If I moved this to GCP</h3><div class="arch" style="grid-template-columns:1fr auto 1fr auto 1fr"><div class="node"><b>Billing export</b>Actual GCP spend</div><div class="arrow">→</div><div class="node"><b>BigQuery</b>Billing + app labels</div><div class="arrow">→</div><div class="node"><b>Cost view</b>Env · route · doc type · model</div></div></div></div></section>

<section class="section" id="platform"><div class="section-head"><div><div class="eyebrow">07 / Build</div><h2>Local now, GCP next</h2></div></div>
<div class="panel"><h3>How it fits together</h3><div class="arch"><div class="node"><b>API client</b>Document request</div><div class="arrow">→</div><div class="node"><b>FastAPI</b>Cloud Run later</div><div class="arrow">→</div><div class="node"><b>Extraction</b>Local parser → Doc AI</div><div class="arrow">→</div><div class="node"><b>Classification</b>Local logic → Vertex AI</div></div><div class="arch" style="margin-top:7px"><div class="node"><b>Checks</b>Required fields + rules</div><div class="arrow">→</div><div class="node"><b>Routing</b>Auto · review · reject</div><div class="arrow">→</div><div class="node"><b>Audit log</b>SQLite → BigQuery</div><div class="arrow">→</div><div class="node"><b>Dashboard</b>Ops + cost view</div></div></div>
<div class="truth-grid" style="margin-top:14px"><div class="panel"><h3>Working locally</h3><ul class="truth-list"><li>FastAPI endpoints + health checks</li><li>Pydantic request/response models</li><li>Field extraction + document classification</li><li>Validation, routing + manual review rules</li><li>SQLite audit log</li><li>Latency + rough per-request cost tracking</li><li>Docker, CI + GitHub Pages</li><li>20 validation & workflow checks implemented</li></ul></div><div class="panel"><h3>Not wired up yet</h3><ul class="truth-list future"><li>Document AI</li><li>Vertex AI</li><li>BigQuery</li><li>Cloud Run</li><li>Apigee</li><li>Terraform apply against a live GCP project</li><li>Cloud Billing export</li></ul></div></div>
</section>
</main>
<script id="dashboard-data" type="application/json">{embedded}</script>
<script>
const rows=[...document.querySelectorAll('#queue tbody tr')];
const q=document.getElementById('q'), decision=document.getElementById('decision'), dtype=document.getElementById('dtype'), priority=document.getElementById('priority'), count=document.getElementById('count');
function filterRows(){{const query=q.value.trim().toLowerCase();let shown=0;for(const row of rows){{const ok=(!query||row.dataset.search.includes(query))&&(!decision.value||row.dataset.decision===decision.value)&&(!dtype.value||row.dataset.type===dtype.value)&&(!priority.value||row.dataset.priority===priority.value);row.style.display=ok?'':'none';if(ok)shown++;}}count.textContent=`Showing ${{shown}} of ${{rows.length}} records`;}}
[q,decision,dtype,priority].forEach(x=>x.addEventListener(x.tagName==='INPUT'?'input':'change',filterRows));filterRows();
</script></body></html>'''


if __name__ == "__main__":
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_PATH.write_text(build(), encoding="utf-8")
    print(f"Wrote {OUTPUT_PATH}")
