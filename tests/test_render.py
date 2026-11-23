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
