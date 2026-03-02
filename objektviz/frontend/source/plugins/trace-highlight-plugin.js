'use strict';

class TraceHighlightPlugin {
    objektviz = null
    isEnabled = false
    traceElementIds = null

    install(target, objektviz) {
        this.objektviz = objektviz
    }

    setPayload(payload) {
        this.isEnabled = payload.animation_preferences.animate_active_elements_flag
        if (this.traceElementIds !== null && this.traceElementIds !== payload.active_element_ids) {
            const oldElements = d3Helpers.selectElementsOnID(
                d3.selectAll('.edge'),
                this.traceElementIds
            )
            d3Helpers.restoreElementStyle(oldElements)
            d3Helpers.stopDashedLineAnimation(oldElements, 'process-trace-animation')
        }

        this.traceElementIds = payload.active_element_ids
    }

    applyStyles() {
        if (this.isEnabled && this.traceElementIds != null) {
            const traceElements = d3Helpers.selectElementsOnID(
                d3.selectAll('.edge'),
                this.traceElementIds
            )

            d3Helpers.setElementStyle(traceElements, defaultConfig.colorTraceAnimation)
            d3Helpers.startDashedLineAnimation(traceElements, 'process-trace-animation')
        }
    }
}
