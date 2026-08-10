// dashboard.js - renders the progress chart on the dashboard page

document.addEventListener('DOMContentLoaded', function () {
    const ctx = document.getElementById('progressChart');
    if (!ctx) return;

    const labels = (typeof activityLabels !== 'undefined' && activityLabels.length)
        ? activityLabels.slice().reverse().map(l => l.charAt(0).toUpperCase() + l.slice(1))
        : ['No Data'];

    const data = (typeof activityData !== 'undefined' && activityData.length)
        ? activityData.slice().reverse()
        : [0];

    new Chart(ctx, {
        type: 'line',
        data: {
            labels: labels,
            datasets: [{
                label: 'Score %',
                data: data,
                borderColor: '#8B5CF6',
                backgroundColor: 'rgba(139, 92, 246, 0.15)',
                tension: 0.4,
                fill: true,
                pointBackgroundColor: '#EC4899',
                pointRadius: 5
            }]
        },
        options: {
            responsive: true,
            plugins: {
                legend: { labels: { color: '#e5e7eb' } }
            },
            scales: {
                x: { ticks: { color: '#94A3B8' }, grid: { color: 'rgba(255,255,255,0.05)' } },
                y: {
                    beginAtZero: true,
                    max: 100,
                    ticks: { color: '#94A3B8' },
                    grid: { color: 'rgba(255,255,255,0.05)' }
                }
            }
        }
    });
});
