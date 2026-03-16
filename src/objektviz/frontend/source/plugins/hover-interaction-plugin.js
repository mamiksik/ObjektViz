'use strict';

class HoverInteractionPlugin {
    objektviz = null
    nodeEdgeMap = null
    edgeNodeMap = null
    nodeNodeMap = null

    isHovering = false
    relatedElementsIds = null;
    excludedElements = null;
    pathsToAnimate = null;
    pathEffectsEnabled = true;

    install(target, objektviz) {
        this.objektviz = objektviz
        const that = this;
        target.selectAll('.node,.edge')
            .on('mouseover', function (d, i) {
                const context = d3.select(this)
                that.onHoverStart(context)
            })
            .on('mouseout', function (d, i) {
                const context = d3.select(this)
                that.onHoverEnd(context)
            })
    }

    setPayload(payload) {
        this.edgeNodeMap = payload.edge_node_map
        this.nodeEdgeMap = payload.node_edge_map
        this.nodeNodeMap = payload.node_node_map
        this.pathEffectsEnabled = payload.enable_path_effects_on_hover
    }

    applyStyles() {
        if (this.isHovering) {
            if (this.pathEffectsEnabled) {
                d3Helpers.startDashedLineAnimation(this.pathsToAnimate, 'hover-animation')
            }

            this.excludedElements
                ?.transition()
                .duration('100')
                .attr('opacity', '.25')
        }
    }

    onHoverStart(context) {
        const id = context.attr('id')
        this.isHovering = true;

        if (context.attr('class') === 'edge') {
            this.pathsToAnimate = context;
            this.relatedElementsIds = this.edgeNodeMap[id].concat([id])
            this.excludedElements = d3Helpers.selectElementsOnID(d3.selectAll('.node,.edge'), this.relatedElementsIds, true)
        } else if (context.attr('class') === 'node') {
            this.pathsToAnimate = d3Helpers.selectElementsOnID(d3.selectAll('.edge'), this.nodeEdgeMap[id])
            this.relatedElementsIds = this.nodeEdgeMap[id].concat(this.nodeNodeMap[id]).concat([id])
            this.excludedElements = d3Helpers.selectElementsOnID(d3.selectAll('.node,.edge'), this.relatedElementsIds, true)
        }

        dispatchEvent(new CustomEvent("objektviz:applyStyles"))
    }

    onHoverEnd() {
        this.isHovering = false;
        this.excludedElements
            .transition()
            .duration('100')
            .attr('opacity', '1')
        d3Helpers.stopDashedLineAnimation(this.pathsToAnimate, 'hover-animation')
        this.excludedElements = null
        this.relatedElementsIds = null
        this.pathsToAnimate = null
        dispatchEvent(new CustomEvent("objektviz:applyStyles"));
    }
}
