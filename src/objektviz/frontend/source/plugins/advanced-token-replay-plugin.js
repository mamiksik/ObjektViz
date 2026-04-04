'use strict';

class AdvancedTokenReplayPlugin {
    // The advanced replay is inspired by
    // https://github.com/bupaverse/processanimateR/blob/master/docs/articles/use-token_scales_files/processanimater-libs-1.0.0/animation_tokens.js#L29
    BASE_SPEED_MULTIPLIER = 100000

    toCleanup = []
    svgNode = null
    svgSelection = null

    settings = null

    // totalDuration = null;
    isEnabled = false
    tokens = null
    speed = null
    alignment = null
    fixedDuration = null
    replayMetadata = null
    graphviz = null
    container = null

    install(target, objektviz) {
        // console.log(objektviz, target)
        this.svgSelection = target
        this.svgNode = target.node();
        this.container = target
            .append("g")
            .attr("id", "token-replay-group");

        const graphGroup = target.selectAll('#graph0')
        this.container.attr('transform', graphGroup.attr('transform'))
        const callback = () => {
            this.container.attr('transform',  graphGroup.attr('transform'))
        };
        const observer = new MutationObserver(callback);
        observer.observe(graphGroup.node(), { attributes: true });

        requestAnimationFrame(() => this.pollCurrentTime());
    }

    setPayload(payload) {
        this.container.html('')
        // Set the  --token-replay-spacing CSS variable to the value provided by the backend to 0px
        document.documentElement.style.setProperty('--token-replay-spacing', '1px');

        d3.selectAll('#slider-container').selectAll('svg').remove()

        this.toCleanup.forEach((clb) => clb())
        this.toCleanup = []
        console.log(payload)

        this.settings = payload.animation_preferences
        if (!this.settings.animate_tokens_flag) return

        if (payload.replay_metadata === null) return
        this.replayMetadata = payload.replay_metadata

        if (payload.tokens === null) return
        this.tokens = payload.tokens

        document.documentElement.style.setProperty('--token-replay-spacing', '101px');
        this.toCleanup.concat(this.setupSlider())
        this.setupReplay()
    }

    PLAYBACK_DURATION_SEC = 6

    // replaySpeed() {
    //     return (this.replayMetadata.total_duration_sec) * 60
        // return this.BASE_SPEED_MULTIPLIER * this.settings.token_animation_speed
    // }

    scaleDuration(sec) {
        return (sec / this.replayMetadata.total_duration_sec) * (this.PLAYBACK_DURATION_SEC * this.settings.token_animation_speed)
    }

    unscaleDuration(sec) {
        return (sec / (this.PLAYBACK_DURATION_SEC * this.settings.token_animation_speed)) * this.replayMetadata.total_duration_sec
    }

    pollCurrentTime() {
        if (this.replayMetadata !== null){
            this.slider.silentValue(this.playBackProgress())
            // Loop back to start, if we reached end of the playback
            if (this.svgNode.getCurrentTime() > this.scaleDuration(this.replayMetadata.total_duration_sec)) {
                this.svgNode.setCurrentTime(0)
            }
        }

        requestAnimationFrame(() => this.pollCurrentTime());
    }

    playBackProgress() {
        const currentTime = this.svgNode.getCurrentTime();
        if (!this.isRealtimeAlignment()) {
            // return currentTime / this.scaleDuration(this.replayMetadata.total_duration_sec) * 100;
            return currentTime / this.scaleDuration(this.replayMetadata.total_duration_sec) * 100;
        }

        const startDate = new Date(this.replayMetadata.start_date);
        const elapesMs = (startDate.getTime()) + this.unscaleDuration(currentTime) * 1000
        return new Date(elapesMs)
    }

    isRealtimeAlignment () {
        return this.settings.token_animation_alignment === "Real-time"
    }

    setupSlider() {
        this.slider = d3.sliderHorizontal()
            .ticks(1200 / 100)
            .displayValue(true);

        if (this.isRealtimeAlignment()) {
            this.slider = this.slider
                .min(new Date(this.replayMetadata['start_date']))
                .max(new Date(this.replayMetadata['end_date']))
                .displayFormat(d3.timeFormat("%x %X"))
        } else {
            this.slider = this.slider
                .min(0)
                .max(100)
                .displayFormat(d => `${d3.format(".0f")(d)}%`)
        }

        // On user interaction, set the svg setCurrentTime to the selected value
        this.slider.on('onchange', (val) => {
            const startDate = new Date(this.replayMetadata.start_date)
            const elapsedSec = this.isRealtimeAlignment()
                ? this.scaleDuration((val - startDate) / 1000)
                : (val / 100) * (this.PLAYBACK_DURATION_SEC * this.settings.token_animation_speed);
            this.svgNode.setCurrentTime(elapsedSec)
        })

        const sliderContainer = d3.selectAll("#slider-container")
            .append("svg")
            .attr("class", "processanimater-control")
            .attr("width", 1200 - 50)
            .attr("height", 70);

        const sliderGroup  = sliderContainer
            .append("g")
            .attr('transform', 'translate(60, 30)')
            .call(this.slider);

        const playbackControlGroup = sliderContainer
            .append("g")
            .attr("transform", "translate(0,12)");

        // Inspired by https://gist.github.com/guilhermesimoes/fbe967d45ceeb350b765
        const
            playIcon = "M11,10 L18,13.74 18,22.28 11,26 M18,13.74 L26,18 26,18 18,22.28",
            pauseIcon = "M11,10 L17,10 17,26 11,26 M20,10 L26,10 26,26 20,26";

        const playPauseButton = playbackControlGroup
            .append("g")
            .attr("style", "pointer-events: bounding-box")
            .append("path")
            .attr("d", this.svgNode.animationsPaused() ? playIcon : pauseIcon)
            .on('mouseenter', (event, d) => {
                playPauseButton
                    .attr('transform', 'translate(-2, -2) scale(1.1)')
            })
            .on('mouseout', () => {
                playPauseButton
                    .attr('transform', 'translate(0, 0) scale(1)')
            })

        playPauseButton.on("click", () => {
            let icon = null
            if (this.svgNode.animationsPaused()) {
                this.svgNode.unpauseAnimations()
                icon = pauseIcon
            } else {
                this.svgNode.pauseAnimations()
                icon = playIcon
            }

            playPauseButton
                .transition()
                .duration(100)
                .attr("d", icon);
        });

        // Lastly on screen change recompute the slider size and ticks count
        const resizeObserver = new ResizeObserver((entries) => {
            const width = entries[0].contentRect.width
            sliderContainer.attr('width', width)
            this.slider = this.slider
                .width(width - 80)
                .ticks(width / 100)
            sliderGroup.call(this.slider)
        })

        resizeObserver.observe(document.getElementById(GRAPH_DIV_ID))
        return [() => resizeObserver.disconnect()]
    }

    setupReplay() {
        this.svgSelection
            .selectAll("g.edge")
            .each(function (parent) {
                d3.select(this).selectAll("path").attr("id", `${parent.attributes.id}-path` )
            })

        const tokens = this.container
            .selectAll('g.token-group')
            .data(this.tokens)
            .enter()
            .append('g')
            .classed('token-group', true)
            .attr("data-entity-id", (d) => d['entity_id'])
            .attr("id", (d) => d['element_id'])
            .attr('display', "none")

        tokens
            .append('set')
            .attr('attributeName', "display")
            .attr('to', 'none')
            .attr('begin', (d) => `0s`)
            .attr('fill', "freeze")

        tokens
            .append('set')
            .attr('attributeName', "display")
            .attr('to', 'none')
            .attr('begin', (d) => `${this.scaleDuration(d.replay_duration_sec)}s`)
            .attr('fill', "freeze")

        tokens
            .selectAll(null)
            .data((d) => {return d.segments})
            .enter()
            .append('set')
            .attr('attributeName', "display")
            .attr('to', "block")
            .attr('begin', (d) => `${this.scaleDuration(d.start_offset_sec)}s`)
            .attr('fill', "freeze")

        // Add tokens
        const circles = tokens
            .append("circle")
            .attr('id', (d) => {return d['element_id']})
            .attr('r','10px')
            .attr('fill', 'black')
            .attr('stroke', 'black')
            .attr('stroke-width', '2px')

        circles
            .selectAll(null)
            .data((d) => { return d.segments})
            .enter()
            .append('set')
            .attr('attributeName', "fill")
            .attr('to', (d) => d.color)
            .attr('begin', (d) => `${this.scaleDuration(d.start_offset_sec)}s`)
            .attr('fill', "freeze")

        circles
                .append("title")
                .text((d) => d['entity_id'])

        // Add path tracking
        tokens
            .selectAll(null)
            .data((d) => { return d.segments})
            .enter()
            .append('animateMotion')
            .attr('begin', (d) => `${this.scaleDuration(d.start_offset_sec)}s`)
            .attr('dur', (d) => {return `${this.scaleDuration(d.duration_sec)}s`})
            .attr('fill', "freeze")
            .attr('rotate', "auto")
            .append("mpath")
            .attr("href", (d) => "#" + d.dfc_element_id + "-path");

    }



    transitionDuration(durationInMinutes) {
        return this.fixedDuration ? 1 : durationInMinutes
    }

    applyStyles() {

    }
}
