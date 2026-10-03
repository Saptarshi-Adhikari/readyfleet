window.renderForecastChart = function() {
    const canvas = document.getElementById('canvas-forecast');
    if (!canvas) return;

    const ctx = canvas.getContext('2d');
    canvas.width = canvas.parentElement.clientWidth - 40;
    canvas.height = 240;

    ctx.clearRect(0, 0, canvas.width, canvas.height);

    fetch('/api/fleet/forecast')
        .then(res => res.json())
        .then(data => {
            const forecast = data.mc_forecast || [0.8, 0.78, 0.75, 0.72, 0.7, 0.68, 0.65];
            
            // Draw axis
            ctx.strokeStyle = '#475569';
            ctx.lineWidth = 1;
            ctx.beginPath();
            ctx.moveTo(40, 20);
            ctx.lineTo(40, 200);
            ctx.lineTo(canvas.width - 20, 200);
            ctx.stroke();

            // Draw line
            ctx.strokeStyle = '#38bdf8';
            ctx.lineWidth = 3;
            ctx.beginPath();

            const stepX = (canvas.width - 80) / 6;
            forecast.forEach((rate, i) => {
                const x = 40 + i * stepX;
                const y = 200 - (rate * 160);
                if (i === 0) ctx.moveTo(x, y);
                else ctx.lineTo(x, y);

                // Draw point
                ctx.fillStyle = '#38bdf8';
                ctx.fillRect(x - 3, y - 3, 6, 6);
                
                // Label
                ctx.fillStyle = '#94a3b8';
                ctx.font = '10px sans-serif';
                ctx.fillText(`T+${i}d`, x - 8, 215);
            });
            ctx.stroke();
        });
};
