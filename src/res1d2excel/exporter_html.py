# -*- coding: utf-8 -*-

# Author: Yi Wang
# this module exports dataframe dictionaries to interactive Plotly HTML pages

from __future__ import annotations

import html
import os
from typing import Mapping

import pandas as pd
from . import utilities_plotly


def export_plot_page(
        dfs: Mapping[str, pd.DataFrame],
        html_file_path: str,
        title: str,
        selector_label: str,
        resample_t: str | None = None
        ) -> None:
    """
    Export a set of dataframes to one HTML page with a dropdown plot filter.

    Parameters
    ----------
    dfs : Mapping[str, pd.DataFrame]
        Dictionary where each key becomes one selectable plot group.
    html_file_path : str
        Output HTML file path.
    title : str
        Page title.
    selector_label : str
        Label shown next to the dropdown.
    resample_t : str, optional
        Optional pandas resample interval.

    Returns
    -------
    None.
    """
    os.makedirs(os.path.dirname(os.path.abspath(html_file_path)), exist_ok=True)

    sections = []
    options = []

    for index, (name, df) in enumerate(dfs.items()):
        if df.empty or df.shape[1] == 0:
            continue

        plot_df = _prepare_dataframe(df, resample_t)
        if plot_df.empty or plot_df.shape[1] == 0:
            continue

        section_id = f"plot-section-{index}"
        options.append((section_id, name))
        sections.append(
            _plot_section_html(
                section_id,
                name,
                plot_df,
                include_plotlyjs=len(sections) == 0,
                active=len(sections) == 0
            )
        )

    page = _page_html(title, selector_label, options, sections)

    with open(html_file_path, "w", encoding="utf-8") as f:
        f.write(page)


def _prepare_dataframe(df: pd.DataFrame, resample_t: str | None) -> pd.DataFrame:
    plot_df = df.copy()

    if resample_t is not None and plot_df.shape[0] > 1:
        plot_df = plot_df.resample(resample_t).interpolate("index")

    return plot_df


def _plot_section_html(
        section_id: str,
        name: str,
        df: pd.DataFrame,
        include_plotlyjs: bool,
        active: bool
        ) -> str:
    plot_html = utilities_plotly.draw_graph(
        [df],
        to_html=True,
        include_plotlyjs=include_plotlyjs,
        title=str(name)
    )
    escaped_name = html.escape(str(name))
    section_class = "plot-section active" if active else "plot-section"

    return f"""
        <section id="{section_id}" class="{section_class}">
            <h2>{escaped_name}</h2>
            {plot_html}
        </section>
    """


def _page_html(
        title: str,
        selector_label: str,
        options: list[tuple[str, str]],
        sections: list[str]
        ) -> str:
    escaped_title = html.escape(title)
    escaped_selector_label = html.escape(selector_label)

    if not options:
        options_html = ""
        body_html = '<p class="empty-message">No plots were available to export.</p>'
    else:
        options_html = "\n".join(
            f'<option value="{section_id}">{html.escape(str(name))}</option>'
            for section_id, name in options
        )
        body_html = "\n".join(sections)

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{escaped_title}</title>
    <style>
        body {{
            margin: 0;
            color: #1f2933;
            font-family: Arial, Helvetica, sans-serif;
            background: #f5f7fa;
        }}

        header {{
            position: sticky;
            top: 0;
            z-index: 10;
            display: flex;
            align-items: center;
            justify-content: space-between;
            gap: 16px;
            padding: 14px 20px;
            border-bottom: 1px solid #d8dee8;
            background: #ffffff;
        }}

        h1 {{
            margin: 0;
            font-size: 20px;
            font-weight: 700;
        }}

        h2 {{
            margin: 0 0 12px;
            font-size: 16px;
        }}

        .filter {{
            display: flex;
            align-items: center;
            gap: 8px;
            min-width: 280px;
        }}

        label {{
            font-size: 14px;
            font-weight: 700;
            white-space: nowrap;
        }}

        select {{
            width: 100%;
            max-width: 420px;
            padding: 8px 10px;
            border: 1px solid #a7b1c2;
            border-radius: 4px;
            background: #ffffff;
            color: #1f2933;
        }}

        main {{
            padding: 20px;
        }}

        .plot-section {{
            display: none;
            padding: 16px;
            border: 1px solid #d8dee8;
            border-radius: 6px;
            background: #ffffff;
        }}

        .plot-section.active {{
            display: block;
        }}

        .empty-message {{
            margin: 0;
            padding: 16px;
            border: 1px solid #d8dee8;
            border-radius: 6px;
            background: #ffffff;
        }}

        @media (max-width: 720px) {{
            header {{
                align-items: stretch;
                flex-direction: column;
            }}

            .filter {{
                min-width: 0;
            }}
        }}
    </style>
</head>
<body>
    <header>
        <h1>{escaped_title}</h1>
        <div class="filter">
            <label for="plot-selector">{escaped_selector_label}</label>
            <select id="plot-selector" aria-label="{escaped_selector_label}">
                {options_html}
            </select>
        </div>
    </header>
    <main>
        {body_html}
    </main>
    <script>
        const selector = document.getElementById("plot-selector");
        const sections = Array.from(document.querySelectorAll(".plot-section"));

        function showSelectedPlot() {{
            const selectedId = selector.value;

            sections.forEach(section => {{
                section.classList.toggle("active", section.id === selectedId);
            }});

            const activePlot = document.querySelector(`#${{selectedId}} .plotly-graph-div`);
            if (activePlot) {{
                Plotly.Plots.resize(activePlot);
            }}
        }}

        if (selector && sections.length > 0) {{
            selector.addEventListener("change", showSelectedPlot);
            selector.value = sections[0].id;
            showSelectedPlot();
        }}
    </script>
</body>
</html>
"""
