'use strict';

const INITIAL_RENDER_DELAY_MS = 250

const SET_COMPONENT_VALUE = "streamlit:setComponentValue"
const RENDER = "streamlit:render"
const COMPONENT_READY = "streamlit:componentReady"
const SET_FRAME_HEIGHT = "streamlit:setFrameHeight"

function _sendMessage(type, data) {
    // copy data into object
    var outboundData = Object.assign({
        isStreamlitMessage: true,
        type: type,
    }, data)

    if (type == SET_COMPONENT_VALUE) {
        console.debug("_sendMessage data: " + JSON.stringify(data))
        console.debug("_sendMessage outboundData: " + JSON.stringify(outboundData))
    }

    window.parent.postMessage(outboundData, "*")
}

function streamlitRender(renderFce) {
    let isFirstRender = true

    // Hook Streamlit's message events into a simple dispatcher of renderFce handlers
    window.addEventListener("message", (event) => {
        const processMessage = (event) => {
            if (event.data.type == RENDER) {
                // The event.data.args dict holds any JSON-serializable value
                // sent from the Streamlit client. It is already deserialized.
                renderFce(event.data.args)
            }
        }

        // We delay the first render so that the original setFrameHeight message has time to be processed
        // the delay is arbitrary chosen (to 'guarantee' the window is ready)
        if (isFirstRender) {
            setTimeout(() => {
                processMessage(event)
                isFirstRender = false;
            }, INITIAL_RENDER_DELAY_MS)
        } else {
            processMessage(event)
        }
    })

    _sendMessage(COMPONENT_READY, {apiVersion: 1});
    // setFrameHeight(parent.window.innerHeight - SAFE_AREA)

    // Component should be mounted by Streamlit in an iframe, so try to autoset the iframe height.
    window.addEventListener("load", () => {
        window.setTimeout(function () {
            setFrameHeight(parent.window.innerHeight - SAFE_AREA)
        }, 0)
    })
}

function setFrameHeight(height) {
    _sendMessage(SET_FRAME_HEIGHT, {height: height})
}

// The `data` argument can be any JSON-serializable value.
function notifyHost(data) {
    _sendMessage(SET_COMPONENT_VALUE, data)
}