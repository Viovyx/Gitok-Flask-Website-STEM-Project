// TODO: Add database functionality!!

const style = getComputedStyle(document.body);
const colorPrimary = style.getPropertyValue("--primary");
const colorSuccess = style.getPropertyValue("--success");
const colorError = style.getPropertyValue("--error");
const colorCopyLight = style.getPropertyValue("--copy-light");

// Scanner chart
const scanner = document.getElementById("scanner-chart");
var days = [];
var totalScans = [];
var successfulScans = [];
var failedScans = [];

const myChart = new Chart(scanner, {
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

function setData(data) {
  data.forEach(item => {
    // Add data to arrays
    myChart.update();
  });
}

function addData(label, data) {
  if (days.slice(-1)[0] == label){
    totalScans[totalScans.length - 1] += 1;
    if (data == "0"){
      failedScans[failedScans.length - 1] += 1;
    }
    else {
      successfulScans[successfulScans.length - 1] += 1;
    }
  }
  else{
    days.push(label);
    totalScans.push(1);
    if (data == "0"){
      successfulScans.push(0)
      failedScans.push(1)
    }
    else {
      successfulScans.push(1)
      failedScans.push(0)
    }
  }

  console.log(totalScans.slice(-1)[0])
  myChart.update();
}

function removeFirstData() {
  myChart.data.labels.splice(0, 1);
  myChart.data.datasets.forEach((dataset) => {
    dataset.data.shift();
  });
}

const MAX_DATA_COUNT = 7;

//connect to the socket server.
const socket = io.connect();

socket.on("connect", () => {
  console.log("Connected to SocketIO server");
});

socket.on("disconnect", () => {
  console.log("Disconnected from server");
});

//receive details from server
socket.on("updateSensorGraph", function (msg) {
  // Show only MAX_DATA_COUNT data
  if (myChart.data.labels.length > MAX_DATA_COUNT) {
    removeFirstData();
  }
  addData(msg.date, msg.value);
});
