"""Integration: render-sample 8 giây → ffprobe 1080×1920 / 30fps / có audio / metadata AI. Cần FFmpeg."""

from datetime import date

import pytest

from stockai import config
from stockai.render import ffmpeg
from stockai.render.composer import broll_sequence, final_graph

pytestmark = pytest.mark.skipif(not ffmpeg.which("ffmpeg"), reason="cần FFmpeg")


def test_preflight_filters():
    r = ffmpeg.preflight_sync()
    assert r["ok"], r


def test_broll_sequence_segments_6_to_8s():
    for D in (45, 75, 95):
        seq, seg = broll_sequence(3, D)
        assert 6 <= seg <= 8.2 and seq[0] == "chart.png" and seq[-1] == "chart.png"
        assert abs(len(seq) * seg - (len(seq) - 1) * 0.4 - D) < 1e-6


def test_final_graph_has_required_filters():
    g = final_graph(800, 75, False, -22)
    for k in ("overlay=0:280", "overlay=0:944", "-mod(t*140,800)", "showwaves", "ass=subs.ass:fontsdir=fonts",
              "lt(t,3)", "gte(t,71.000)", "loudnorm=I=-14"):
        assert k in g
    assert "amix" in final_graph(800, 75, True, -22)


async def test_render_sample_8s(tmp_path):
    from stockai.render.sample import render_sample

    out = await render_sample(date(2026, 11, 23), tmp_path / "job")
    info = await ffmpeg.probe(out)
    v = next(s for s in info["streams"] if s["codec_type"] == "video")
    assert (v["width"], v["height"]) == (1080, 1920) and v["r_frame_rate"] == "30/1"
    assert any(s["codec_type"] == "audio" for s in info["streams"])
    assert abs(float(info["format"]["duration"]) - 8) <= 0.5
    assert info["format"]["tags"].get("comment") == config.AI_METADATA
    assert (tmp_path / "job" / "thumbnail.jpg").exists() and (tmp_path / "job" / "safe_zone_check.png").exists()


@pytest.mark.network
async def test_e2e_offline_pipeline():
    """E2E (chậm ~2–3 phút): uv run pytest -m network -k e2e."""
    from stockai.pipeline.orchestrator import Orchestrator

    o = Orchestrator()
    jid = await o.start(offline=True, skip_publish=True, mode="DEMO")
    await o.wait()
    assert o.repo.get_job(jid)["status"] == "COMPLETED"


def test_hybrid_split_plan():
    from stockai.providers.avatar.hybrid import split_plan

    assert split_plan(10) == [("full", 0.0, 10)]
    p = split_plan(75)
    assert [n for n, *_ in p] == ["head", "mid", "tail"] and abs(sum(d for *_, d in p) - 75) < 1e-6


async def test_hybrid_avatar_concat(tmp_path):
    """Lip-sync giả = DemoMotion có giá 0,1$/s → kiểm tra nối đoạn, độ dài, chi phí chỉ tính head+tail."""

    from PIL import Image

    from stockai.providers.avatar.demo_motion import DemoMotionProvider
    from stockai.providers.avatar.hybrid import HybridAvatarProvider

    class FakeLip(DemoMotionProvider):
        name = "fake"

        def estimate_cost_usd(self, d):
            return round(0.1 * d, 2)

        async def render(self, *a):
            r = await super().render(*a)
            return r.model_copy(update={"cost_usd": self.estimate_cost_usd(r.duration_s)})

    Image.new("RGB", (540, 488), (40, 60, 90)).save(tmp_path / "p.png")
    await ffmpeg.run(["-f", "lavfi", "-i", "anullsrc=r=24000:cl=mono", "-t", "20", "-c:a", "libmp3lame", "voice.mp3"],
                     cwd=tmp_path)
    h = HybridAvatarProvider(FakeLip())
    assert h.estimate_cost_usd(20) == 1.5

    async def prog(f, m):
        pass

    res = await h.render(tmp_path / "p.png", tmp_path / "voice.mp3", (1080, 976), tmp_path, prog)
    assert abs(await ffmpeg.probe_duration(res.video_path) - 20) < 0.15 and res.cost_usd == 1.5
