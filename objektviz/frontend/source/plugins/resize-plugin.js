'use strict';

class ResizeObserverPlugin {

    constructor() {
        // This plugin is sort of not a plugin, since it works on the global level.
        // It's not tied to the rendering of the graph, but rather ensures that the graph always
        // fills the whole available space.
        // But it is nice to have it as a plugin, since it is a self-contained piece of functionality
        // that can be easily reused and maintained.

        const resize = new ResizeObserver((entries) => {
            const width = entries[0].contentRect.width
            const height = entries[0].contentRect.height
            d3.select("#graph")
                .selectWithoutDataPropagation("svg")
                .attr('width', width)
                .attr('height', height)
        })

        addEventListener("resize", () => setFrameHeight(parent.window.innerHeight - SAFE_AREA))
        resize.observe(document.getElementById(GRAPH_DIV_ID))
    }

    install(target, objektviz) {}
    setPayload(payload) {}
    applyStyles() {}
}
