window.renderFleetBoard = function() {
    const canvas = document.getElementById('canvas-fleet');
    if (!canvas) return;
    
    const ctx = canvas.getContext('2d');
    canvas.width = canvas.parentElement.clientWidth - 32;
    canvas.height = 320;

    ctx.clearRect(0, 0, canvas.width, canvas.height);

    const tailStates = window.tailStates || {};
    const tails = Object.keys(tailStates);

    const cols = 8;
    const cardWidth = (canvas.width - (cols + 1) * 12) / cols;
    const cardHeight = 50;

    tails.forEach((tail, idx) => {
        const row = Math.floor(idx / cols);
        const col = idx % cols;
        const x = 12 + col * (cardWidth + 12);
        const y = 12 + row * (cardHeight + 12);

        const status = tailStates[tail];
        let color = '#4ade80';
        if (status === 'PMC') color = '#facc15';
        if (status === 'NMC') color = '#f87171';

        // Background
        ctx.fillStyle = '#0f172a';
        ctx.fillRect(x, y, cardWidth, cardHeight);

        // Border
        ctx.strokeStyle = color;
        ctx.lineWidth = 2;
        ctx.strokeRect(x, y, cardWidth, cardHeight);

        // Text
        ctx.fillStyle = '#f8fafc';
        ctx.font = 'bold 12px sans-serif';
        ctx.fillText(tail, x + 10, y + 22);

        ctx.fillStyle = color;
        ctx.font = '11px sans-serif';
        ctx.fillText(status, x + 10, y + 40);
    });
};
