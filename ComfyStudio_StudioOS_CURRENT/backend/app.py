"""ComfyStudio StudioOS Production Core Flask application.

The application owns the stable absolute paths and the V10 API contract.  Older
V8 modules remain on disk for compatibility, while this entry point avoids their
relative-path and duplicate-blueprint problems.
"""

from __future__ import annotations

import sys
import json
import uuid
from pathlib import Path
from typing import Any, Mapping

from flask import Flask, Response, jsonify, request, send_file, send_from_directory

BACKEND_DIR = Path(__file__).resolve().parent
ROOT = BACKEND_DIR.parent
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from v10_core import (  # noqa: E402
    CanvasConflict,
    ComfyClient,
    DB,
    MEMORY_PATH,
    UI,
    STUDIO_PATHS,
    atomic_write_json,
    canon_check,
    compile_prompt,
    load_canvas,
    load_database,
    parse_script,
    qc_html,
    read_json,
    save_canvas,
    now_beijing,
)
from services.worker_registry import WorkerRegistry, lane_definition, normalize_public_lane  # noqa: E402
from services.workflow_capsule import WorkflowCapsuleStore  # noqa: E402
from services.job_service import JobStore  # noqa: E402
from services.output_validation import validate_mp4_output  # noqa: E402
from services.asset_resolver import bind_shot, resolve_assets  # noqa: E402
from services.character_identity import build_identity_bindings, voice_bindings  # noqa: E402
from services.continuity import evaluate_continuity  # noqa: E402


def _json_body() -> dict[str, Any]:
    body = request.get_json(silent=True)
    return dict(body) if isinstance(body, Mapping) else {}


def _expected_revision(body: Mapping[str, Any]) -> int | None:
    value = body.get("expected_revision", body.get("revision"))
    if value is None:
        value = request.headers.get("If-Match")
    if value is None or value == "":
        return None
    try:
        text = str(value).strip().strip('"')
        if text.startswith("W/"):
            text = text[2:].strip('"')
        return int(text)
    except (TypeError, ValueError):
        return None


def _document(name: str, default: Any) -> Any:
    return load_database(name, default)


def _ui_file() -> tuple[Path, str]:
    dist = UI / "dist" / "index.html"
    if dist.exists():
        return UI / "dist", "index.html"
    v92 = UI / "v92" / "director.html"
    if v92.exists():
        return UI / "v92", "director.html"
    return UI, "director.html" if (UI / "director.html").exists() else "index.html"


DEMO_ROOT = ROOT / "demo" / "projects" / "demo_time_phone"


def _demo_json(name: str, default: Any) -> Any:
    return read_json(DEMO_ROOT / name, default)


def _demo_state() -> dict[str, Any]:
    state = read_json(DEMO_ROOT / "runtime.json", {"version": "1", "shots": {}, "updated_at": now_beijing()})
    return dict(state) if isinstance(state, Mapping) else {"version": "1", "shots": {}, "updated_at": now_beijing()}


def _save_demo_state(state: Mapping[str, Any]) -> None:
    atomic_write_json(DEMO_ROOT / "runtime.json", {**dict(state), "updated_at": now_beijing()})

def create_app(
    comfy_client: ComfyClient | None = None,
    worker_registry: WorkerRegistry | None = None,
    capsule_store: WorkflowCapsuleStore | None = None,
    job_store: JobStore | None = None,
) -> Flask:
    """Create an app suitable for production or isolated route tests."""

    # Static files are served through explicit UI/dist and legacy routes below.
    # Disabling Flask's catch-all static rule prevents it from intercepting the
    # Vite `/assets/...` bundle paths before our production asset route.
    app = Flask(__name__, static_folder=None)
    app.config.update(JSON_AS_ASCII=False, COMFYSTUDIO_ROOT=str(ROOT), COMFY_URL="http://127.0.0.1:8189")
    comfy = comfy_client or ComfyClient()
    registry = worker_registry or WorkerRegistry()
    capsules = capsule_store or WorkflowCapsuleStore(ROOT)
    jobs = job_store or JobStore(DB / "studioos_jobs.sqlite3")
    output_root = STUDIO_PATHS.reports_dir / "job_outputs"

    def _lane_state(value: Any) -> tuple[str, dict[str, Any] | None, dict[str, Any] | None]:
        """Resolve the public lane without allowing a cloud fallback."""
        lane = normalize_public_lane(str(value or "local_comfy"))
        definition = lane_definition(lane)
        if definition.get("blocked_reason"):
            return lane, None, {
                "status": "BLOCKED",
                "reason_code": definition["blocked_reason"],
                "message_zh": definition["blocked_message"],
                "lane": lane,
            }
        worker = registry.select(lane)
        # A small compatibility adapter keeps existing injected V10 test
        # registries usable while production WorkerRegistry maps local_comfy.
        if worker is None and lane == "local_comfy":
            worker = registry.select("local_h3")
        if worker is None:
            return lane, None, {
                "status": "BLOCKED",
                "reason_code": "LOCAL_COMFY_UNAVAILABLE",
                "message_zh": "本机 ComfyUI 8189 当前不可用，未提交任务。",
                "lane": lane,
            }
        return lane, worker, None

    def _lane_inventory(workers: list[Mapping[str, Any]]) -> list[dict[str, Any]]:
        local = next(
            (
                worker for worker in workers
                if worker.get("status") == "READY"
                and (worker.get("lane") == "local_comfy" or worker.get("internal_lane") == "local_h3" or worker.get("lane") == "local_h3")
            ),
            None,
        )
        return [
            {
                "id": "local_comfy",
                "label_zh": "本机 ComfyUI 8189",
                "status": "READY" if local else "BLOCKED",
                "reason_code": None if local else "LOCAL_COMFY_UNAVAILABLE",
                "worker_id": local.get("id") if local else None,
            },
            {
                "id": "autodl5090",
                "label_zh": "AutoDL 5090",
                "status": "BLOCKED",
                "reason_code": "AUTODL5090_NOT_CONFIGURED",
                "message_zh": "尚未配置，系统不会回退到本机或调用付费服务。",
            },
            {
                "id": "api",
                "label_zh": "API",
                "status": "BLOCKED",
                "reason_code": "API_NOT_CONFIGURED",
                "message_zh": "尚未配置，系统不会发送外部或付费请求。",
            },
        ]

    def _output_evidence_path(output_path: Path) -> Path:
        return output_path.with_suffix(output_path.suffix + ".validation.json")

    def _output_view(job_id: str, output: Mapping[str, Any]) -> dict[str, Any]:
        """Expose only allowlisted output metadata, never a direct local path."""
        result = {
            "id": output.get("id"),
            "job_id": job_id,
            "filename": Path(str(output.get("path") or "")).name,
            "sha256": output.get("sha256"),
            "mime": output.get("mime"),
            "verified": bool(output.get("verified")),
            "created_at": output.get("created_at"),
        }
        evidence = read_json(_output_evidence_path(Path(str(output.get("path") or ""))), {})
        if isinstance(evidence, Mapping) and evidence.get("verified"):
            result["duration_s"] = evidence.get("duration_s")
            result["ffprobe"] = evidence.get("ffprobe")
        if result["verified"] and result["mime"] == "video/mp4":
            result["media_url"] = f"/api/v10/jobs/{job_id}/outputs/{output.get('id')}/media"
        return result

    def _job_outputs_view(job_id: str) -> list[dict[str, Any]]:
        return [_output_view(job_id, output) for output in jobs.outputs(job_id)]

    # UI and static files -------------------------------------------------
    @app.get("/")
    @app.get("/director")
    @app.get("/director/")
    def director() -> Response:
        directory, filename = _ui_file()
        return send_from_directory(str(directory), filename)

    @app.get("/legacy")
    def legacy() -> Response:
        filename = "index.html" if (UI / "index.html").exists() else "director.html"
        return send_from_directory(str(UI), filename)

    @app.get("/director/css/<path:filename>")
    def director_css(filename: str) -> Response:
        return send_from_directory(str(UI / "v92" / "css"), filename)

    @app.get("/director/js/<path:filename>")
    def director_js(filename: str) -> Response:
        return send_from_directory(str(UI / "v92" / "js"), filename)

    @app.get("/director/assets/<path:filename>")
    def director_dist_assets(filename: str) -> Response:
        return send_from_directory(str(UI / "dist" / "assets"), filename)

    @app.get("/assets/<path:filename>")
    def root_dist_assets(filename: str) -> Response:
        """Serve the Vite bundle paths emitted by the production index.html."""
        return send_from_directory(str(UI / "dist" / "assets"), filename)

    @app.get("/director/<path:filename>")
    def director_dist_path(filename: str) -> Response:
        dist = UI / "dist"
        candidate = dist / filename
        if candidate.is_file():
            return send_from_directory(str(dist), filename)
        return send_from_directory(str(dist), "index.html")

    # Stable V10 API ------------------------------------------------------
    @app.get("/api/v10/health")
    def v10_health():
        return jsonify({
            "ok": True,
            "service": "ComfyStudio StudioOS Production Core",
            "version": "V10.1-V44",
            "root": str(ROOT),
            "now": now_beijing(),
            "comfy": comfy.health(),
        })

    @app.get("/api/v10/health/live")
    def v10_health_live():
        return jsonify({"status": "READY", "version": "V10.1-V44", "timezone": "Asia/Shanghai", "now": now_beijing()})

    @app.get("/api/v10/health/ready")
    def v10_health_ready():
        database_ready = DB.exists() and (DB / "canon.json").exists()
        lane = request.args.get("lane") or "local_comfy"
        if lane == "core":
            selected, lane_error = None, None
        else:
            lane, selected, lane_error = _lane_state(lane)
        comfy_state = "READY" if selected else ("NOT_REQUIRED" if lane == "core" else "BLOCKED")
        status = "READY" if database_ready and (lane == "core" or selected) else "BLOCKED"
        ready_status = 200 if status == "READY" else 503
        return jsonify({
            "status": status,
            "database": "READY" if database_ready else "BLOCKED",
            "studio": "READY",
            "comfy": comfy_state,
            "lane": lane,
            "worker_id": selected.get("id") if selected else None,
            "reason_code": lane_error.get("reason_code") if lane_error else None,
            "message_zh": lane_error.get("message_zh") if lane_error else None,
            "timezone": "Asia/Shanghai",
            "now": now_beijing(),
        }), ready_status

    @app.get("/api/v10/workers")
    def v10_workers():
        workers = registry.discover()
        lane = request.args.get("lane")
        if lane:
            normalized = normalize_public_lane(lane)
            workers = [
                worker for worker in workers
                if worker.get("lane") == normalized or (normalized == "local_comfy" and worker.get("internal_lane") == "local_h3")
            ]
        return jsonify({
            "status": "READY" if any(worker.get("status") == "READY" for worker in workers) else "BLOCKED",
            "time": now_beijing(),
            "workers": workers,
            "lanes": _lane_inventory(registry.discover() if lane else workers),
        })

    @app.post("/api/v10/workers/probe")
    def v10_workers_probe():
        workers = registry.discover()
        return jsonify({"status": "READY" if any(worker.get("status") == "READY" for worker in workers) else "BLOCKED", "time": now_beijing(), "workers": workers, "lanes": _lane_inventory(workers)})

    @app.get("/api/v10/demo/project")
    def v10_demo_project():
        project = _demo_json("project.json", {})
        shots = _demo_json("shots.json", {"shots": []})
        assets = _demo_json("assets.json", {"assets": []})
        voices = _demo_json("voices.json", {"voices": []})
        return jsonify({"project": project, "shots": shots.get("shots", []) if isinstance(shots, Mapping) else [], "assets": assets.get("assets", []) if isinstance(assets, Mapping) else [], "voices": voices.get("voices", []) if isinstance(voices, Mapping) else [], "runtime": _demo_state(), "time": now_beijing()})

    def _prepare_demo_shot(shot_id: str) -> dict[str, Any]:
        shots_doc = _demo_json("shots.json", {"shots": []})
        shots = shots_doc.get("shots", []) if isinstance(shots_doc, Mapping) else []
        shot = next((item for item in shots if isinstance(item, Mapping) and item.get("id") == shot_id), None)
        if not shot:
            return {"status": "NOT_FOUND", "shot_id": shot_id, "issues": [{"code": "SHOT_NOT_FOUND"}]}
        previous = next((item for item in shots if isinstance(item, Mapping) and item.get("id") == shot.get("previous_shot_id")), None)
        resolved = bind_shot(shot)
        identities = build_identity_bindings(list(shot.get("characters", [])))
        voices = voice_bindings(list(shot.get("characters", [])), list(shot.get("voices", [])))
        continuity = evaluate_continuity(previous, shot)
        payload = {"shot": dict(shot), "assets": resolved["assets"], "references": resolved["assets"], "memory": {"continuity": continuity}, "positive": [identity.get("name") for identity in identities]}
        gate = canon_check(payload)
        prompt = compile_prompt(payload) if gate.get("pass") else {"positive": "", "negative": "", "references": []}
        return {"status": "READY" if gate.get("pass") and continuity.get("status") in {"READY", "ROOT_SHOT"} else "HOLD", "shot": dict(shot), "resolved_assets": resolved, "character_bindings": identities, "voice_bindings": voices, "continuity": continuity, "canon_gate": gate, "prompt_bundle": prompt, "time": now_beijing()}

    @app.get("/api/v10/demo/shots/<shot_id>/prepare")
    @app.post("/api/v10/demo/shots/<shot_id>/prepare")
    def v10_demo_prepare(shot_id: str):
        result = _prepare_demo_shot(shot_id)
        return jsonify(result), (200 if result.get("status") in {"READY", "HOLD"} else 404)

    @app.post("/api/v10/demo/shots/<shot_id>/generate")
    def v10_demo_generate(shot_id: str):
        body = _json_body()
        prepared = _prepare_demo_shot(shot_id)
        if prepared.get("status") != "READY":
            return jsonify({"status": "HOLD", "prepared": prepared}), 422
        if not body.get("execute"):
            return jsonify({
                "status": "PREPARED",
                "execution": "NOT_REQUESTED",
                "prepared": prepared,
                "message_zh": "已完成 Canon、连续性和提示词准备；未创建或提交任务。",
            })

        lane, worker, lane_error = _lane_state(body.get("lane"))
        if lane_error:
            return jsonify({**lane_error, "prepared": prepared}), 422
        idempotency_key = str(body.get("idempotency_key") or f"demo-{shot_id}-{uuid.uuid4().hex}")
        job, duplicate = jobs.create({
            "idempotency_key": idempotency_key,
            "lane": lane,
            "capsule_id": "h3_reference_to_video",
            "shot_id": shot_id,
            "requested_at": now_beijing(),
        })
        if duplicate:
            return jsonify({
                "status": "IDEMPOTENT_REPLAY",
                "job": job,
                "outputs": _job_outputs_view(job["id"]),
                "message_zh": "相同请求已创建任务，不会重复上传或重复提交。",
            })

        jobs.transition(job["id"], "PREFLIGHT", {"shot_id": shot_id, "lane": lane})
        preflight = capsules.preflight("h3_reference_to_video", worker)
        if preflight.get("status") != "READY":
            failed = jobs.transition(
                job["id"],
                "FAILED",
                {"reason_code": "H3_PREFLIGHT_BLOCKED", "preflight": preflight},
                error_json={"reason_code": "H3_PREFLIGHT_BLOCKED", "preflight": preflight},
            ) or job
            return jsonify({"status": "BLOCKED", "reason_code": "H3_PREFLIGHT_BLOCKED", "job": failed, "preflight": preflight}), 422

        expected_reference = str(prepared["shot"].get("reference_image") or "").strip()
        requested_reference = str(body.get("reference_image") or expected_reference).strip()
        if not expected_reference or not requested_reference:
            failed = jobs.transition(
                job["id"], "FAILED", {"reason_code": "REFERENCE_REQUIRED"}, error_json={"reason_code": "REFERENCE_REQUIRED"}
            ) or job
            return jsonify({"status": "BLOCKED", "reason_code": "REFERENCE_REQUIRED", "job": failed, "message_zh": "H3 参考图生视频必须绑定已登记的参考图。"}), 422
        try:
            source_reference = Path(requested_reference).resolve()
            permitted_reference = Path(expected_reference).resolve()
        except OSError:
            source_reference = Path(requested_reference)
            permitted_reference = Path(expected_reference)
        if source_reference != permitted_reference:
            failed = jobs.transition(
                job["id"],
                "FAILED",
                {"reason_code": "REFERENCE_SOURCE_NOT_ALLOWED"},
                error_json={"reason_code": "REFERENCE_SOURCE_NOT_ALLOWED"},
            ) or job
            return jsonify({"status": "BLOCKED", "reason_code": "REFERENCE_SOURCE_NOT_ALLOWED", "job": failed, "message_zh": "当前镜头只能使用已绑定参考资产，不能上传任意本机路径。"}), 422

        jobs.transition(job["id"], "STAGING", {"worker_id": worker.get("id"), "preflight": preflight})
        uploaded = comfy.upload_input(source_reference, subfolder="studioos_demo", image_type="input")
        if not uploaded.get("uploaded"):
            failed = jobs.transition(
                job["id"],
                "FAILED",
                {"reason_code": "REFERENCE_UPLOAD_FAILED", "upload": uploaded},
                error_json={"reason_code": "REFERENCE_UPLOAD_FAILED", "upload": uploaded},
            ) or job
            return jsonify({"status": "BLOCKED", "reason_code": "REFERENCE_UPLOAD_FAILED", "job": failed, "upload": uploaded}), 422
        try:
            duration_seconds = float(prepared["shot"].get("duration_seconds", 5))
            seed = int(body.get("seed", 552845927415303))
        except (TypeError, ValueError):
            failed = jobs.transition(
                job["id"],
                "FAILED",
                {"reason_code": "WORKFLOW_PARAMETER_INVALID"},
                error_json={"reason_code": "WORKFLOW_PARAMETER_INVALID"},
            ) or job
            return jsonify({"status": "BLOCKED", "reason_code": "WORKFLOW_PARAMETER_INVALID", "job": failed, "message_zh": "镜头时长或随机种子无效。"}), 422
        compiled = capsules.compile_workflow("h3_reference_to_video", {
            "prompt": prepared["prompt_bundle"].get("positive", ""),
            "duration_seconds": duration_seconds,
            "aspect_ratio": str(body.get("aspect_ratio") or prepared["shot"].get("aspect_ratio") or "9:16"),
            "reference_image": uploaded.get("name") or uploaded.get("filename"),
            "seed": seed,
        })
        if compiled.get("status") != "READY":
            failed = jobs.transition(
                job["id"],
                "FAILED",
                {"reason_code": compiled.get("reason_code", "WORKFLOW_COMPILE_FAILED"), "workflow": compiled},
                error_json={"reason_code": compiled.get("reason_code", "WORKFLOW_COMPILE_FAILED"), "workflow": compiled},
            ) or job
            return jsonify({"status": "BLOCKED", "reason_code": compiled.get("reason_code", "WORKFLOW_COMPILE_FAILED"), "job": failed, "workflow": compiled}), 422
        result = comfy.submit(compiled["workflow"], body.get("client_id") or f"studioos-{job['id']}", False)
        if not result.get("submitted"):
            job = jobs.transition(job["id"], "FAILED", {"result": result}, error_json={"reason_code": "COMFY_SUBMIT_FAILED", "result": result}) or job
            return jsonify({"status": "FAILED", "job": job, "comfy": result}), 502
        job = jobs.transition(job["id"], "QUEUED", {"prompt_id": result.get("prompt_id")}, worker_id=worker.get("id") if worker else None, prompt_id=result.get("prompt_id")) or job
        return jsonify({
            "status": "QUEUED",
            "job": job,
            "comfy": result,
            "prepared": prepared,
            "lane": lane,
            "workflow_evidence": compiled.get("evidence"),
            "message_zh": "任务已提交；只有下载并校验通过的 MP4 才会显示完成。",
        })
    @app.get("/api/v10/capabilities")
    def v10_capabilities():
        workers = registry.discover()
        ready_workers = [worker for worker in workers if worker.get("status") == "READY"]
        _, selected_worker, lane_error = _lane_state("local_comfy")
        h3_worker = selected_worker if selected_worker and selected_worker.get("capabilities", {}).get("h3") else None
        preflight = capsules.preflight("h3_reference_to_video", h3_worker)
        h3_status = "READY" if preflight.get("status") == "READY" else ("BLOCKED" if not h3_worker else "UNVERIFIED")
        checks = [
            {"id": "studio.process", "status": "READY", "reason_code": None, "message_zh": "StudioOS 进程正常响应"},
            {"id": "comfy.worker", "status": "READY" if ready_workers else "BLOCKED", "reason_code": None if ready_workers else "COMFY_UNREACHABLE", "message_zh": "已发现 ComfyUI Worker" if ready_workers else "未发现可用的 ComfyUI Worker"},
            {"id": "comfy.h3", "status": h3_status, "reason_code": None if h3_status == "READY" else (lane_error or {}).get("reason_code", "H3_RUNTIME_UNVERIFIED"), "message_zh": "H3 节点和模型均已通过 HTTP 预检" if h3_status == "READY" else "H3 节点或模型尚未完成可执行预检"},
            {"id": "workflow.capsule", "status": preflight["status"], "reason_code": None if preflight["status"] == "READY" else (preflight.get("errors") or [{"code": "CAPSULE_BLOCKED"}])[0].get("code"), "message_zh": "H3 工作流胶囊预检通过" if preflight["status"] == "READY" else "H3 工作流胶囊预检未通过"},
        ]
        overall = "READY" if all(item["status"] == "READY" for item in checks) else ("DEGRADED" if any(item["status"] == "READY" for item in checks) else "BLOCKED")
        return jsonify({"status": overall, "time": now_beijing(), "lane": "local_comfy", "checks": checks, "workers": workers, "lanes": _lane_inventory(workers), "capsule_preflight": preflight, "evidence": {"object_info": "/api/v10/comfy/object_info", "worker_scope": "HTTP-only"}})

    @app.get("/api/v10/assets")
    def v10_assets():
        """Expose the production asset registry without replacing its source file."""
        data = _document("assets.json", {"assets": []})
        items = data.get("assets", []) if isinstance(data, Mapping) else data
        if not isinstance(items, list):
            items = []
        return jsonify({"total": len(items), "assets": items})

    @app.get("/api/v10/workflows/capsules")
    def v10_capsules():
        return jsonify({"capsules": capsules.list(), "time": now_beijing()})

    @app.get("/api/v10/workflows/capsules/<capsule_id>")
    def v10_capsule(capsule_id: str):
        item = capsules.get(capsule_id)
        if item is None:
            return jsonify({"status": "NOT_FOUND", "error": "capsule_not_found"}), 404
        return jsonify(item)

    @app.post("/api/v10/workflows/capsules/<capsule_id>/preflight")
    def v10_capsule_preflight(capsule_id: str):
        lane, worker, lane_error = _lane_state(request.args.get("lane") or "local_comfy")
        if lane_error:
            return jsonify({**lane_error, "time": now_beijing()}), 422
        result = capsules.preflight(capsule_id, worker)
        return jsonify({**result, "time": now_beijing(), "lane": lane}), (200 if result["status"] == "READY" else 422)

    @app.get("/api/v10/canvas")
    def v10_canvas_get():
        return jsonify(load_canvas())

    @app.route("/api/v10/canvas", methods=["POST", "PUT"])
    def v10_canvas_save():
        body = _json_body()
        try:
            saved = save_canvas(body.get("canvas", body), _expected_revision(body))
        except CanvasConflict as conflict:
            return jsonify({"ok": False, "error": "revision_conflict", "current": conflict.current}), 409
        return jsonify({"ok": True, **saved})

    @app.get("/api/v10/canvases/<canvas_id>")
    def v10_canvas_by_id(canvas_id: str):
        canvas = load_canvas()
        canvas["id"] = canvas_id
        return jsonify(canvas)

    @app.put("/api/v10/canvases/<canvas_id>")
    def v10_canvas_by_id_save(canvas_id: str):
        body = _json_body()
        try:
            saved = save_canvas({**body, "id": canvas_id}, _expected_revision(body))
        except CanvasConflict as conflict:
            return jsonify({"ok": False, "error": "revision_conflict", "current": conflict.current}), 409
        return jsonify(saved)

    @app.get("/api/v10/gates")
    def v10_gates_get():
        return jsonify({"canon": "POST /api/v10/gates/canon", "blocking": True})

    @app.post("/api/v10/gates/canon")
    @app.post("/api/v10/canon/check")
    @app.post("/api/v10/gates/evaluate")
    def v10_canon_gate():
        result = canon_check(_json_body())
        return jsonify({
            "status": "GO" if result["pass"] else "HOLD",
            "issues": result.get("errors", []),
            "evidence": result.get("warnings", []),
            "affected_shots": [],
            **result,
        }), (200 if result["pass"] else 422)

    @app.post("/api/v10/prompts/compile")
    @app.post("/api/v10/prompt/compile")
    @app.post("/api/v10/prompts/build")
    def v10_prompt_compile():
        body = _json_body()
        gate = canon_check(body)
        if gate["blocked"]:
            return jsonify({"status": "HOLD", "error": "canon_blocked", "canon_gate": gate}), 422
        return jsonify(compile_prompt(body))

    @app.post("/api/v10/script/parse")
    @app.post("/api/v10/scripts/parse")
    def v10_script_parse():
        body = _json_body()
        return jsonify(parse_script(body.get("text", ""), body.get("episode", "E01")))

    @app.post("/api/v10/references/plan")
    def v10_reference_plan():
        body = _json_body()
        refs = body.get("references") or body.get("assets") or []
        return jsonify({"status": "GO" if refs else "HOLD", "reference_map": refs, "issues": [] if refs else ["missing references"]})

    @app.get("/api/v10/comfy/status")
    def v10_comfy_status():
        return jsonify(comfy.health())

    @app.get("/api/v10/comfy/object_info")
    def v10_comfy_object_info():
        result = comfy.object_info()
        return jsonify(result), (200 if result.get("connected", False) else 503)

    @app.get("/api/v10/comfy/queue")
    def v10_comfy_queue():
        result = comfy.queue()
        return jsonify(result), (200 if result.get("connected", False) else 503)

    @app.get("/api/v10/comfy/history")
    @app.get("/api/v10/comfy/history/<prompt_id>")
    def v10_comfy_history(prompt_id: str | None = None):
        result = comfy.history(prompt_id)
        return jsonify(result), (200 if result.get("connected", False) else 503)

    @app.post("/api/v10/comfy/submit")
    def v10_comfy_submit():
        body = _json_body()
        gate = canon_check(body)
        if gate["blocked"]:
            return jsonify({"status": "HOLD", "error": "canon_blocked", "canon_gate": gate}), 422
        workflow = body.get("workflow", body.get("prompt", body))
        result = comfy.submit(workflow, body.get("client_id"), bool(body.get("dry_run", False)))
        result["canon_gate"] = gate
        return jsonify(result), (200 if result.get("submitted") or result.get("dry_run") else 502)

    @app.post("/api/v10/qc/report")
    def v10_qc_report():
        html = qc_html(_json_body())
        if request.args.get("format") == "json":
            return jsonify({"html": html})
        return Response(html, mimetype="text/html")

    @app.route("/api/v10/jobs", methods=["GET", "POST"])
    def v10_jobs():
        if request.method == "GET":
            return jsonify({"jobs": jobs.list(), "time": now_beijing()})
        body = _json_body()
        requested_lane = body.get("lane") or "local_comfy"
        lane = normalize_public_lane(str(requested_lane))
        worker: dict[str, Any] | None = None
        if body.get("submit"):
            lane, worker, lane_error = _lane_state(lane)
            if lane_error:
                return jsonify(lane_error), 422
        job, duplicate = jobs.create({**body, "lane": lane})
        if duplicate:
            return jsonify({"status": "IDEMPOTENT_REPLAY", "job": job, "time": now_beijing()}), 200
        if body.get("submit"):
            capsule_id = body.get("capsule_id") or "h3_reference_to_video"
            jobs.transition(job["id"], "PREFLIGHT", {"lane": lane})
            preflight = capsules.preflight(capsule_id, worker)
            if preflight["status"] != "READY":
                job = jobs.transition(job["id"], "FAILED", {"reason_code": "PREFLIGHT_BLOCKED", "preflight": preflight}, error_json={"reason_code": "PREFLIGHT_BLOCKED", "preflight": preflight}) or job
                return jsonify({"status": "BLOCKED", "job": job, "preflight": preflight}), 422
            jobs.transition(job["id"], "STAGING", {"capsule_id": capsule_id, "worker_id": worker.get("id") if worker else None})
            result = comfy.submit(body.get("workflow", body.get("prompt", {})), body.get("client_id"), bool(body.get("dry_run", False)))
            if result.get("dry_run"):
                # dry_run 只验证门禁与 payload，绝不能伪装成已排队的真实任务。
                job = jobs.transition(job["id"], "PREFLIGHT", {"dry_run": True}, worker_id=worker.get("id") if worker else None) or job
            elif result.get("submitted"):
                job = jobs.transition(job["id"], "QUEUED", {"prompt_id": result.get("prompt_id")}, worker_id=worker.get("id") if worker else None, prompt_id=result.get("prompt_id")) or job
            else:
                job = jobs.transition(job["id"], "FAILED", {"reason_code": "COMFY_SUBMIT_FAILED", "result": result}, error_json={"reason_code": "COMFY_SUBMIT_FAILED", "result": result}) or job
            return jsonify({"status": job["status"], "job": job, "worker": worker, "comfy": result}), (200 if job["status"] == "QUEUED" else 502)
        return jsonify({"status": "DRAFT", "job": job, "time": now_beijing()}), 201

    @app.get("/api/v10/jobs/<job_id>")
    def v10_job(job_id: str):
        job = jobs.get(job_id)
        return (jsonify({"job": job, "events": jobs.events(job_id), "outputs": _job_outputs_view(job_id), "time": now_beijing()}), 200) if job else (jsonify({"error": "job_not_found"}), 404)

    @app.get("/api/v10/jobs/<job_id>/events")
    def v10_job_events(job_id: str):
        if not jobs.get(job_id):
            return jsonify({"error": "job_not_found"}), 404
        return jsonify({"job_id": job_id, "events": jobs.events(job_id), "time": now_beijing()})

    @app.get("/api/v10/jobs/<job_id>/outputs")
    def v10_job_outputs(job_id: str):
        if not jobs.get(job_id):
            return jsonify({"error": "job_not_found"}), 404
        return jsonify({"job_id": job_id, "outputs": _job_outputs_view(job_id), "time": now_beijing()})

    @app.get("/api/v10/jobs/<job_id>/outputs/<output_id>/media")
    def v10_job_output_media(job_id: str, output_id: str):
        output = jobs.get_output(job_id, output_id)
        if output is None:
            return jsonify({"status": "NOT_FOUND", "reason_code": "JOB_OUTPUT_NOT_FOUND"}), 404
        if not output.get("verified") or output.get("mime") != "video/mp4":
            return jsonify({"status": "BLOCKED", "reason_code": "JOB_OUTPUT_NOT_VERIFIED", "message_zh": "该任务输出尚未通过 MP4 验收，不能播放。"}), 404
        validation = validate_mp4_output(output.get("path") or "", output_root)
        if not validation.get("verified"):
            return jsonify({"status": "BLOCKED", "reason_code": validation.get("reason_code", "OUTPUT_MP4_VERIFICATION_FAILED"), "message_zh": "输出文件已不满足 MP4 播放验收。"}), 409
        if validation.get("sha256") != output.get("sha256"):
            return jsonify({"status": "BLOCKED", "reason_code": "OUTPUT_HASH_MISMATCH", "message_zh": "输出内容与已登记的 SHA-256 不一致，拒绝播放。"}), 409
        return send_file(validation["path"], mimetype="video/mp4", conditional=True, as_attachment=False)

    def _refresh_job(job_id: str) -> dict[str, Any]:
        job = jobs.get(job_id)
        if not job:
            return {"status": "NOT_FOUND", "job_id": job_id}
        if job.get("status") in {"SUCCEEDED", "FAILED", "CANCELLED"}:
            return {"status": job.get("status"), "job": job, "outputs": _job_outputs_view(job_id), "message_zh": "任务已处于终态，不会重复提交。"}
        prompt_id = job.get("prompt_id")
        if not prompt_id:
            return {"status": job.get("status"), "job": job, "reason_code": "PROMPT_ID_MISSING"}
        history = comfy.history(prompt_id)
        records = comfy._history_records(history) if hasattr(comfy, "_history_records") else []
        if records:
            jobs.transition(job_id, "COLLECTING", {"prompt_id": prompt_id})
            destination = output_root / job_id
            collector = getattr(comfy, "collect_outputs", None)
            outputs = collector(history, destination) if callable(collector) else []
            validations: list[dict[str, Any]] = []
            for item in outputs:
                if item.get("downloaded") and item.get("path"):
                    validation = validate_mp4_output(item["path"], output_root)
                else:
                    validation = {
                        "verified": False,
                        "reason_code": "OUTPUT_DOWNLOAD_FAILED",
                        "message_zh": "无法下载 ComfyUI 输出，不能标记任务完成。",
                        "download": item,
                    }
                validations.append(validation)
            verified = [item for item in validations if item.get("verified")]
            for item in verified:
                output_path = Path(str(item["path"]))
                atomic_write_json(_output_evidence_path(output_path), item)
                jobs.add_output(job_id, str(output_path), str(item["sha256"]), "video/mp4", True)
            if verified:
                jobs.transition(job_id, "SUCCEEDED", {"output_count": len(verified), "validation": verified})
            else:
                jobs.transition(
                    job_id,
                    "FAILED",
                    {"reason_code": "OUTPUT_MP4_VERIFICATION_FAILED", "outputs": outputs, "validations": validations},
                    error_json={"reason_code": "OUTPUT_MP4_VERIFICATION_FAILED", "outputs": outputs, "validations": validations},
                )
        else:
            queue = comfy.queue()
            raw = (queue.get("queue_running") or []) + (queue.get("queue_pending") or [])
            queue_text = repr(raw)
            next_status = "RUNNING" if str(prompt_id) in queue_text else "ORPHANED"
            jobs.transition(job_id, next_status, {"prompt_id": prompt_id, "queue": queue})
        updated = jobs.get(job_id)
        return {"status": updated.get("status") if updated else "UNKNOWN", "job": updated, "history": history, "outputs": _job_outputs_view(job_id)}

    @app.post("/api/v10/jobs/<job_id>/refresh")
    def v10_job_refresh(job_id: str):
        result = _refresh_job(job_id)
        return jsonify({**result, "time": now_beijing()}), (200 if result.get("status") != "NOT_FOUND" else 404)

    @app.post("/api/v10/jobs/<job_id>/cancel")
    def v10_job_cancel(job_id: str):
        job = jobs.get(job_id)
        if not job:
            return jsonify({"error": "job_not_found"}), 404
        result = comfy.cancel(job.get("prompt_id")) if job.get("prompt_id") else {"cancelled": True, "status": 200, "connected": True}
        updated = jobs.transition(job_id, "CANCELLED", {"comfy": result}) or job
        return jsonify({"job": updated, "comfy": result, "time": now_beijing()})

    @app.post("/api/v10/jobs/reconcile")
    def v10_jobs_reconcile():
        queue = comfy.queue()
        refreshed = []
        if queue.get("connected"):
            for active_job in jobs.active():
                refreshed.append(_refresh_job(active_job["id"]))
        return jsonify({"status": "RECONCILED" if queue.get("connected") else "DEGRADED", "queue": queue, "jobs": refreshed, "time": now_beijing()})

    @app.route("/api/v10/memory", methods=["GET", "POST"])
    def v10_memory():
        if request.method == "GET":
            return jsonify(read_json(MEMORY_PATH, {"version": "MemoryOS_1.0", "memory": []}))
        body = _json_body()
        current = read_json(MEMORY_PATH, {"version": "MemoryOS_1.0", "memory": []})
        if not isinstance(current, Mapping):
            current = {"version": "MemoryOS_1.0", "memory": []}
        memory = list(current.get("memory") or [])
        memory.append({"id": body.get("id") or f"memory-{len(memory) + 1:04}", **body})
        updated = {**dict(current), "memory": memory}
        atomic_write_json(MEMORY_PATH, updated)
        return jsonify(updated), 201

    # Legacy V4/V8 routes -----------------------------------------------
    @app.get("/api/status")
    def legacy_status():
        return jsonify({"version": "V8.0", "name": "ComfyStudio StudioOS Production Core", "status": "running"})

    @app.get("/api/ui/status")
    @app.get("/api/v8/ui/status")
    def legacy_ui_status():
        return jsonify({"ui": "V9.2", "backend": "V8.0", "status": "online", "agent": True, "memory": True})

    @app.get("/api/assets")
    def legacy_assets():
        data = _document("assets.json", None)
        if data is None:
            data = _document("studio.json", {"assets": []})
        return jsonify(data)

    @app.get("/api/v8/director/assets")
    @app.get("/api/v8/production/assets")
    def v8_assets():
        data = _document("assets.json", {"assets": []})
        items = data.get("assets", []) if isinstance(data, Mapping) else data
        return jsonify({"total": len(items), "assets": items})

    @app.get("/api/shots")
    def legacy_shots():
        return jsonify(_document("shots.json", {"shots": []}))

    @app.get("/api/v8/production/shots")
    def v8_shots():
        data = _document("shots.json", {"shots": []})
        return jsonify(data.get("shots", []) if isinstance(data, Mapping) else data)

    @app.get("/api/canon")
    def legacy_canon():
        return jsonify(_document("canon.json", {"rules": []}))

    @app.get("/api/reference")
    def legacy_reference():
        return jsonify(_document("reference.json", {"slots": []}))

    @app.post("/api/prompt")
    def legacy_prompt():
        body = _json_body()
        gate = canon_check(body)
        if gate["blocked"]:
            return jsonify({"status": "HOLD", "error": "canon_blocked", "canon_gate": gate}), 422
        return jsonify(compile_prompt(body))

    @app.get("/api/v8/status")
    def v8_status():
        return jsonify({"version": "V8.0", "status": "running", "comfy": comfy.health()})

    @app.get("/api/v8/pipeline/status")
    def v8_pipeline_status():
        return jsonify({"status": "ready", "queue": []})

    @app.get("/api/v8/pipeline/queue")
    def v8_pipeline_queue():
        return jsonify({"queue": []})

    @app.post("/api/v8/canon/check")
    def v8_canon():
        result = canon_check(_json_body())
        return jsonify(result), (200 if result["pass"] else 422)

    @app.post("/api/v8/prompt/build")
    def v8_prompt():
        body = _json_body()
        gate = canon_check(body)
        if gate["blocked"]:
            return jsonify({"status": "HOLD", "error": "canon_blocked", "canon_gate": gate}), 422
        return jsonify(compile_prompt(body))

    @app.post("/api/v8/comfy/submit")
    def v8_submit():
        body = _json_body()
        gate = canon_check(body)
        if gate["blocked"]:
            return jsonify({"status": "HOLD", "error": "canon_blocked", "canon_gate": gate}), 422
        result = comfy.submit(body.get("workflow", body.get("prompt", body)))
        result["canon_gate"] = gate
        return jsonify(result), (200 if result.get("submitted") else 502)

    @app.route("/api/v8/director/canvas", methods=["GET", "POST", "PUT"])
    def v8_canvas():
        if request.method == "GET":
            return jsonify(load_canvas())
        body = _json_body()
        try:
            return jsonify(save_canvas(body.get("canvas", body), _expected_revision(body)))
        except CanvasConflict as conflict:
            return jsonify({"error": "revision_conflict", "current": conflict.current}), 409

    @app.post("/api/v8/production/parse")
    def v8_parse():
        body = _json_body()
        return jsonify(parse_script(body.get("text", ""), body.get("episode", "E01")))

    @app.post("/memory/search")
    @app.post("/api/v8/memory/search")
    def memory_search():
        body = _json_body()
        query = str(body.get("query", "")).strip().lower()
        memory = read_json(MEMORY_PATH, {"memory": []})
        items = memory.get("memory", []) if isinstance(memory, Mapping) else []
        matches = [item for item in items if query and query in str(item).lower()]
        return jsonify({"query": query, "memory": matches})

    return app


app = create_app()


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=8190)







