"""Provider cho mọi API kiểu OpenAI (base_url, model, api_key) với JSON mode."""

import httpx

from stockai.errors import ConfigError
from stockai.models import ScriptContext, ScriptOutput
from stockai.providers.llm.base import build_prompts


class OpenAICompatProvider:
    name = "openai_compat"

    def __init__(self, base_url: str, model: str, api_key: str | None):
        if not base_url or not model or not api_key:
            raise ConfigError("Thiếu base_url/model/api_key cho OpenAI-compatible")
        self.base_url, self.model, self.api_key = base_url.rstrip("/"), model, api_key

    async def generate(self, ctx: ScriptContext, feedback: str | None = None) -> ScriptOutput:
        sys, user = build_prompts(ctx, feedback)
        schema_hint = "\nJSON schema:\n" + str(ScriptOutput.model_json_schema())
        async with httpx.AsyncClient(timeout=90) as c:
            r = await c.post(f"{self.base_url}/chat/completions", headers={"Authorization": f"Bearer {self.api_key}"},
                             json={"model": self.model, "temperature": 0.5, "response_format": {"type": "json_object"},
                                   "messages": [{"role": "system", "content": sys + schema_hint},
                                                {"role": "user", "content": user}]})
            r.raise_for_status()
        return ScriptOutput.model_validate_json(r.json()["choices"][0]["message"]["content"])
