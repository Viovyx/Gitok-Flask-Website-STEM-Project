const style = getComputedStyle(document.body);
const colorPrimary = style.getPropertyValue("--primary");
const colorSuccess = style.getPropertyValue("--success");
const colorError = style.getPropertyValue("--error");
const colorCopyLight = style.getPropertyValue("--copy-light");

// Scanner chart
const scanner = document.getElementById("scanner-chart");
const days = ["24/10", "25/10", "26/10", "27/10", "28/10", "Yesterday", "Today"];
const totalScans = [12, 19, 3, 5, 2, 3, 9];
const successfulScans = [10, 16, 2, 3, 1, 1, 6];
const failedScans = [2, 3, 1, 2, 1, 2, 3];

new Chart(scanner, {
    type: "line",
    data: {
        labels: days,
        datasets: [
            {
                label: "# Total Scans",
                data: totalScans,
                showLine: true,
                fill: false,
                borderColor: colorPrimary,
                tension: 0.1,
                pointRadius: 5,
                pointHoverRadius: 10,
            },
            {
                label: "# Successful Scans",
                data: successfulScans,
                showLine: true,
                fill: false,
                borderColor: colorSuccess,
                tension: 0.1,
                pointRadius: 5,
                pointHoverRadius: 10,
            },
            {
                label: "# Failed Scans",
                data: failedScans,
                showLine: true,
                fill: false,
                borderColor: colorError,
                tension: 0.1,
                pointRadius: 5,
                pointHoverRadius: 10,
            },
        ],
    },
    options: {
        scales: {
            x: {
                grid: {
                    color: colorCopyLight,
                },
                ticks: {
                    color: colorCopyLight,
                },
            },
            y: {
                beginAtZero: true,
                grid: {
                    color: colorCopyLight,
                },
                ticks: {
                    color: colorCopyLight,
                },
            },
        },
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
            legend: {
                labels: {
                    color: colorCopyLight,
                    position: "bottom",
                },
            },
        },
    },
});
