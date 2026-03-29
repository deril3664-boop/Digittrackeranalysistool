<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8" />
<meta name="viewport" content="width=device-width, initial-scale=1.0"/>
<title>DigitFlow Analysis</title>

<style>
body {
  margin: 0;
  font-family: Arial;
  background: black;
  color: #00eaff;
  text-align: center;
}

/* Matrix canvas */
canvas {
  position: fixed;
  top: 0;
  left: 0;
  z-index: 0;
}

/* UI */
.container {
  position: relative;
  z-index: 2;
  padding: 20px;
}

button {
  padding: 10px 20px;
  background: orange;
  border: none;
  border-radius: 6px;
  margin: 10px;
  font-weight: bold;
}

select {
  padding: 10px;
  margin: 10px;
  background: black;
  color: orange;
  border: 1px solid orange;
}

.price {
  font-size: 30px;
  color: orange;
}

/* Modal */
.modal {
  position: fixed;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  background: black;
  display: none;
  justify-content: center;
  align-items: center;
  flex-direction: column;
  z-index: 5;
}

.circle {
  width: 100px;
  height: 100px;
  border: 4px solid orange;
  border-radius: 50%;
  display: flex;
  justify-content: center;
  align-items: center;
}

.freq {
  display: flex;
  justify-content: center;
  margin-top: 20px;
}

.bar {
  width: 10px;
  margin: 2px;
  background: orange;
}
</style>
</head>

<body>

<canvas id="matrix"></canvas>

<div class="container">
  <h2>Matches / Differs</h2>

  <select id="symbol">
    <option value="R_10">Vol 10</option>
    <option value="R_25">Vol 25</option>
    <option value="R_50">Vol 50</option>
    <option value="R_75">Vol 75</option>
    <option value="R_100">Vol 100</option>
    <option value="1HZ10V">1s Vol 10</option>
    <option value="1HZ25V">1s Vol 25</option>
    <option value="1HZ50V">1s Vol 50</option>
    <option value="1HZ75V">1s Vol 75</option>
    <option value="1HZ100V">1s Vol 100</option>
  </select>

  <br>

  <button onclick="connect()">CONNECT</button>
  <button onclick="toggle()">START ANALYSIS</button>

  <div class="price" id="price">----</div>

  <div class="freq" id="chart"></div>
</div>

<div class="modal" id="modal">
  <div id="loader">Loading...</div>

  <div id="content" style="display:none;">
    <div class="circle" id="score">0</div>

    <div style="display:flex; gap:30px; margin-top:20px;">
      <div>
        <div class="circle" id="match">0%</div>
        MATCH
      </div>
      <div>
        <div class="circle" id="diff">0%</div>
        DIFFERS
      </div>
    </div>

    <h3 id="prediction"></h3>
  </div>
</div>

<script>
let ws;
let ticks = [];
let analyzing = false;

// 🔌 Connect
function connect() {
  ws = new WebSocket("wss://ws.derivws.com/websockets/v3?app_id=1089");
}

// ▶️ Start/Stop
function toggle() {
  if (!ws) return alert("Connect first");

  analyzing = !analyzing;

  if (analyzing) {
    document.getElementById("modal").style.display = "flex";

    ws.send(JSON.stringify({
      ticks_history: symbol.value,
      count: 45,
      end: "latest"
    }));
  } else {
    location.reload();
  }
}

// 📡 WebSocket
wsHandler = (data) => {
  if (data.history) {
    ticks = data.history.prices.map(p => lastDigit(p));
    update();
    subscribe();
  }

  if (data.tick) {
    let price = data.tick.quote;
    document.getElementById("price").innerText = price;

    ticks.push(lastDigit(price));
    ticks = ticks.slice(-45);

    update();
  }
};

function subscribe() {
  ws.send(JSON.stringify({
    ticks: symbol.value,
    subscribe: 1
  }));
}

function lastDigit(p) {
  return parseInt(p.toString().slice(-1));
}

// 📊 Logic
function update() {
  let freq = Array(10).fill(0);
  ticks.forEach(d => freq[d]++);

  let matches = 0;
  for (let i = 1; i < ticks.length; i++) {
    if (ticks[i] === ticks[i - 1]) matches++;
  }

  let matchP = (matches / ticks.length) * 100;
  let diffP = 100 - matchP;

  document.getElementById("match").innerText = matchP.toFixed(1) + "%";
  document.getElementById("diff").innerText = diffP.toFixed(1) + "%";

  let overdue = freq.filter(f => f === 0).length;
  let score = Math.min(100, (overdue * 10) + matches * 2);

  document.getElementById("score").innerText = score;

  let pred = "NEUTRAL";
  if (matches > 5) pred = "MATCH 🔥";
  else if (overdue > 3) pred = "DIFFERS ⚡";

  document.getElementById("prediction").innerText = pred;

  drawChart(freq);

  document.getElementById("loader").style.display = "none";
  document.getElementById("content").style.display = "block";
}

// 📊 Chart
function drawChart(freq) {
  let chart = document.getElementById("chart");
  chart.innerHTML = "";

  freq.forEach(f => {
    let bar = document.createElement("div");
    bar.className = "bar";
    bar.style.height = (f * 5) + "px";
    chart.appendChild(bar);
  });
}

// 🎨 Matrix
const canvas = document.getElementById("matrix");
const ctx = canvas.getContext("2d");

canvas.width = window.innerWidth;
canvas.height = window.innerHeight;

let letters = "0123456789";
let fontSize = 14;
let columns = canvas.width / fontSize;
let drops = Array(Math.floor(columns)).fill(1);

function draw() {
  ctx.fillStyle = "rgba(0,0,0,0.05)";
  ctx.fillRect(0,0,canvas.width,canvas.height);

  ctx.fillStyle = "#00eaff";
  ctx.font = fontSize + "px monospace";

  for (let i = 0; i < drops.length; i++) {
    let text = letters[Math.floor(Math.random()*letters.length)];
    ctx.fillText(text, i*fontSize, drops[i]*fontSize);

    if (drops[i]*fontSize > canvas.height) drops[i] = 0;
    drops[i]++;
  }
}

setInterval(draw, 80);

// attach ws listener AFTER connect
setInterval(() => {
  if (ws) ws.onmessage = (msg) => wsHandler(JSON.parse(msg.data));
}, 500);
</script>

</body>
</html>
