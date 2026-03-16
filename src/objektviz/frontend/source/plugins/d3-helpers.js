'use strict';

const d3Helpers = {
    storeOriginalStroke: (selection) => selection.attr('data-original-stroke', function () {
        return d3.select(this).attr('stroke')
    }),
    storeOriginalFill: (selection) => selection.attr('data-original-fill', function () {
        return d3.select(this).attr('fill')
    }),
    storeOriginalDashArray: (selection) => selection.attr('data-original-stroke-dasharray', function () {
        return d3.select(this).attr('stroke-dasharray')
    }),
    setNodeStyle: (selection) =>  selection.style('filter', 'drop-shadow( 0px 0px 2px rgba(0, 0, 0, .35))'),
    setElementStyle: (selection, color) => {
        selection.selectAll('polygon')
            .attr("stroke", function () {
                return color
            })
            .attr("fill", function () {
                return color
            })

        selection.selectAll('path')
        .attr('stroke', function () {
            return color
        })
    },
    restoreElementStyle: (selection) => {
        selection.selectAll('path').attr("stroke-dasharray", function () {
            return d3.select(this).attr('data-original-stroke-dasharray')
        }).attr("stroke", function () {
            return d3.select(this).attr('data-original-stroke')
        })

        selection.selectAll('polygon').attr("stroke", function () {
            return d3.select(this).attr('data-original-stroke')
        }).attr("fill", function () {
            return d3.select(this).attr('data-original-fill')
        })
    },
    selectElementsOnID(selection, ids, invert = false) {
        return selection.filter((elem, i) => {
            if (invert) {
                return !ids.includes(elem.attributes['id'])
            } else {
                return ids.includes(elem.attributes['id'])
            }
        })
    },
    stopDashedLineAnimation(context, name) {
        // d3Helpers.restoreElementStyle(context)
        context.selectAll('path').interrupt(name)
    },
    startDashedLineAnimation(context, name) {
        context.selectAll('path')
            .attr("stroke-dasharray", function () {
                const strokeSize = d3.select(this).attr('stroke-width')
                return strokeSize + " " + strokeSize
            })
            .attr("stroke-dashoffset", function () {
                return d3.select(this).node().getTotalLength();
            })
            .transition(name)
            .ease(d3.easeLinear)
            .attr("stroke-dashoffset", 0)
            .duration(function () {
                return 60 * d3.select(this).node().getTotalLength();
            })
            .on("end", () => d3Helpers.startDashedLineAnimation(context));
    }
};
