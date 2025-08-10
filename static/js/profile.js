// static/js/profile.js
document.addEventListener('DOMContentLoaded', () => {
    const chartElement = document.getElementById('statusChart');
    if (!chartElement) return; // Grafik elementi yoksa devam etme

    // `chartElement`'in data-* özelliklerinden verileri al
    const labels = JSON.parse(chartElement.dataset.labels);
    const data = JSON.parse(chartElement.dataset.data);
    const seriesLabel = chartElement.dataset.serieslabel;

    const ctx = chartElement.getContext('2d');

    // Temaya göre renkleri belirle
    const isDarkMode = document.body.dataset.theme === 'dark';
    const textColor = isDarkMode ? '#f8fafc' : '#1e293b';

    new Chart(ctx, {
        type: 'pie',
        data: {
            labels: labels,
            datasets: [{
                label: seriesLabel,
                data: data,
                backgroundColor: [
                    'rgba(59, 130, 246, 0.7)',  // Mavi
                    'rgba(16, 185, 129, 0.7)',  // Yeşil
                    'rgba(239, 68, 68, 0.7)',    // Kırmızı
                    'rgba(249, 115, 22, 0.7)',   // Turuncu
                    'rgba(148, 163, 184, 0.7)'  // Gri
                ],
                borderColor: [
                    'rgba(59, 130, 246, 1)',
                    'rgba(16, 185, 129, 1)',
                    'rgba(239, 68, 68, 1)',
                    'rgba(249, 115, 22, 1)',
                    'rgba(148, 163, 184, 1)'
                ],
                borderWidth: 1
            }]
        },
        options: {
            responsive: true,
            plugins: {
                legend: {
                    position: 'top',
                    labels: {
                        color: textColor
                    }
                },
                title: {
                    display: false
                }
            }
        }
    });
});