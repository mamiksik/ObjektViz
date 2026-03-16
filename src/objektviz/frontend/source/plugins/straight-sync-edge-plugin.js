'use strict';

class StraightSyncEdgePlugin {
    install(svg, objektviz) {
        this.straightenSyncEdges(svg)
        this.moveSyncEdgesToStart(svg)
    }

    straightenSyncEdges(svg) {
        // Find all sync edges
        const syncEdges = svg.selectAll('.sync-edge');

        syncEdges.each(function() {
            const edge = d3.select(this);
            const pathElement = edge.select('path');
            const pathNode = pathElement.node();

            // Get the total length and use it to find start and end points
            const pathLength = pathNode.getTotalLength();
            const startPoint = pathNode.getPointAtLength(0);
            const endPoint = pathNode.getPointAtLength(pathLength);

            // Store original path
            const originalPath = pathElement.attr('d');
            pathElement.attr('data-original-path', originalPath);

            // Create straight line
            const straightPath = `M${startPoint.x},${startPoint.y} L${endPoint.x},${endPoint.y}`;
            pathElement.attr('d', straightPath);
        });

        console.log(`Processed ${syncEdges.size()} sync edges`);
    }

    moveSyncEdgesToStart(svg) {
        // Find the main graph group (where edges are contained)
        const graphGroup = svg.selectWithoutDataPropagation('#graph0');
        // Find all sync edges
        const syncEdges = graphGroup.selectAll('.sync-edge');

        // Store sync edge nodes in an array
        const syncEdgeNodes = [];
        syncEdges.each(function() {
            syncEdgeNodes.push(this);
        });

        // Insert each sync edge at the beginning of the graph group
        syncEdgeNodes.forEach((edgeNode, index) => {
            // Get the first child of the graph group
            const firstChild = graphGroup.node().firstChild;

            if (firstChild) {
                // Insert before the first child
                graphGroup.node().insertBefore(edgeNode, firstChild);
            } else {
                // If no children, just append
                graphGroup.node().appendChild(edgeNode);
            }
        });
    }

    setPayload() {}

    applyStyles() {}

}
