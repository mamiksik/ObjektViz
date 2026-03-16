'use strict';

class ObjektViz {
    constructor(targetHtmlNode, plugins, config) {
        this.config = config
        this.plugins = plugins
        this.isBusy = false
        this.graphviz = d3
            .select(targetHtmlNode)
            .graphviz({
                tweenShapes: true,
                tweenPrecision: '10%',
                growEnteringEdges: false,
            })
            .scale(0.8)
            .transition(this.config.twiningTransitionFce);

        addEventListener("objektviz:applyStyles", () => this.applyStyles())
    }

    renderDot(dotSource, payload) {
        this.isBusy = true
        d3Helpers.restoreElementStyle(d3.selectAll('.node,.edge'))
        console.info("[RENDERING DOT]")

        const width = d3.select("#graph").node().getBoundingClientRect().width
        const height = d3.select("#graph").node().getBoundingClientRect().height

        this.graphviz
            .width(width)
            .height(height)
            .renderDot(dotSource)
            .on("end", () => {
                console.info("[RENDERING DONE]")
                d3.selectAll('title').text('')

                const nodes = d3.selectAll('.node');
                d3Helpers.setNodeStyle(nodes)
                d3Helpers.storeOriginalStroke(nodes.selectAll('path'))
                d3Helpers.storeOriginalFill(nodes.selectAll('path'))

                const edges = d3.selectAll('.edge');
                d3Helpers.storeOriginalStroke(edges.selectAll('path'))
                d3Helpers.storeOriginalFill(edges.selectAll('path'))

                const arrowsOnEdges = edges.selectAll('polygon')
                d3Helpers.storeOriginalFill(arrowsOnEdges)
                d3Helpers.storeOriginalDashArray(arrowsOnEdges)
                this.isBusy = false;

                const svgSelection = d3.select("#graph").selectWithoutDataPropagation("svg")

                // Remove the white background
                svgSelection.selectWithoutDataPropagation('polygon').remove()

                for (const plugin of this.plugins) {
                    plugin.install(svgSelection, this)
                }

                this.setPayload(payload)
                this.applyStyles()
            })
    };

    setPayload(payload) {
        if (this.isBusy) {return}

        for (const plugin of this.plugins) {
            plugin.setPayload(payload)
        }
    }

    applyStyles() {
        if (this.isBusy) {return}

        d3Helpers.restoreElementStyle(d3.selectAll('.node,.edge'))
        for (const plugin of this.plugins) {
            plugin.applyStyles()
        }
    }
}