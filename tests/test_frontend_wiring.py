"""Tests for REDESIGN-SEAM helpers in app.py (Step 3/5 live wiring).

Statistical association only; proxy sanity markers adjacent to numbers.
"""

from __future__ import annotations

import inspect
import re
import sys
import types

LOWER_SNAKE = re.compile(r"^[a-z][a-z0-9_]*$")
TAG = "(proxy sanity, not proof)"


class _FakeState(dict):
    def __getattr__(self, name: str) -> object:
        try:
            return self[name]
        except KeyError as ex:
            raise AttributeError(name) from ex

    def __setattr__(self, name: str, value: object) -> None:
        self[name] = value


class _DummyCtx:
    def __enter__(self) -> _DummyCtx:
        return self

    def __exit__(self, *args: object) -> bool:
        return False


def _make_fake_streamlit() -> types.ModuleType:
    mod = types.ModuleType("streamlit")

    def _cache_data(*args: object, **kwargs: object):  # type: ignore[no-untyped-def]
        def _dec(fn):  # type: ignore[no-untyped-def]
            return fn

        if args and callable(args[0]) and len(args) == 1 and not kwargs:
            return args[0]
        return _dec

    def _columns(spec=None, *args: object, **kwargs: object):  # type: ignore[no-untyped-def]
        n = spec if isinstance(spec, int) else len(spec or [1, 2])
        return [_DummyCtx() for _ in range(int(n))]

    mod.set_page_config = lambda *a, **k: None
    mod.markdown = lambda *a, **k: None
    mod.caption = lambda *a, **k: None
    mod.columns = _columns  # type: ignore[attr-defined]
    mod.radio = lambda *a, **k: 1
    mod.multiselect = lambda *a, **k: ["Tomato"]
    mod.slider = lambda *a, **k: 5
    mod.number_input = lambda *a, **k: 0.0
    mod.button = lambda *a, **k: False
    mod.expander = lambda *a, **k: _DummyCtx()
    mod.plotly_chart = lambda *a, **k: None
    mod.rerun = lambda *a, **k: None
    mod.cache_data = _cache_data  # type: ignore[attr-defined]
    mod.session_state = _FakeState({"current_step": 1})  # type: ignore[attr-defined]
    mod.query_params = {}  # type: ignore[attr-defined]
    mod.sidebar = _DummyCtx()  # type: ignore[attr-defined]
    return mod


def _ensure_app_imported():  # type: ignore[no-untyped-def]
    if "app" in sys.modules:
        return sys.modules["app"]
    fake_st = _make_fake_streamlit()
    sys.modules["streamlit"] = fake_st
    plotly_mod = types.ModuleType("plotly")
    go_mod = types.ModuleType("plotly.graph_objects")

    class _Fig:
        def __init__(self, *a: object, **k: object) -> None:
            pass

        def update_layout(self, *a: object, **k: object) -> None:
            pass

    class _Bar:
        def __init__(self, *a: object, **k: object) -> None:
            pass

    go_mod.Figure = _Fig  # type: ignore[attr-defined]
    go_mod.Bar = _Bar  # type: ignore[attr-defined]
    sys.modules["plotly"] = plotly_mod
    sys.modules["plotly.graph_objects"] = go_mod
    import importlib.util
    from pathlib import Path

    app_path = Path(__file__).resolve().parent.parent / "app.py"
    spec = importlib.util.spec_from_file_location("app", str(app_path))
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules["app"] = module
    spec.loader.exec_module(module)
    return module


app = _ensure_app_imported()


def test_live_maturity_keys_lower_snake() -> None:
    out = app._live_maturity({"cn": 28.0, "ph": 6.8, "moist_pct": 55.0})
    assert all(LOWER_SNAKE.match(k) for k in out)
    for key in ("p_mature", "p_mature_note", "raw_score", "disclaimer"):
        assert key in out


def test_live_maturity_in_unit_interval() -> None:
    for blend in (
        {"cn": 28.0, "ph": 6.8, "moist_pct": 55.0, "score": 0.7},
        {"cn": 18.0, "ph": 7.1, "moist_pct": 55.0, "score": 0.2},
        {"cn": 40.0, "ph": 5.0, "moist_pct": 30.0, "score": -3.0},
    ):
        out = app._live_maturity(blend)
        assert 0.0 <= float(out["p_mature"]) <= 1.0
    assert app._live_maturity({})["p_mature_note"] == TAG


def test_live_maturity_deterministic() -> None:
    blend = {"cn": 27.0, "ph": 6.5, "moist_pct": 56.0, "score": 0.65}
    assert app._live_maturity(blend) == app._live_maturity(blend)


def test_live_maturity_fallback_on_bad_input() -> None:
    out = app._live_maturity({"cn": "bad", "ph": None})  # type: ignore[dict-item]
    assert 0.0 <= float(out["p_mature"]) <= 1.0
    assert out["p_mature_note"] == TAG
    out2 = app._live_maturity("not-a-dict")  # type: ignore[arg-type]
    assert 0.0 <= float(out2["p_mature"]) <= 1.0


def test_render_warns_triggers_low() -> None:
    warns = app._render_warns({"cn": 28.0, "ph": 6.8, "moist_pct": 26.0})
    assert len(warns) == 1
    assert warns[0]["warn_code"] == "moist_low"


def test_render_warns_triggers_high() -> None:
    warns = app._render_warns({"cn": 28.0, "ph": 6.8, "moist_pct": 72.0})
    assert len(warns) == 1
    assert warns[0]["warn_code"] == "moist_high"


def test_render_warns_empty_in_band() -> None:
    assert app._render_warns({"cn": 28.0, "ph": 6.8, "moist_pct": 55.0}) == []
    assert app._render_warns({"cn": 28.0, "ph": 6.8, "moist_pct": 50.0}) == []
    assert app._render_warns({"cn": 28.0, "ph": 6.8, "moist_pct": 60.0}) == []


def test_render_warns_fallback_on_bad_input() -> None:
    assert app._render_warns({}) == []
    assert app._render_warns({"moist_pct": "bad"}) == []


def test_helpers_pure_no_streamlit_calls() -> None:
    for fn in (app._live_maturity, app._render_warns):
        src = inspect.getsource(fn)
        assert "streamlit" not in src
        assert "st." not in src
        assert "st(" not in src


def test_helpers_tag_and_disclaimer() -> None:
    out = app._live_maturity({"cn": 28.0, "ph": 6.8, "moist_pct": 55.0})
    assert TAG in out["p_mature_note"]
    assert TAG in out["disclaimer"]
    warns = app._render_warns({"cn": 28.0, "ph": 6.8, "moist_pct": 26.0})
    assert TAG in warns[0]["warn_text"]
