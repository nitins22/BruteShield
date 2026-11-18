/**
 * BruteShield SOC Offline Canvas Chart Engine
 * Lightweight, zero-dependency data visualization library.
 */

window.SocCharts = (function() {
    'use strict';

    function setupCanvas(canvas) {
        const dpr = window.devicePixelRatio || 1;
        const rect = canvas.getBoundingClientRect();
        canvas.width = rect.width * dpr;
        canvas.height = rect.height * dpr;
        const ctx = canvas.getContext('2d');
        ctx.scale(dpr, dpr);
        return { ctx, width: rect.width, height: rect.height };
    }

    // 1. Interactive Area / Line Chart
    class LineChart {
        constructor(canvasId, options = {}) {
            this.canvas = document.getElementById(canvasId);
            if (!this.canvas) return;
            this.options = Object.assign({
                labels: [],
                datasets: [], // [{ label, data, color, fillColor }]
                padding: { top: 20, right: 20, bottom: 35, left: 45 },
                showGrid: true,
                gridColor: '#1e293b',
                textColor: '#94a3b8',
                font: '11px -apple-system, sans-serif'
            }, options);

            this.hoverIndex = -1;
            this.initEvents();
            this.render();
        }

        initEvents() {
            this.canvas.addEventListener('mousemove', (e) => {
                const rect = this.canvas.getBoundingClientRect();
                const mouseX = e.clientX - rect.left;
                const plotWidth = rect.width - this.options.padding.left - this.options.padding.right;
                const numPoints = this.options.labels.length;
                if (numPoints <= 1) return;
                
                const step = plotWidth / (numPoints - 1);
                const relX = mouseX - this.options.padding.left;
                let idx = Math.round(relX / step);
                idx = Math.max(0, Math.min(numPoints - 1, idx));
                if (idx !== this.hoverIndex) {
                    this.hoverIndex = idx;
                    this.render();
                }
            });

            this.canvas.addEventListener('mouseleave', () => {
                this.hoverIndex = -1;
                this.render();
            });

            window.addEventListener('resize', () => {
                this.render();
            });
        }

        setData(labels, datasets) {
            this.options.labels = labels;
            this.options.datasets = datasets;
            this.render();
        }

        render() {
            if (!this.canvas) return;
            const { ctx, width, height } = setupCanvas(this.canvas);
            const p = this.options.padding;
            const plotW = width - p.left - p.right;
            const plotH = height - p.top - p.bottom;

            ctx.clearRect(0, 0, width, height);

            const labels = this.options.labels;
            const datasets = this.options.datasets;
            if (!labels.length || !datasets.length) {
                // Empty state text
                ctx.fillStyle = this.options.textColor;
                ctx.font = this.options.font;
                ctx.textAlign = 'center';
                ctx.fillText('Awaiting telemetry events...', width / 2, height / 2);
                return;
            }

            // Find Max Value
            let maxVal = 0;
            datasets.forEach(ds => {
                ds.data.forEach(v => { if (v > maxVal) maxVal = v; });
            });
            maxVal = Math.max(5, Math.ceil(maxVal * 1.15));

            // Draw Y-Axis Gridlines & Ticks
            const yTicks = 4;
            ctx.fillStyle = this.options.textColor;
            ctx.font = this.options.font;
            ctx.textAlign = 'right';
            ctx.textBaseline = 'middle';

            for (let i = 0; i <= yTicks; i++) {
                const tickVal = Math.round((maxVal / yTicks) * i);
                const y = p.top + plotH - (i / yTicks) * plotH;

                if (this.options.showGrid) {
                    ctx.strokeStyle = this.options.gridColor;
                    ctx.lineWidth = 1;
                    ctx.beginPath();
                    ctx.moveTo(p.left, y);
                    ctx.lineTo(p.left + plotW, y);
                    ctx.stroke();
                }

                ctx.fillText(tickVal.toString(), p.left - 8, y);
            }

            // Draw X-Axis Ticks
            const stepX = labels.length > 1 ? plotW / (labels.length - 1) : plotW;
            ctx.textAlign = 'center';
            ctx.textBaseline = 'top';

            // Limit label density on small screens
            const labelSkip = Math.max(1, Math.ceil(labels.length / 8));
            labels.forEach((label, i) => {
                if (i % labelSkip === 0 || i === labels.length - 1) {
                    const x = p.left + i * stepX;
                    ctx.fillText(label, x, p.top + plotH + 8);
                }
            });

            // Draw Datasets
            datasets.forEach(ds => {
                const pts = ds.data.map((v, i) => ({
                    x: p.left + i * stepX,
                    y: p.top + plotH - (v / maxVal) * plotH
                }));

                // Area Fill
                if (ds.fillColor) {
                    ctx.fillStyle = ds.fillColor;
                    ctx.beginPath();
                    ctx.moveTo(pts[0].x, p.top + plotH);
                    pts.forEach(pt => ctx.lineTo(pt.x, pt.y));
                    ctx.lineTo(pts[pts.length - 1].x, p.top + plotH);
                    ctx.closePath();
                    ctx.fill();
                }

                // Line Stroke
                ctx.strokeStyle = ds.color || '#38bdf8';
                ctx.lineWidth = 2.5;
                ctx.beginPath();
                pts.forEach((pt, i) => {
                    if (i === 0) ctx.moveTo(pt.x, pt.y);
                    else ctx.lineTo(pt.x, pt.y);
                });
                ctx.stroke();

                // Draw Dots
                pts.forEach((pt, i) => {
                    ctx.fillStyle = ds.color || '#38bdf8';
                    ctx.beginPath();
                    ctx.arc(pt.x, pt.y, i === this.hoverIndex ? 5 : 2.5, 0, Math.PI * 2);
                    ctx.fill();
                });
            });

            // Interactive Hover Crosshair and Tooltip
            if (this.hoverIndex >= 0 && this.hoverIndex < labels.length) {
                const hoverX = p.left + this.hoverIndex * stepX;

                // Vertical Crosshair
                ctx.strokeStyle = '#38bdf8';
                ctx.lineWidth = 1;
                ctx.setLineDash([4, 4]);
                ctx.beginPath();
                ctx.moveTo(hoverX, p.top);
                ctx.lineTo(hoverX, p.top + plotH);
                ctx.stroke();
                ctx.setLineDash([]);

                // Tooltip Box
                const ttX = Math.min(width - 130, Math.max(10, hoverX - 60));
                const ttY = p.top + 6;
                ctx.fillStyle = 'rgba(15, 23, 42, 0.95)';
                ctx.strokeStyle = '#334155';
                ctx.lineWidth = 1;
                ctx.beginPath();
                ctx.roundRect(ttX, ttY, 120, 24 + datasets.length * 16, 6);
                ctx.fill();
                ctx.stroke();

                ctx.textAlign = 'left';
                ctx.textBaseline = 'top';
                ctx.fillStyle = '#f8fafc';
                ctx.font = 'bold 10px monospace';
                ctx.fillText(labels[this.hoverIndex], ttX + 8, ttY + 6);

                datasets.forEach((ds, dsi) => {
                    ctx.fillStyle = ds.color || '#38bdf8';
                    ctx.font = '10px sans-serif';
                    ctx.fillText(`${ds.label}: ${ds.data[this.hoverIndex]}`, ttX + 8, ttY + 20 + dsi * 15);
                });
            }
        }
    }

    // 2. Donut / Ring Chart
    class DonutChart {
        constructor(canvasId, options = {}) {
            this.canvas = document.getElementById(canvasId);
            if (!this.canvas) return;
            this.options = Object.assign({
                data: [], // [{ label, value, color }]
                innerRadiusRatio: 0.65,
                centerText: '',
                centerSub: ''
            }, options);

            this.render();
            window.addEventListener('resize', () => this.render());
        }

        setData(data, centerText = '', centerSub = '') {
            this.options.data = data;
            if (centerText) this.options.centerText = centerText;
            if (centerSub) this.options.centerSub = centerSub;
            this.render();
        }

        render() {
            if (!this.canvas) return;
            const { ctx, width, height } = setupCanvas(this.canvas);
            ctx.clearRect(0, 0, width, height);

            const total = this.options.data.reduce((sum, item) => sum + (item.value || 0), 0);
            const cx = width / 2;
            const cy = height / 2;
            const radius = Math.min(cx, cy) - 10;
            const innerRadius = radius * this.options.innerRadiusRatio;

            if (total === 0) {
                // Empty state ring
                ctx.strokeStyle = '#1e293b';
                ctx.lineWidth = radius - innerRadius;
                ctx.beginPath();
                ctx.arc(cx, cy, (radius + innerRadius) / 2, 0, Math.PI * 2);
                ctx.stroke();

                ctx.fillStyle = '#94a3b8';
                ctx.font = '11px sans-serif';
                ctx.textAlign = 'center';
                ctx.textBaseline = 'middle';
                ctx.fillText('No activity', cx, cy);
                return;
            }

            let startAngle = -Math.PI / 2;

            this.options.data.forEach(slice => {
                if (!slice.value) return;
                const sliceAngle = (slice.value / total) * (Math.PI * 2);
                const endAngle = startAngle + sliceAngle;

                ctx.fillStyle = slice.color || '#38bdf8';
                ctx.beginPath();
                ctx.arc(cx, cy, radius, startAngle, endAngle);
                ctx.arc(cx, cy, innerRadius, endAngle, startAngle, true);
                ctx.closePath();
                ctx.fill();

                startAngle = endAngle;
            });

            // Center Text
            if (this.options.centerText) {
                ctx.fillStyle = '#f8fafc';
                ctx.font = 'bold 18px monospace';
                ctx.textAlign = 'center';
                ctx.textBaseline = 'middle';
                ctx.fillText(this.options.centerText, cx, cy - 6);

                if (this.options.centerSub) {
                    ctx.fillStyle = '#94a3b8';
                    ctx.font = '10px sans-serif';
                    ctx.fillText(this.options.centerSub, cx, cy + 12);
                }
            }
        }
    }

    // 3. Horizontal / Vertical Bar Chart
    class BarChart {
        constructor(canvasId, options = {}) {
            this.canvas = document.getElementById(canvasId);
            if (!this.canvas) return;
            this.options = Object.assign({
                labels: [],
                data: [],
                color: '#38bdf8',
                padding: { top: 20, right: 20, bottom: 35, left: 45 }
            }, options);

            this.render();
            window.addEventListener('resize', () => this.render());
        }

        setData(labels, data) {
            this.options.labels = labels;
            this.options.data = data;
            this.render();
        }

        render() {
            if (!this.canvas) return;
            const { ctx, width, height } = setupCanvas(this.canvas);
            const p = this.options.padding;
            const plotW = width - p.left - p.right;
            const plotH = height - p.top - p.bottom;

            ctx.clearRect(0, 0, width, height);

            const labels = this.options.labels;
            const data = this.options.data;
            if (!labels.length || !data.length) {
                ctx.fillStyle = '#94a3b8';
                ctx.font = '11px sans-serif';
                ctx.textAlign = 'center';
                ctx.fillText('No comparative data recorded', width / 2, height / 2);
                return;
            }

            let maxVal = Math.max(5, ...data);
            maxVal = Math.ceil(maxVal * 1.15);

            // Gridlines
            const ticks = 4;
            ctx.fillStyle = '#94a3b8';
            ctx.font = '10px sans-serif';
            ctx.textAlign = 'right';
            ctx.textBaseline = 'middle';

            for (let i = 0; i <= ticks; i++) {
                const tickVal = Math.round((maxVal / ticks) * i);
                const y = p.top + plotH - (i / ticks) * plotH;
                ctx.strokeStyle = '#1e293b';
                ctx.lineWidth = 1;
                ctx.beginPath();
                ctx.moveTo(p.left, y);
                ctx.lineTo(p.left + plotW, y);
                ctx.stroke();
                ctx.fillText(tickVal.toString(), p.left - 6, y);
            }

            // Bars
            const slotWidth = plotW / labels.length;
            const barWidth = Math.min(36, slotWidth * 0.6);

            labels.forEach((label, i) => {
                const val = data[i] || 0;
                const barH = (val / maxVal) * plotH;
                const x = p.left + i * slotWidth + (slotWidth - barWidth) / 2;
                const y = p.top + plotH - barH;

                ctx.fillStyle = this.options.color;
                ctx.beginPath();
                ctx.roundRect(x, y, barWidth, barH, [4, 4, 0, 0]);
                ctx.fill();

                // Bar value on top
                ctx.fillStyle = '#f8fafc';
                ctx.font = 'bold 10px monospace';
                ctx.textAlign = 'center';
                ctx.fillText(val.toString(), x + barWidth / 2, y - 6);

                // Label below
                ctx.fillStyle = '#94a3b8';
                ctx.font = '10px sans-serif';
                ctx.fillText(label, x + barWidth / 2, p.top + plotH + 8);
            });
        }
    }

    return {
        LineChart,
        DonutChart,
        BarChart
    };
})();
