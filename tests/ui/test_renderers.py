from __future__ import annotations

from ui.renderers import build_figure


def test_renderer_accepts_only_known_columns_and_chart_types():
    result = {
        "columns": ["sales_channel", "net_revenue"],
        "rows": [
            {"sales_channel": "WEB", "net_revenue": 100},
            {"sales_channel": "STORE", "net_revenue": 80},
        ],
        "visualization": {
            "kind": "bar",
            "title": "Revenue by channel",
            "x": "sales_channel",
            "y": ["net_revenue"],
        },
    }
    figure = build_figure(result)
    assert figure is not None
    assert figure.layout.title.text == "Revenue by channel"


def test_renderer_rejects_unknown_chart_column():
    result = {
        "columns": ["sales_channel", "net_revenue"],
        "rows": [{"sales_channel": "WEB", "net_revenue": 100}],
        "visualization": {
            "kind": "bar",
            "title": "Unsafe",
            "x": "secret_column",
            "y": ["net_revenue"],
        },
    }
    assert build_figure(result) is None
