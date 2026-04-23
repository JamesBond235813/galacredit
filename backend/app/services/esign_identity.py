import base64
import hashlib
import hmac
import json
import re
import time
from typing import Any, Dict, Optional
from urllib import error, request

from app.core.config import settings


class ESignIdentityError(Exception):
    pass


class ESignIdentityClient:
    ERROR_CODE_MAP = {
        "IDENTITY_AUTH_FAIL": "实名核验未通过，请确认姓名、身份证号与人脸为本人信息。",
        "FACE_COMPARE_FAIL": "人脸比对未通过，请在光线充足环境下重试。",
        "FACE_NOT_LIVE": "活体检测未通过，请正对镜头并完成眨眼/点头动作后重试。",
        "FACE_QUALITY_LOW": "人脸照片质量不足，请保持清晰、无遮挡后重试。",
        "IDCARD_OCR_FAIL": "身份证识别失败，请重新拍摄清晰的身份证照片。",
        "IDCARD_INFO_MISMATCH": "身份证信息与核验主体不一致，请确认后重试。",
        "PARAM_ERROR": "请求参数有误，请检查姓名、身份证号和图片后重试。",
        "UNAUTHORIZED": "身份核验服务鉴权失败，请联系管理员检查 e签宝配置。",
        "TOKEN_EXPIRED": "身份核验服务授权已过期，系统将自动重试。",
        "TOO_MANY_REQUESTS": "核验请求过于频繁，请稍后再试。",
        "30503129": "身份证人像面识别失败，请拍摄清晰的人像面后重试。",
        "30503131": "身份证国徽面识别失败，请拍摄清晰的国徽面后重试。",
        "30504001": "人脸核验未通过，请核实姓名、身份证号与本人照片是否一致。",
        "30504002": "核验数据源查询失败，请稍后重试或联系管理员。",
        "30500100": "请求参数不完整，请检查姓名、身份证号与照片后重试。",
        "FACE_CONFIDENCE_LOW": "人脸识别信息与身份证信息不符，请重新尝试借款。",
    }

    ERROR_KEYWORD_MAP = {
        "活体": "活体检测未通过，请在光线充足环境下按提示完成动作。",
        "liveness": "活体检测未通过，请在光线充足环境下按提示完成动作。",
        "quality": "图片质量不足，请重新拍摄清晰无遮挡的人脸/证件照片。",
        "blur": "图片模糊，请重新拍摄后再试。",
        "occlusion": "检测到遮挡，请露出完整面部后重试。",
        "face not found": "未检测到清晰人脸，请将面部置于画面中央后重试。",
        "idcard": "身份证识别失败，请重新拍摄身份证正反面。",
        "name idno not match": "姓名与身份证号不匹配，请核对后重试。",
        "token": "身份核验服务授权异常，请稍后重试。",
        "signature": "身份核验服务签名校验失败，请联系管理员。",
        "timeout": "身份核验服务响应超时，请稍后重试。",
    }

    def ensure_configured(self) -> None:
        if not settings.ESIGN_APP_ID or not settings.ESIGN_APP_SECRET:
            raise ESignIdentityError("e签宝参数未配置完整，请检查 ESIGN_APP_ID / ESIGN_APP_SECRET。")

    def _build_url(self, path: str) -> str:
        return f"{settings.ESIGN_OPENAPI_BASE_URL.rstrip('/')}{path}"

    @staticmethod
    def _to_base64(raw: bytes) -> str:
        return base64.b64encode(raw).decode("utf-8")

    @staticmethod
    def _normalize_valid_period(value: Optional[str]) -> Optional[str]:
        if not value:
            return value
        # 兼容 2025.04.22-2045.04.22 / 2025/04/22-长期 等格式，统一成 YYYY.MM.DD-YYYY.MM.DD(或长期)
        normalized = value.strip().replace("/", ".").replace("—", "-")
        normalized = re.sub(r"\s+", "", normalized)
        return normalized

    def _build_signature_headers(self, method: str, path: str, payload: Optional[bytes]) -> Dict[str, str]:
        method = method.upper()
        accept = "*/*"
        content_type = "application/json;charset=UTF-8"
        content_md5 = ""
        if payload is not None:
            content_md5 = base64.b64encode(hashlib.md5(payload).digest()).decode("utf-8")

        # stringToSign = METHOD + "\n" + ACCEPT + "\n" + CONTENT_MD5 + "\n" + CONTENT_TYPE + "\n" + DATE + "\n" + URL
        # DATE 这里为空字符串，但换行符必须保留。
        string_to_sign = (
            f"{method}\n"
            f"{accept}\n"
            f"{content_md5}\n"
            f"{content_type}\n"
            "\n"
            f"{path}"
        )
        signature = base64.b64encode(
            hmac.new(
                settings.ESIGN_APP_SECRET.encode("utf-8"),
                string_to_sign.encode("utf-8"),
                digestmod=hashlib.sha256,
            ).digest()
        ).decode("utf-8")

        timestamp = str(int(time.time() * 1000))
        headers = {
            "Accept": accept,
            "Content-Type": content_type,
            "X-Tsign-Open-Auth-Mode": "Signature",
            "X-Tsign-Open-App-Id": settings.ESIGN_APP_ID,
            "X-Tsign-Open-Ca-Timestamp": timestamp,
            "X-Tsign-Open-Ca-Signature": signature,
        }
        if content_md5:
            headers["Content-MD5"] = content_md5
        return headers

    def _http_request(self, method: str, path: str, body: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        self.ensure_configured()
        payload = None
        if body is not None:
            payload = json.dumps(body, ensure_ascii=False).encode("utf-8")

        headers = self._build_signature_headers(method, path, payload)
        req = request.Request(
            url=self._build_url(path),
            data=payload,
            headers=headers,
            method=method.upper(),
        )

        try:
            with request.urlopen(req, timeout=settings.ESIGN_HTTP_TIMEOUT_SECONDS) as resp:
                raw = resp.read().decode("utf-8")
                return json.loads(raw) if raw else {}
        except error.HTTPError as exc:
            raw = exc.read().decode("utf-8", errors="ignore")
            raise ESignIdentityError(self._translate_http_error(exc.code, raw)) from exc
        except error.URLError as exc:
            raise ESignIdentityError(f"网络请求失败: {exc.reason}") from exc
        except json.JSONDecodeError as exc:
            raise ESignIdentityError("服务返回了无法解析的响应。") from exc

    def _translate_http_error(self, status_code: int, raw_body: str) -> str:
        parsed: Dict[str, Any] = {}
        try:
            if raw_body:
                parsed = json.loads(raw_body)
        except Exception:
            parsed = {}

        code = str(parsed.get("code") or parsed.get("errCode") or "").strip()
        msg = str(parsed.get("message") or parsed.get("msg") or raw_body or "").strip()
        business_msg = self._translate_business_error(code, msg)

        if status_code == 401:
            return "身份核验服务鉴权失败，请联系管理员检查 e签宝 AppId/Secret 或签名规则。"
        if status_code == 429:
            return "身份核验请求过于频繁，请稍后再试。"
        if status_code >= 500:
            return f"身份核验服务异常（{status_code}），请稍后重试。"
        if business_msg:
            return business_msg
        return f"身份核验请求失败（HTTP {status_code}）。"

    def _translate_business_error(self, code: str, msg: str) -> str:
        normalized_code = (code or "").strip().upper()
        if normalized_code in self.ERROR_CODE_MAP:
            return self.ERROR_CODE_MAP[normalized_code]

        normalized_msg = re.sub(r"\s+", " ", (msg or "").strip())
        lower_msg = normalized_msg.lower()
        for key, mapped in self.ERROR_KEYWORD_MAP.items():
            if key in lower_msg:
                return mapped

        if normalized_msg:
            return f"核验失败：{normalized_msg}"
        return ""

    def _extract_response_data(self, resp: Dict[str, Any], default_err: str) -> Dict[str, Any]:
        code_raw = resp.get("code", resp.get("errCode", 0))
        code = str(code_raw).strip()
        success_codes = {"0", "200", "SUCCESS", ""}
        if code not in success_codes:
            msg = str(resp.get("message") or resp.get("msg") or "").strip()
            translated = self._translate_business_error(code, msg)
            raise ESignIdentityError(translated or default_err)

        data = resp.get("data")
        if isinstance(data, dict):
            return data

        result = resp.get("result")
        if isinstance(result, dict):
            return result

        if isinstance(resp, dict) and resp:
            return resp
        raise ESignIdentityError(default_err)

    def id_card_ocr(self, info_face_bytes: bytes, emblem_face_bytes: Optional[bytes]) -> Dict[str, Any]:
        if not info_face_bytes:
            raise ESignIdentityError("请上传身份证人像面。")

        body: Dict[str, Any] = {
            "infoImg": self._to_base64(info_face_bytes),
        }
        if emblem_face_bytes:
            body["emblemImg"] = self._to_base64(emblem_face_bytes)

        resp = self._http_request("POST", "/v2/identity/auth/api/ocr/idcard", body=body)
        data = self._extract_response_data(resp, "身份证识别失败，请重新拍摄后重试。")

        return {
            "name": (data.get("name") or "").strip(),
            "id_card_num": (data.get("idNo") or "").strip(),
            "id_address": (data.get("address") or "").strip(),
            "id_expiry": (self._normalize_valid_period(data.get("validityPeriod")) or "").strip(),
        }

    def face_compare(self, name: str, id_card_num: str, face_image_bytes: bytes) -> Dict[str, Any]:
        if not face_image_bytes:
            raise ESignIdentityError("请上传人脸照片。")

        resp = self._http_request(
            "POST",
            "/v2/identity/verify/individual/faceCompare/withoutSource",
            body={
                "name": name,
                "idNo": id_card_num,
                "faceImgBase64": self._to_base64(face_image_bytes),
            },
        )
        data = self._extract_response_data(resp, "人脸核验失败，请重新尝试。")

        # 人脸核验接口语义：code=0表示通过，非0已在 _extract_response_data 里抛错。
        score = data.get("confidence")
        if score is None:
            score = data.get("score")
        try:
            numeric_score = float(score) if score is not None else None
        except (TypeError, ValueError):
            numeric_score = None

        threshold = float(settings.ESIGN_FACE_CONFIDENCE_THRESHOLD or 70.0)
        if numeric_score is None:
            raise ESignIdentityError("人脸核验结果异常，请重新拍摄后再试。")
        if numeric_score < threshold:
            raise ESignIdentityError(self.ERROR_CODE_MAP["FACE_CONFIDENCE_LOW"])

        return {"passed": True, "score": numeric_score, "raw": data, "threshold": threshold}


esign_identity_client = ESignIdentityClient()
