document.addEventListener('DOMContentLoaded', () => {
    const navFleet = document.getElementById('nav-fleet');
    const navForecast = document.getElementById('nav-forecast');
    const navCannibal = document.getElementById('nav-cannibal');
    const navAudit = document.getElementById('nav-audit');

    const viewFleet = document.getElementById('view-fleet');
    const viewForecast = document.getElementById('view-forecast');
    const viewCannibal = document.getElementById('view-cannibal');
    const viewAudit = document.getElementById('view-audit');

    const buttons = [navFleet, navForecast, navCannibal, navAudit];
    const views = [viewFleet, viewForecast, viewCannibal, viewAudit];

    function showView(targetBtn, targetView) {
        buttons.forEach(btn => btn.classList.remove('active'));
        views.forEach(view => view.style.display = 'none');

        targetBtn.classList.add('active');
        targetView.style.display = 'block';

        if (targetView === viewFleet && window.renderFleetBoard) {
            window.renderFleetBoard();
        } else if (targetView === viewForecast && window.renderForecastChart) {
            window.renderForecastChart();
        }
    }

    navFleet.addEventListener('click', () => showView(navFleet, viewFleet));
    navForecast.addEventListener('click', () => showView(navForecast, viewForecast));
    navCannibal.addEventListener('click', () => showView(navCannibal, viewCannibal));
    navAudit.addEventListener('click', () => showView(navAudit, viewAudit));

    // Fetch initial fleet status
    fetch('/api/fleet/status')
        .then(res => res.json())
        .then(data => {
            document.getElementById('stat-total').innerText = data.total_tails;
            document.getElementById('stat-mc').innerText = data.mc_count;
            document.getElementById('stat-pmc').innerText = data.pmc_count;
            document.getElementById('stat-nmc').innerText = data.nmc_count;
            window.tailStates = data.tail_states;
            if (window.renderFleetBoard) window.renderFleetBoard();
        })
        .catch(err => console.error(err));
});
