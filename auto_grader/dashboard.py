"""Small Flask dashboard: list eval runs with a score trend chart, and
drill into any single run to see per-response scores and flags.
"""
import json

from flask import Flask, render_template, abort

from . import db

app = Flask(__name__, template_folder="../templates", static_folder="../static")
db.init_db()  # safe to call repeatedly; ensures tables exist under gunicorn too


@app.route("/")
def index():
    runs = db.list_runs()
    chart_labels = [r["label"] or f"Run {r['id']}" for r in runs]
    chart_scores = [round(r["avg_score"], 1) if r["avg_score"] is not None else 0 for r in runs]
    return render_template(
        "index.html",
        runs=runs,
        chart_labels=json.dumps(chart_labels),
        chart_scores=json.dumps(chart_scores),
    )


@app.route("/run/<int:run_id>")
def run_detail(run_id):
    run = db.get_run(run_id)
    if run is None:
        abort(404)
    results = db.get_results_for_run(run_id)
    parsed = []
    for r in results:
        parsed.append({
            **dict(r),
            "flags": json.loads(r["flags"] or "[]"),
            "check_errors": json.loads(r["check_errors"] or "[]"),
        })
    return render_template("run_detail.html", run=run, results=parsed)


if __name__ == "__main__":
    import os
    debug = os.environ.get("FLASK_DEBUG", "0") == "1"
    port = int(os.environ.get("PORT", 5050))
    app.run(host="0.0.0.0", port=port, debug=debug)
