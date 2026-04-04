/**
 * histogram_slider_frontend.js
 * Streamlit Custom Components v2 — ES module
 *
 * D3 is loaded as a static ES-module import so it is fully resolved before
 * this module executes. No global window.d3 is required.
 *
 * The exported default function is called by Streamlit on every render pass
 * (initial mount AND every time `data` changes). Per-instance state is kept
 * in the `instances` Map, keyed on `parentElement`, so multiple sliders on
 * the same page are fully independent.
 */

import * as d3 from "https://cdn.jsdelivr.net/npm/d3@7/+esm";

/* ═══════════════════════════════════════════════════════════════════════════
   HistogramSlider class
   (identical logic to the standalone histogram-slider.js, but `d3` is the
   module-scoped import above instead of a browser global)
═══════════════════════════════════════════════════════════════════════════ */

class HistogramSlider {
  /* ─── constructor ────────────────────────────────────────────────────── */

  constructor(options = {}) {
    this._container =
      typeof options.container === "string"
        ? document.querySelector(options.container)
        : options.container;

    if (!this._container)
      throw new Error("HistogramSlider: container not found");

    this._values = options.values ?? [];
    this._onChange = options.onChange ?? (() => {});
    this._binCount = options.bins ?? null;

    this._margin = { top: 24, right: 24, bottom: 24, left: 24 };
    this._totalW = options.width ?? 500;
    this._totalH = options.height ?? 120;
    this._w = this._totalW - this._margin.left - this._margin.right;
    this._h = this._totalH - this._margin.top - this._margin.bottom;

    this._selection = null;
    this._brush = null;
    this._brushG = null;
    this._silentBrushMove = false;

    this._build();
  }

  /* ─── public API ─────────────────────────────────────────────────────── */

  setValues(values) {
    this._values = values ?? [];
    this._selection = null;
    this._render();
    this._onChange(null);
  }

  setSelection(range, silent = false) {
    if (range == null) {
      this._clearBrush();
      return;
    }
    const x = this._xScale;
    if (!x) return;
    this._silentBrushMove = silent;
    this._brushG.call(this._brush.move, [x(range.min), x(range.max)]);
    this._silentBrushMove = false;
  }

  destroy() {
    if (this._wrapper && this._wrapper.parentNode) {
      this._wrapper.parentNode.removeChild(this._wrapper);
    }
  }

  /* ─── private: one-time DOM build ───────────────────────────────────── */

  _build() {
    this._wrapper = document.createElement("div");
    this._wrapper.className = "histogram-slider";
    this._container.appendChild(this._wrapper);

    this._root = d3
      .select(this._wrapper)
      .append("svg")
      .attr("width", this._totalW)
      .attr("height", this._totalH);

    this._g = this._root
      .append("g")
      .attr("transform", `translate(${this._margin.left},${this._margin.top})`);

    // Clip path — scoped to a unique ID so multiple instances don't clash
    const clipId = `hs-clip-${this._uid()}`;
    this._root
      .append("defs")
      .append("clipPath")
      .attr("id", clipId)
      .append("rect")
      .attr("width", this._w)
      .attr("height", this._h);

    this._barsG = this._g
      .append("g")
      .attr("class", "bars")
      .attr("clip-path", `url(#${clipId})`);

    this._xAxisG = this._g
      .append("g")
      .attr("class", "axis x-axis")
      .attr("transform", `translate(0,${this._h})`);

    this._yAxisG = this._g.append("g").attr("class", "axis y-axis");

    this._rangeLabel = this._g
      .append("text")
      .attr("class", "range-label")
      .attr("x", this._w / 2)
      .attr("y", -5);

    this._brushG = this._g.append("g").attr("class", "brush");

    this._render();
  }

  /* ─── private: (re)render scales + histogram + brush ────────────────── */

  _render() {
    const values = this._values;
    const hasData = values.length > 0;

    const extent = hasData ? d3.extent(values) : [0, 1];
    const pad = (extent[1] - extent[0]) * 0.02 || 0.5;

    this._xScale = d3
      .scaleLinear()
      .domain([extent[0] - pad, extent[1] + pad])
      .range([0, this._w]);

    const binGen = d3
      .bin()
      .domain(this._xScale.domain())
      .value((d) => d);

    if (this._binCount) binGen.thresholds(this._binCount);

    const bins = hasData ? binGen(values) : [];

    const yScale = d3
      .scaleLinear()
      .domain([0, d3.max(bins, (d) => d.length) || 1])
      .range([this._h, 0])
      .nice();

    // Bars
    const bars = this._barsG.selectAll(".bar").data(bins);
    const barsEnter = bars.enter().append("g").attr("class", "bar");
    barsEnter.append("rect");

    const barsMerge = barsEnter.merge(bars);
    barsMerge.attr(
      "transform",
      (d) => `translate(${this._xScale(d.x0)},${yScale(d.length)})`,
    );
    barsMerge
      .select("rect")
      .attr("width", (d) =>
        Math.max(0, this._xScale(d.x1) - this._xScale(d.x0) - 1),
      )
      .attr("height", (d) => this._h - yScale(d.length))
      .attr("class", (d) => this._barClass(d));

    bars.exit().remove();

    // Axes
    this._xAxisG.call(
      d3
        .axisBottom(this._xScale)
        .ticks(Math.min(10, Math.floor(this._w / 55)))
        .tickSizeOuter(0),
    );
    this._yAxisG.call(d3.axisLeft(yScale).ticks(4).tickSizeOuter(0));

    // Brush
    this._brush = d3
      .brushX()
      .extent([
        [0, 0],
        [this._w, this._h],
      ])
      .on("brush", (event) => this._onBrush(event, bins))
      .on("end", (event) => this._onBrushEnd(event, bins));

    this._brushG.call(this._brush);

    if (this._selection) {
      this._brushG.call(this._brush.move, [
        this._xScale(this._selection.min),
        this._xScale(this._selection.max),
      ]);
    }
  }

  /* ─── private: brush handlers ────────────────────────────────────────── */

  _onBrush(event, bins) {
    if (!event.selection) return;
    this._updateBarColors(event.selection, bins);
    this._updateRangeLabel(event.selection);
  }

  _onBrushEnd(event, bins) {
    if (!event.selection) {
      this._selection = null;
      this._updateBarColors(null, bins);
      this._updateRangeLabel(null);
      if (!this._silentBrushMove) this._onChange(null);
      return;
    }

    const [x0, x1] = event.selection;
    const min = this._xScale.invert(x0);
    const max = this._xScale.invert(x1);

    this._selection = { min, max };
    if (!this._silentBrushMove) this._onChange({ min, max });
  }

  /* ─── private: helpers ───────────────────────────────────────────────── */

  _clearBrush() {
    this._selection = null;
    this._brushG.call(this._brush.move, null);
    this._updateRangeLabel(null);
  }

  _updateBarColors(pixelSelection, bins) {
    this._barsG
      .selectAll(".bar rect")
      .attr("class", (d) => this._barClass(d, pixelSelection));
  }

  _barClass(d, pixelSelection) {
    if (!pixelSelection) return "";
    const barLeft = this._xScale(d.x0);
    const barRight = this._xScale(d.x1);
    const [selLeft, selRight] = pixelSelection;
    return barRight > selLeft && barLeft < selRight ? "selected" : "";
  }

  _updateRangeLabel(pixelSelection) {
    this._rangeLabel.selectAll("tspan").remove();

    if (!pixelSelection) return;

    const min = this._xScale.invert(pixelSelection[0]);
    const max = this._xScale.invert(pixelSelection[1]);
    const fmt = this._labelFormatter();

    const total = this._values.length;
    const inRange =
      total > 0 ? this._values.filter((v) => v >= min && v <= max).length : 0;
    const pct = total > 0 ? ((inRange / total) * 100).toFixed(1) : "0.0";

    this._rangeLabel.append("tspan").text(`${fmt(min)} – ${fmt(max)}`);
    this._rangeLabel
      .append("tspan")
      .attr("class", "range-pct")
      .text(`  (${pct}% of values)`);
  }

  _labelFormatter() {
    const extent = d3.extent(this._values);
    const range = extent[1] - extent[0];
    if (range === 0) return d3.format(".2f");
    if (range < 1) return d3.format(".3f");
    if (range < 100) return d3.format(".1f");
    return d3.format(",.0f");
  }

  _uid() {
    return Math.random().toString(36).slice(2, 9);
  }
}

/* ═══════════════════════════════════════════════════════════════════════════
   Per-instance registry
   Key:   parentElement (the DOM node Streamlit gives us)
   Value: { container, slider, observer, setStateValue, prevData }
         prevData: { values, height, bins, effectiveWidth, maxWidth }
═══════════════════════════════════════════════════════════════════════════ */

const instances = new Map();

/* ─── helpers ────────────────────────────────────────────────────────────── */

function valuesEqual(a, b) {
  if (a === b) return true;
  if (!Array.isArray(a) || !Array.isArray(b)) return false;
  if (a.length !== b.length) return false;
  for (let i = 0; i < a.length; i++) {
    if (a[i] !== b[i]) return false;
  }
  return true;
}

/**
 * Measure the usable pixel width of the container.
 * Falls back to maxWidth (if given) or 650 when the element has no layout yet.
 */
function measureWidth(parentElement, maxWidth) {
  const w = parentElement.offsetWidth;
  const effective = w > 10 ? w : (maxWidth ?? 650);
  return maxWidth != null ? Math.min(effective, maxWidth) : effective;
}

/**
 * Tear down the old slider container and build a fresh one.
 *
 * initialSelection  – { min, max } to pre-select, or null for no selection.
 * silent            – when true, the initial brush move does NOT fire onChange
 *                     (use this when Python's `default` already seeds the state,
 *                     avoiding an unnecessary extra rerun on first mount).
 *                     When false, onChange fires so Python gets the new state.
 *
 * Returns { container, slider }.
 */
function buildInstance(
  parentElement,
  values,
  width,
  height,
  bins,
  initialSelection = null,
  silent = true,
) {
  const container = document.createElement("div");
  parentElement.appendChild(container);

  const slider = new HistogramSlider({
    container,
    values,
    width,
    height,
    bins,
    // Always look up the latest setStateValue from the registry so that
    // callbacks fired by the ResizeObserver use the current reference.
    onChange: (range) => {
      const i = instances.get(parentElement);
      if (i) i.setStateValue("selection", range);
    },
  });

  if (initialSelection != null) {
    slider.setSelection(initialSelection, silent);
  }

  return { container, slider };
}

/* ═══════════════════════════════════════════════════════════════════════════
   v2 default export
   Called by Streamlit on every render pass (mount + data updates).
═══════════════════════════════════════════════════════════════════════════ */

export default function (component) {
  const { parentElement, data, setStateValue } = component;

  // Unpack props from Python.
  // `maxWidth` is optional — when null the slider fills the full container.
  // `initialSelection` is { min, max } computed from percentiles in Python,
  // or null when no default selection is configured.
  const values = Array.isArray(data?.values) ? data.values : [];
  const maxWidth = typeof data?.maxWidth === "number" ? data.maxWidth : null;
  const height = typeof data?.height === "number" ? data.height : 150;
  const bins = typeof data?.bins === "number" ? data.bins : null;
  const initialSelection =
    data?.initialSelection != null &&
    typeof data.initialSelection.min === "number" &&
    typeof data.initialSelection.max === "number"
      ? data.initialSelection
      : null;

  let inst = instances.get(parentElement);

  if (!inst) {
    /* ── First render: create slider + ResizeObserver ─────────────────── */
    const width = measureWidth(parentElement, maxWidth);
    const { container, slider } = buildInstance(
      parentElement,
      values,
      width,
      height,
      bins,
      initialSelection,
      /* silent */ true, // Python's `default` seeds the state — no rerun needed
    );

    inst = {
      container,
      slider,
      observer: null,
      setStateValue, // updated on every render (see else-branch)
      prevData: {
        values,
        maxWidth,
        height,
        bins,
        effectiveWidth: width,
        initialSelection,
      },
    };
    instances.set(parentElement, inst);

    // Rebuild the slider whenever the container is resized.
    const observer = new ResizeObserver(() => {
      const i = instances.get(parentElement);
      if (!i) return;

      const newWidth = measureWidth(parentElement, i.prevData.maxWidth);
      if (Math.abs(newWidth - i.prevData.effectiveWidth) < 2) return;

      // Preserve whatever selection the user currently has rather than
      // resetting to the default percentile just because the window resized.
      const currentSelection = i.slider._selection;

      i.container.remove();
      const { container: c, slider: s } = buildInstance(
        parentElement,
        i.prevData.values,
        newWidth,
        i.prevData.height,
        i.prevData.bins,
        currentSelection,
        /* silent */ true, // width change doesn't alter the logical selection
      );
      i.container = c;
      i.slider = s;
      i.prevData = { ...i.prevData, effectiveWidth: newWidth };
    });

    observer.observe(parentElement);
    inst.observer = observer;
  } else {
    /* ── Subsequent renders ───────────────────────────────────────────── */

    // Always refresh the setStateValue reference so the ResizeObserver
    // callback (and any pending brush callbacks) use the latest closure.
    inst.setStateValue = setStateValue;

    const pd = inst.prevData;
    const configChanged =
      height !== pd.height || bins !== pd.bins || maxWidth !== pd.maxWidth;

    const valsChanged = !valuesEqual(values, pd.values);

    if (configChanged || valsChanged) {
      /* Layout or data changed — rebuild.
         When data changes the default percentile range is re-applied
         (new dataset → fresh default selection makes sense).
         When only layout changed we preserve whatever the user had selected. */
      const width = measureWidth(parentElement, maxWidth);
      const selectionToApply = valsChanged
        ? initialSelection // new data → reset to default percentile
        : inst.slider._selection; // layout change only → keep current selection

      inst.container.remove();
      const { container, slider } = buildInstance(
        parentElement,
        values,
        width,
        height,
        bins,
        selectionToApply,
        /* silent */ !valsChanged, // non-silent only when data changed (need to sync Python state)
      );
      inst.container = container;
      inst.slider = slider;
      inst.prevData = {
        values,
        maxWidth,
        height,
        bins,
        effectiveWidth: width,
        initialSelection,
      };
    }
    /* If nothing changed (another widget triggered a rerun), do nothing —
       the slider keeps its current visual state and selection intact. */
  }

  /* ── Cleanup: called by Streamlit when the component is unmounted ──── */
  return () => {
    const i = instances.get(parentElement);
    if (i) {
      i.observer?.disconnect();
      i.container.remove();
      instances.delete(parentElement);
    }
  };
}
