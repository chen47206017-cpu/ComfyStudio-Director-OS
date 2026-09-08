import json
import sys
import traceback
from pathlib import Path
from datetime import datetime
from zoneinfo import ZoneInfo

import httpx
import keyring


PROJECT = Path(r"F:\一人公司\comfyui-production")

PROVIDER_FILE = PROJECT / "ai_operator" / "providers" / "providers.json"
REPORT_DIR = PROJECT / "reports" / "ai_operator"
REPORT_FILE = REPORT_DIR / "JOJO_MAX_CAPABILITY_REPORT.json"

BASE_URL_FALLBACK = "https://max2.jojocode.com/v1"

# 第一轮优先尝试。
# 如果 /models 返回可用模型，会优先寻找这些；
# 都不存在时再尝试 models 返回的前几个模型。
PREFERRED_MODELS = [
    "gpt-5.6",
    "gpt-5.6-codex",
    "gpt-5.5",
    "gpt-5",
]


def now_bj():
    return datetime.now(
        ZoneInfo("Asia/Shanghai")
    ).isoformat()


def safe_json(resp):
    try:
        return resp.json()
    except Exception:
        return {
            "_raw_preview": resp.text[:1000]
        }


def summarize_error(resp):
    data = safe_json(resp)

    if isinstance(data, dict):
        err = data.get("error")

        if isinstance(err, dict):
            return {
                "message": err.get("message"),
                "type": err.get("type"),
                "code": err.get("code"),
            }

    return {
        "status_code": resp.status_code,
        "body_preview": str(data)[:500],
    }


def load_provider():
    data = json.loads(
        PROVIDER_FILE.read_text(encoding="utf-8-sig")
    )

    provider = next(
        (
            x
            for x in data["providers"]
            if x["id"] == "jojo-max"
        ),
        None,
    )

    if not provider:
        raise RuntimeError(
            "providers.json 中没有 jojo-max"
        )

    return data, provider


def save_provider(data):
    PROVIDER_FILE.write_text(
        json.dumps(
            data,
            ensure_ascii=False,
            indent=2
        ),
        encoding="utf-8",
    )


def extract_models(data):
    if not isinstance(data, dict):
        return []

    items = data.get("data")

    if not isinstance(items, list):
        return []

    result = []

    for item in items:
        if isinstance(item, dict):
            model_id = item.get("id")

            if model_id:
                result.append(model_id)

    return result


def choose_candidates(
    registry_model,
    discovered_models
):
    result = []

    def add(x):
        if x and x not in result:
            result.append(x)

    if registry_model and registry_model != "auto":
        add(registry_model)

    # 优先我们希望使用的GPT模型，
    # 但只有发现列表里确实存在时才优先。
    for preferred in PREFERRED_MODELS:
        if preferred in discovered_models:
            add(preferred)

    # 再加入服务端发现的前5个
    for m in discovered_models[:5]:
        add(m)

    # 有些兼容站点不提供 /models，
    # 最后才尝试常用名称。
    if not result:
        for preferred in PREFERRED_MODELS:
            add(preferred)

    return result[:6]


def main():

    REPORT_DIR.mkdir(
        parents=True,
        exist_ok=True
    )

    report = {
        "timestamp_beijing": now_bj(),
        "provider": "jojo-max",
        "status": "PARTIAL",
        "base_url": None,
        "key_present": False,
        "key_length": 0,
        "models_endpoint": {
            "supported": False,
            "status_code": None,
            "models": [],
        },
        "responses": {
            "supported": False,
            "status_code": None,
            "model": None,
        },
        "tool_calling": {
            "supported": False,
            "status_code": None,
        },
        "structured_output": {
            "supported": False,
            "status_code": None,
        },
        "selected_model": None,
        "errors": [],
    }

    try:
        registry, provider = load_provider()

        base_url = (
            provider.get("base_url")
            or BASE_URL_FALLBACK
        ).rstrip("/")

        report["base_url"] = base_url

        key = keyring.get_password(
            "ComfyStudio",
            "jojo-max"
        )

        report["key_present"] = bool(key)
        report["key_length"] = len(key) if key else 0

        if not key:
            raise RuntimeError(
                "Windows Credential Manager 中没有 jojo-max Key"
            )

        headers = {
            "Authorization": f"Bearer {key}",
            "Content-Type": "application/json",
        }

        # 不把环境变量里的HTTP代理自动带进来，
        # 减少 Clash/旧代理重复接管。
        with httpx.Client(
            headers=headers,
            timeout=60.0,
            follow_redirects=True,
            trust_env=False,
        ) as client:

            print()
            print("========== 1. GET /models ==========")

            try:
                r = client.get(
                    f"{base_url}/models"
                )

                report[
                    "models_endpoint"
                ]["status_code"] = r.status_code

                print(
                    "HTTP",
                    r.status_code
                )

                if r.is_success:
                    models = extract_models(
                        safe_json(r)
                    )

                    report[
                        "models_endpoint"
                    ]["supported"] = True

                    report[
                        "models_endpoint"
                    ]["models"] = models[:100]

                    print(
                        "Models discovered:",
                        len(models)
                    )

                    for model in models[:20]:
                        print(" ", model)

                else:
                    report["errors"].append({
                        "stage": "models",
                        "detail": summarize_error(r),
                    })

                    models = []

            except Exception as e:
                models = []

                report["errors"].append({
                    "stage": "models",
                    "detail": repr(e),
                })

                print(
                    "MODELS ERROR:",
                    repr(e)
                )

            candidates = choose_candidates(
                provider.get("model"),
                models
            )

            print()
            print(
                "Candidate models:",
                candidates
            )

            selected_model = None

            print()
            print("========== 2. POST /responses ==========")

            for model in candidates:

                body = {
                    "model": model,
                    "input": (
                        "Reply with exactly this text "
                        "and nothing else: "
                        "COMFYSTUDIO_PROBE_OK"
                    ),
                    "max_output_tokens": 32,
                }

                try:
                    r = client.post(
                        f"{base_url}/responses",
                        json=body,
                    )

                    print(
                        model,
                        "=> HTTP",
                        r.status_code
                    )

                    if r.is_success:
                        selected_model = model

                        report["responses"] = {
                            "supported": True,
                            "status_code": r.status_code,
                            "model": model,
                        }

                        break

                    report["errors"].append({
                        "stage": "responses",
                        "model": model,
                        "detail": summarize_error(r),
                    })

                except Exception as e:
                    report["errors"].append({
                        "stage": "responses",
                        "model": model,
                        "detail": repr(e),
                    })

            if not selected_model:
                print()
                print(
                    "FAIL: 没有模型通过 Responses API"
                )

                report["status"] = "BLOCKED"

                REPORT_FILE.write_text(
                    json.dumps(
                        report,
                        ensure_ascii=False,
                        indent=2
                    ),
                    encoding="utf-8",
                )

                print(
                    "Report:",
                    REPORT_FILE
                )

                return 2

            report[
                "selected_model"
            ] = selected_model

            print()
            print(
                "PASS Responses API:",
                selected_model
            )

            # --------------------------------
            # Tool Calling
            # --------------------------------

            print()
            print("========== 3. Tool Calling ==========")

            tool_body = {
                "model": selected_model,
                "input": (
                    "You must call the "
                    "get_comfystudio_runtime_status "
                    "tool exactly once. "
                    "Do not answer normally."
                ),
                "tools": [
                    {
                        "type": "function",
                        "name": "get_comfystudio_runtime_status",
                        "description": (
                            "Read ComfyStudio runtime status."
                        ),
                        "parameters": {
                            "type": "object",
                            "properties": {},
                            "additionalProperties": False,
                        },
                    }
                ],
                "tool_choice": "required",
                "max_output_tokens": 128,
            }

            try:
                r = client.post(
                    f"{base_url}/responses",
                    json=tool_body,
                )

                report[
                    "tool_calling"
                ]["status_code"] = r.status_code

                print(
                    "HTTP",
                    r.status_code
                )

                if r.is_success:
                    data = safe_json(r)

                    outputs = (
                        data.get("output", [])
                        if isinstance(data, dict)
                        else []
                    )

                    function_calls = [
                        x
                        for x in outputs
                        if isinstance(x, dict)
                        and x.get("type") == "function_call"
                    ]

                    supported = (
                        len(function_calls) > 0
                    )

                    report[
                        "tool_calling"
                    ]["supported"] = supported

                    print(
                        "Function calls:",
                        len(function_calls)
                    )

                    if function_calls:
                        for call in function_calls:
                            print(
                                " ",
                                call.get("name")
                            )

                else:
                    report["errors"].append({
                        "stage": "tool_calling",
                        "detail": summarize_error(r),
                    })

            except Exception as e:
                report["errors"].append({
                    "stage": "tool_calling",
                    "detail": repr(e),
                })

                print(
                    "TOOL CALL ERROR:",
                    repr(e)
                )

            # --------------------------------
            # Structured Output
            # --------------------------------

            print()
            print("========== 4. Structured Output ==========")

            schema_body = {
                "model": selected_model,
                "input": (
                    "Return a workflow decision. "
                    "The action must be inspect."
                ),
                "text": {
                    "format": {
                        "type": "json_schema",
                        "name": "workflow_probe",
                        "strict": True,
                        "schema": {
                            "type": "object",
                            "properties": {
                                "action": {
                                    "type": "string",
                                    "enum": [
                                        "inspect"
                                    ],
                                },
                                "safe": {
                                    "type": "boolean"
                                },
                            },
                            "required": [
                                "action",
                                "safe"
                            ],
                            "additionalProperties": False,
                        },
                    }
                },
                "max_output_tokens": 128,
            }

            try:
                r = client.post(
                    f"{base_url}/responses",
                    json=schema_body,
                )

                report[
                    "structured_output"
                ]["status_code"] = r.status_code

                print(
                    "HTTP",
                    r.status_code
                )

                if r.is_success:
                    report[
                        "structured_output"
                    ]["supported"] = True

                    print(
                        "PASS Structured Output"
                    )

                else:
                    report["errors"].append({
                        "stage": "structured_output",
                        "detail": summarize_error(r),
                    })

            except Exception as e:
                report["errors"].append({
                    "stage": "structured_output",
                    "detail": repr(e),
                })

                print(
                    "STRUCTURED OUTPUT ERROR:",
                    repr(e)
                )

        # --------------------------------
        # 最终状态
        # --------------------------------

        if (
            report["responses"]["supported"]
            and
            report["tool_calling"]["supported"]
        ):
            report["status"] = "READY"

        elif report["responses"]["supported"]:
            report["status"] = "PARTIAL"

        else:
            report["status"] = "BLOCKED"

        # --------------------------------
        # 更新Provider Registry
        # --------------------------------

        provider["model"] = (
            report["selected_model"]
            or provider.get("model")
        )

        provider["capabilities"][
            "responses"
        ] = report["responses"]["supported"]

        provider["capabilities"][
            "tool_calling"
        ] = report["tool_calling"]["supported"]

        provider["capabilities"][
            "structured_output"
        ] = report[
            "structured_output"
        ]["supported"]

        # Streaming本轮还没探测
        provider["capabilities"][
            "streaming"
        ] = "pending_probe"

        save_provider(registry)

        REPORT_FILE.write_text(
            json.dumps(
                report,
                ensure_ascii=False,
                indent=2
            ),
            encoding="utf-8",
        )

        print()
        print("====================================")
        print(
            "JOJO MAX STATUS =",
            report["status"]
        )
        print(
            "SELECTED MODEL =",
            report["selected_model"]
        )
        print(
            "RESPONSES =",
            report["responses"]["supported"]
        )
        print(
            "TOOL CALLING =",
            report["tool_calling"]["supported"]
        )
        print(
            "STRUCTURED OUTPUT =",
            report["structured_output"]["supported"]
        )
        print(
            "REPORT =",
            REPORT_FILE
        )
        print("====================================")

        return 0

    except Exception as e:

        report["status"] = "BLOCKED"

        report["errors"].append({
            "stage": "fatal",
            "detail": repr(e),
            "traceback": traceback.format_exc(),
        })

        REPORT_FILE.write_text(
            json.dumps(
                report,
                ensure_ascii=False,
                indent=2
            ),
            encoding="utf-8",
        )

        print(
            "FATAL:",
            repr(e)
        )

        print(
            "Report:",
            REPORT_FILE
        )

        return 1


if __name__ == "__main__":
    sys.exit(main())
