import json
import os
from typing import Any

import requests
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt


def _voiceframe_base_url() -> str:
    return os.environ.get("VOICEFRAME_API_BASE_URL", "http://127.0.0.1:8020").rstrip("/")


def _timeout_s() -> int:
    raw = os.environ.get("VOICEFRAME_PROXY_TIMEOUT", "30")
    try:
        return max(5, int(raw))
    except (TypeError, ValueError):
        return 30


def _proxy_error(detail: str, status: int = 502) -> JsonResponse:
    return JsonResponse({"status": "error", "error": detail}, status=status)


@csrf_exempt
def generate(request):
    if request.method != "POST":
        return JsonResponse({"error": "Only POST allowed"}, status=405)

    try:
        target = f"{_voiceframe_base_url()}/generate"
        resp = requests.post(
            target,
            data=request.body,
            headers={"Content-Type": request.META.get("CONTENT_TYPE", "application/json")},
            timeout=_timeout_s(),
        )
        try:
            payload: Any = resp.json()
        except ValueError:
            return _proxy_error("Invalid JSON from voiceframe service")
        return JsonResponse(payload, status=resp.status_code)
    except requests.RequestException as e:
        return _proxy_error(str(e))


def status(request, job_id: str):
    if request.method != "GET":
        return JsonResponse({"error": "Only GET allowed"}, status=405)

    try:
        target = f"{_voiceframe_base_url()}/status/{job_id}"
        resp = requests.get(target, timeout=_timeout_s())
        try:
            payload: Any = resp.json()
        except ValueError:
            return _proxy_error("Invalid JSON from voiceframe service")
        return JsonResponse(payload, status=resp.status_code)
    except requests.RequestException as e:
        return _proxy_error(str(e))


def result(request, job_id: str):
    if request.method != "GET":
        return JsonResponse({"error": "Only GET allowed"}, status=405)

    try:
        target = f"{_voiceframe_base_url()}/result/{job_id}"
        resp = requests.get(target, timeout=_timeout_s())
        try:
            payload: Any = resp.json()
        except ValueError:
            return _proxy_error("Invalid JSON from voiceframe service")
        return JsonResponse(payload, status=resp.status_code)
    except requests.RequestException as e:
        return _proxy_error(str(e))
