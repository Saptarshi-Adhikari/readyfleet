document.addEventListener('DOMContentLoaded', () => {
    const btnExpedite = document.getElementById('btn-expedite');
    const deltaPanel = document.getElementById('whatif-delta');

    if (btnExpedite) {
        btnExpedite.addEventListener('click', () => {
            fetch('/api/whatif', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ lever: { type: 'expedite_spares', part_no: 'PART-ENG-01' } })
            })
            .then(res => res.json())
            .then(data => {
                deltaPanel.innerText = `Lever Applied! Latency: ${data.latency_ms.toFixed(1)} ms | Before: ${(data.before_mc_rate * 100).toFixed(1)}% -> After: ${(data.after_mc_rate * 100).toFixed(1)}%`;
                if (window.renderForecastChart) window.renderForecastChart();
            });
        });
    }

    const btnCannEval = document.getElementById('btn-cann-eval');
    const cannResult = document.getElementById('cann-result');

    if (btnCannEval) {
        btnCannEval.addEventListener('click', () => {
            const donor = document.getElementById('cann-donor').value || 'SYN-04';
            const rec = document.getElementById('cann-rec').value || 'SYN-01';

            fetch('/api/cannibalization/advice', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ donor_tail: donor, recipient_tail: rec, comp_class: 'engine' })
            })
            .then(res => res.json())
            .then(data => {
                cannResult.innerHTML = `<b style="color: ${data.approved ? '#4ade80' : '#f87171'};">${data.message}</b>`;
            });
        });
    }
});
