"""
streamlit-histogram-slider
~~~~~~~~~~~~~~~~~~~~~~~~~~
A D3-based histogram range slider Streamlit component (v2 API).

Typical usage
-------------
    from histogram_slider import histogram_slider

    selection = histogram_slider(values, key="my_slider")
    if selection:
        print(selection["min"], selection["max"])
"""

from pathlib import Path
from typing import List, Optional

import math
import streamlit.components.v2 as components

import streamlit as st

__version__ = "0.2.0"

from streamlit.runtime.state import BindOption


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------


def _percentile(sorted_vals: list, p: float) -> float:
    """Return the p-th percentile (0–100) using linear interpolation.

    Equivalent to ``numpy.percentile(sorted_vals, p, interpolation='linear')``
    with no NumPy dependency.
    """
    n = len(sorted_vals)
    if n == 0:
        return 0.0
    if n == 1:
        return float(sorted_vals[0])
    idx = p / 100.0 * (n - 1)
    lo = int(idx)
    hi = min(lo + 1, n - 1)
    frac = idx - lo
    return sorted_vals[lo] + frac * (sorted_vals[hi] - sorted_vals[lo])


# ---------------------------------------------------------------------------
# Read frontend assets from the package directory at import time.
# ---------------------------------------------------------------------------

_DIR = Path(__file__).parent

_JS = (_DIR / "histogram_slider_frontend.js").read_text(encoding="utf-8")
_CSS = (_DIR / "histogram_slider.css").read_text(encoding="utf-8")

# ---------------------------------------------------------------------------
# Register the component once at module-import time.
#
# isolate_styles=False is intentional: SVG clip-path url(#id) references are
# resolved from the main document, which breaks inside a shadow DOM.  Our CSS
# is already fully namespaced under the `.histogram-slider` class, so there is
# no risk of style leakage into or from the rest of the Streamlit app.
# ---------------------------------------------------------------------------

_component = components.component(
    "histogram_slider",
    css=_CSS,
    js=_JS,
    isolate_styles=False,
)


# ---------------------------------------------------------------------------
# Public Python API
# ---------------------------------------------------------------------------


def histogram_slider(
    values: List[float],
    *,
    key: Optional[str] = None,
    width: Optional[int] = None,
    height: int = 150,
    bins: Optional[int] = None,
    default_percentile: Optional[tuple] = (5, 100),
    on_change=None,
    bind: BindOption=None,
) -> Optional[dict]:
    """Render a D3 histogram range slider and return the selected range.

       Drag across the histogram to select a value range.  The component returns
       the selection as soon as the brush is released, and returns
    ``None`` when
       the selection is cleared or no interaction has occurred yet.

       Parameters
       ----------
       values:
           List of numeric values to visualise in the histogram.
       key:
           An optional unique key.  Required when you render more than one slider
           on the same page.
       width:
           Maximum width of the histogram SVG in pixels.  Defaults to ``None``,
           which makes the slider fill the full width of its Streamlit column.
           Pass an integer to cap it at a specific pixel width.
       height:
           Height of the histogram SVG in pixels.  Defaults to ``150``.
       bins:
           Number of histogram bins.  Pass ``None`` (default) to let D3 choose
           automatically.
       default_percentile:
           A ``(lo, hi)`` tuple of percentile values (0–100) that defines the
           pre-selected range shown when the component first renders, and again
           whenever the ``values`` array changes.  Defaults to ``(5, 100)``,
           which trims the bottom 5 % of the distribution.  Pass ``None`` to
           start with no selection.
       on_change:
           Optional zero-argument callback executed whenever the selection
           changes.  Equivalent to the ``on_<state>_change`` pattern used by
           native Streamlit widgets.

       bind:
           Optional binding for the slider's selection to external state (e.g. query params).

       Returns
       -------
       dict or None
           ``{"min": float, "max": float}`` while a range is selected,
           or ``None`` when no selection is active.

       Examples
       --------
       Basic usage::

           import streamlit as st
           from histogram_slider import histogram_slider

           values = [1.2, 3.4, 2.1, 5.6, 4.3, 3.8, 2.9]
           selection = histogram_slider(values, key="demo")

           if selection:
               st.write(f"Range: {selection['min']:.2f} – {selection['max']:.2f}")

       Multiple independent sliders on the same page::

           age_range   = histogram_slider(ages,   key="ages",   bins=10)
           price_range = histogram_slider(prices, key="prices", bins=20)
    """
    # Compute the initial selection from the requested percentile range.
    # This is recalculated every render so it stays in sync when `values`
    # changes (e.g. the user picks a different dataset).
    import urllib
    query_key_min = f"{urllib.parse.quote(key)}_min" if key else None
    query_key_max = f"{urllib.parse.quote(key)}_max" if key else None
    if (_min := st.query_params.get_all(query_key_min)) and (_max := st.query_params.get_all(query_key_max)):
        initial_selection = {"min": float(_min[0]), "max": float(_max[0])}
    elif default_percentile is not None and len(values) > 0:
        lo_pct, hi_pct = default_percentile
        sv = sorted(values)
        initial_selection: Optional[dict] = {
            "min": _percentile(sv, lo_pct),
            "max": _percentile(sv, hi_pct),
        }
    else:
        initial_selection = None

    # Container height = SVG height + small buffer for the range label.
    container_height = height + 10

    result = _component(
        # Props forwarded to the JS `data` parameter
        data={
            "values": list(values),
            "maxWidth": width,  # None → null in JS → fill container
            "height": height,
            "bins": bins,  # None → null in JS → D3 auto-bins
            "initialSelection": initial_selection,
        },
        # Seed the Python-side state so the first render returns the default
        # percentile range without requiring an extra round-trip rerun.
        default={"selection": initial_selection},
        # Size the Streamlit container wrapper
        height=container_height,
        # Wire up the state callback
        on_selection_change=on_change or (lambda: None),
        key=key,
    )

    # Update query params if bind is set to "query_params"
    if bind == "query-params" and result and result.selection:
        if not math.isclose(result.selection["min"], initial_selection['min']):
            st.query_params[query_key_min] = round(result.selection["min"], 2)

        if not math.isclose(result.selection["max"], initial_selection['max']):
            st.query_params[query_key_max] = round(result.selection["max"], 2)

    # result is a BidiComponentResult; .selection holds the current range.
    return result.selection if result is not None else None
