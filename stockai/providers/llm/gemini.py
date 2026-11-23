"""Gemini provider (google-genai). [KIỂM CHỨNG] tên model trong docs/DECISIONS.md."""

from stockai.errors import ConfigError, TransientError
from stockai.models import ScriptContext, ScriptOutput
from stockai.providers.llm.base import build_prompts


class GeminiProvider:
    name = "gemini"

    def __init__(self, api_key: str | None, model: str, fallback_model: str | None = None):
        if not api_key:
            raise ConfigError("Chưa có Gemini API key", hint="Cài đặt → AI → Gemini API key")
        self.api_key, self.model, self.fallback_model = api_key, model, fallback_model

    async def _call(self, model: str, ctx: ScriptContext, feedback: str | None) -> ScriptOutput:
        from google import genai
        from google.genai import types

        sys, user = build_prompts(ctx, feedback)
        client = genai.Client(api_key=self.api_key)
        resp = await client.aio.models.generate_content(
            model=model, contents=user,
            config=types.GenerateContentConfig(system_instruction=sys, response_mime_type="application/json",
                                               response_schema=ScriptOutput, temperature=0.5))
        return ScriptOutput.model_validate_json(resp.text)

    async def generate(self, ctx: ScriptContext, feedback: str | None = None) -> ScriptOutput:
        last: Exception | None = None
        for model in [self.model] + ([self.fallback_model] if self.fallback_model else []):
            for _ in range(2):
                try:
                    out = await self._call(model, ctx, feedback)
                    self.model = model
                    return out
                except Exception as e:  # 429/5xx → thử lại / đổi model
                    last = e
                    msg = str(e)
                    if not any(c in msg for c in ("429", "500", "503", "RESOURCE_EXHAUSTED", "UNAVAILABLE")):
                        break
        raise TransientError(f"Gemini lỗi: {last}")
