"""Tests for Step 2 specific-item waste entry (catalog + aliases + pool).

Screening estimates only; statistical association, not proof.
"""

from __future__ import annotations

import re
import sys
import types
from pathlib import Path

LOWER_SNAKE = re.compile(r"^[a-z][a-z0-9_]*$")


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
    mod.multiselect = lambda *a, **k: []
    mod.slider = lambda *a, **k: 5
    mod.number_input = lambda *a, **k: 0.0
    mod.text_input = lambda *a, **k: ""
    mod.data_editor = lambda rows, *a, **k: rows
    mod.button = lambda *a, **k: False
    mod.expander = lambda *a, **k: _DummyCtx()
    mod.plotly_chart = lambda *a, **k: None
    mod.rerun = lambda *a, **k: None
    mod.cache_data = _cache_data  # type: ignore[attr-defined]
    mod.column_config = types.SimpleNamespace(
        TextColumn=lambda *a, **k: None,
        NumberColumn=lambda *a, **k: None,
    )
    mod.session_state = _FakeState({"current_step": 1})  # type: ignore[attr-defined]
    mod.query_params = {}  # type: ignore[attr-defined]
    mod.sidebar = _DummyCtx()  # type: ignore[attr-defined]
    return mod


def _ensure_app_imported():  # type: ignore[no-untyped-def]
    if "app" in sys.modules:
        return sys.modules["app"]
    sys.modules["streamlit"] = _make_fake_streamlit()
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

    app_path = Path(__file__).resolve().parent.parent / "app.py"
    spec = importlib.util.spec_from_file_location("app", str(app_path))
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules["app"] = module
    spec.loader.exec_module(module)
    return module


app = _ensure_app_imported()
st = sys.modules["streamlit"]


def _set_state(**kwargs: object) -> None:
    st.session_state.clear()  # type: ignore[attr-defined]
    st.session_state.update(kwargs)  # type: ignore[attr-defined]


def test_catalog_has_25_known_ids() -> None:
    assert len(app.WASTE_CATALOG) == 25
    assert len({i for i, _, _ in app.WASTE_CATALOG}) == 25
    for ing_id, _name, _group in app.WASTE_CATALOG:
        assert LOWER_SNAKE.match(ing_id)


def test_alias_match_potato_onion_tomato() -> None:
    assert "vegetable_scraps" in app._catalog_search("potato")
    assert "onion_peels" in app._catalog_search("onion")
    assert "vegetable_scraps" in app._catalog_search("tomato")
    assert "banana_peel" in app._catalog_search("banana")
    assert app._catalog_search("potato")[0] == "vegetable_scraps"


def test_catalog_search_substring_and_empty() -> None:
    assert len(app._catalog_search("")) == 25
    assert "citrus_peels" in app._catalog_search("citrus")
    assert app._catalog_search("zzz-no-such-item") == []


def test_pool_from_items_grams_to_kg() -> None:
    pool = app._pool_from_items({"onion_peels": 500.0, "dry_leaves": 1000.0})
    assert pool == {"onion_peels": 0.5, "dry_leaves": 1.0}


def test_pool_from_items_drops_unknown_and_zero() -> None:
    pool = app._pool_from_items(
        {"onion_peels": 500.0, "free_text_item": 999.0, "dry_leaves": 0.0}
    )
    assert pool == {"onion_peels": 0.5}


def test_pool_truncates_to_top10_by_grams() -> None:
    items = {ing_id: float(100 * (n + 1)) for n, (ing_id, _, _) in enumerate(app.WASTE_CATALOG[:12])}
    pool = app._pool_from_items(items)
    assert len(pool) == 10
    assert "dry_leaves" not in pool  # smallest grams dropped deterministically


def test_pool_from_session_prefers_items() -> None:
    _set_state(
        waste_items={"onion_peels": 500.0},
        waste_kitchen=9.0,
        waste_coffee=9.0,
        waste_leaves=9.0,
        waste_grass=9.0,
    )
    assert app._waste_pool_from_session() == {"onion_peels": 0.5}


def test_pool_from_session_fallback_buckets() -> None:
    _set_state(waste_kitchen=2.0, waste_coffee=0.5, waste_leaves=0.0, waste_grass=0.0)
    st.session_state.pop("waste_items", None)  # type: ignore[attr-defined]
    pool = app._waste_pool_from_session()
    assert pool["coffee_grounds"] == 0.5
    assert pool["vegetable_scraps"] == 2.0
    assert len(pool) <= 10


def test_pool_from_session_empty_items_gives_empty() -> None:
    _set_state(
        waste_items={},
        waste_kitchen=2.0,
        waste_coffee=0.5,
        waste_leaves=3.0,
        waste_grass=1.5,
    )
    assert app._waste_pool_from_session() == {}


def test_grams_sum_total() -> None:
    _set_state(waste_items={"onion_peels": 500.0, "dry_leaves": 1500.0})
    assert app._total_waste_kg() == 2.0
