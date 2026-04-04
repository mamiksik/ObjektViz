'use strict';

class ClickInteractionPlugin {
    selectedElementId = null
    objektviz = null

    selectedElement() {
        return d3.select(document.getElementById(this.selectedElementId))
    }

    install(target, objektviz) {
        this.objektviz = objektviz
    }

    setPayload(payload) {
        const that = this;
        const selection = d3.selectAll('.node,.dfc-edge,.token-group');

        selection.on("click", function () {
            that.onLeftClick(d3.select(this)) //TODO: replace with SelectAll
        })

        selection.on('contextmenu', function (e) {
            console.log(e)
            console.log(d3.select(this))
            e.preventDefault();
            that.onRightClick(d3.select(this)) //TODO: replace with SelectAll
        })

        this.setSelectedElement(payload.selected_element_id)
        console.log("Payload", this.selectedElementId)
    }

    setSelectedElement(id) {
        if (this.selectedElementId !== null && this.selectedElementId !== id) {
            d3Helpers.restoreElementStyle(this.selectedElement())
        }
        this.selectedElementId = id
    }

    onLeftClick(target) {
        let id = target.attr('id')
        if (id === this.selectedElementId) {
            id = null;
        }

        const classes = target.attr('class').split(' ')
        const type =
            classes.includes('node') ? 'node'
                : (classes.includes('dfc-edge') ? 'edge'
                    : (classes.includes('token-group') ? 'token-group' : null)
        )

        this.setSelectedElement(id)
        // console.log("Selected element id", this.selectedElementId, target.attr('class'), target.attr('id'))
        notifyHost({ value: {
            'eventType': 'LeftClick',
            'type': type,
            'elementId': id
        }, dataType: 'json'})
        dispatchEvent(new CustomEvent("objektviz:applyStyles"))
    }

    onRightClick(target) {
        notifyHost({ value: {
                'eventType': 'RightClick',
                'type': target.attr('class'),
                'elementId': target.attr('id')
            }, dataType: 'json'})
    }

    applyStyles() {
        const selectedElement = this.selectedElement()
        d3Helpers.setElementStyle(selectedElement, defaultConfig.colorSelected)
    }
}
