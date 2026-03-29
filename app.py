import { useState, useRef, useEffect } from "react";

export default function DerivDashboard() { const [connected, setConnected] = useState(false); const [analyzing, setAnalyzing] = useState(false); const [price, setPrice] = useState("----"); const [ticks, setTicks] = useState([]); const [matchPercent, setMatchPercent] = useState(0); const [diffPercent, setDiffPercent] = useState(0); const [showModal, setShowModal] = useState(false); const [selectedIndex, setSelectedIndex] = useState("1HZ10V"); const [score, setScore] = useState(0); const [prediction, setPrediction] = useState("-");

const ws = useRef(null); const canvasRef = useRef(null);

const indices = [ "R_10","R_25","R_50","R_75","R_100", "1HZ10V","1HZ25V","1HZ50V","1HZ75V","1HZ100V" ];

// 🔥 MATRIX BACKGROUND (LIGHT BLUE LIKE VIDEO) useEffect(() => { const canvas = canvasRef.current; const ctx = canvas.getContext("2d");

canvas.width = window.innerWidth;
canvas.height = window.innerHeight;

const letters = "0123456789";
const fontSize = 16;
const columns = canvas.width / fontSize;
const drops = Array(Math.floor(columns)).fill(1);

function draw() {
  ctx.fillStyle = "rgba(0, 0, 0, 0.08)";
  ctx.fillRect(0, 0, canvas.width, canvas.height);

  ctx.fillStyle = "#00eaff"; // light blue glow
  ctx.shadowColor = "#00eaff";
  ctx.shadowBlur = 8;
  ctx.font = fontSize + "px monospace";

  for (let i = 0; i < drops.length; i++) {
    const text = letters[Math.floor(Math.random() * letters.length)];
    ctx.fillText(text, i * fontSize, drops[i] * fontSize);

    if (drops[i] * fontSize > canvas.height && Math.random() > 0.96) {
      drops[i] = 0;
    }
    drops[i]++;
  }
}

const interval = setInterval(draw, 28);
return () => clearInterval(interval);

}, []);

const connect = () => { ws.current = new WebSocket("wss://ws.derivws.com/websockets/v3?app_id=1089");

ws.current.onopen = () => setConnected(true);
ws.current.onclose = () => {
  setConnected(false);
  setAnalyzing(false);
};

};

// 🧠 IMPROVED SMART ENGINE const processTicks = (tickArray) => { let matches = 0; let freq = Array(10).fill(0);

tickArray.forEach(d => freq[d]++);

for (let i = 1; i < tickArray.length; i++) {
  if (tickArray[i] === tickArray[i - 1]) matches++;
}

const match = (matches / tickArray.length) * 100;
const diff = 100 - match;

setMatchPercent(match.toFixed(1));
setDiffPercent(diff.toFixed(1));

const avg = tickArray.length / 10;
const variance = freq.reduce((acc, f) => acc + Math.pow(f - avg, 2), 0) / 10;

let streak = 1;
for (let i = tickArray.length - 1; i > 0; i--) {
  if (tickArray[i] === tickArray[i - 1]) streak++;
  else break;
}

const overdueDigits = freq.filter(f => f === 0).length;

const finalScore = (variance * 3) + (streak * 8) + (overdueDigits * 5);
setScore(Math.min(100, finalScore.toFixed(0)));

// 🎯 BETTER SIGNAL
if (streak >= 5) {
  setPrediction("STRONG MATCH 🔥");
} else if (streak >= 3) {
  setPrediction("MATCH CONTINUATION");
} else if (overdueDigits >= 4) {
  setPrediction("DIFFERS SPIKE ⚡");
} else if (match > 65) {
  setPrediction("MATCH BIAS");
} else if (diff > 65) {
  setPrediction("DIFFERS BIAS");
} else {
  setPrediction("WAIT / NEUTRAL");
}

};

const startAnalysis = () => { if (!ws.current || ws.current.readyState !== 1) return;

setAnalyzing(true);
setShowModal(true);

// ⚡ INSTANT 45 TICKS BUFFER
ws.current.send(JSON.stringify({
  ticks_history: selectedIndex,
  count: 45,
  end: "latest",
  style: "ticks"
}));

ws.current.onmessage = (msg) => {
  const data = JSON.parse(msg.data);

  if (data.history) {
    const digits = data.history.prices.map(p => parseInt(p.toString().slice(-1)));
    setTicks(digits);
    processTicks(digits);

    ws.current.send(JSON.stringify({
      ticks: selectedIndex,
      subscribe: 1
    }));
  }

  if (data.tick) {
    const p = data.tick.quote;
    setPrice(p);

    const digit = parseInt(p.toString().slice(-1));

    setTicks(prev => {
      const updated = [...prev, digit].slice(-45);
      processTicks(updated);
      return updated;
    });
  }
};

};

const stopAnalysis = () => { setAnalyzing(false); setShowModal(false); ws.current.close(); setTicks([]); };

const freq = Array(10).fill(0); ticks.forEach(d => freq[d]++);

return ( <div className="relative min-h-screen text-green-400 flex flex-col items-center p-4">

<canvas ref={canvasRef} className="fixed inset-0 z-0" />

  <div className="relative z-10 flex flex-col items-center w-full max-w-sm">

    <h1 className="text-lg mb-2 text-orange-400 font-bold">Matches / Differs</h1>

    <select
      className="mb-4 bg-black border border-orange-400 p-2 rounded text-orange-400 w-full"
      value={selectedIndex}
      onChange={(e) => setSelectedIndex(e.target.value)}
    >
      {indices.map(i => <option key={i}>{i}</option>)}
    </select>

    {!connected ? (
      <button onClick={connect} className="bg-orange-500 text-black px-6 py-2 rounded mb-4 w-full">
        CONNECT TO WEBSOCKET
      </button>
    ) : (
      <p className="mb-4 text-green-400">● LIVE</p>
    )}

    <div className="bg-black border border-orange-400 px-6 py-2 rounded mb-4 text-orange-400 w-full text-center">
      Volatility Index: {selectedIndex}
    </div>

    <div className="text-3xl text-orange-400 mb-4 font-bold">{price}</div>

    {connected && (
      <button
        onClick={analyzing ? stopAnalysis : startAnalysis}
        className="bg-orange-500 text-black px-6 py-3 rounded mb-6 w-full font-bold"
      >
        {analyzing ? "STOP ANALYSIS" : "START ANALYSIS"}
      </button>
    )}

    {/* 📊 DIGIT FREQUENCY CHART */}
    <div className="w-full mt-4 bg-black bg-opacity-60 p-3 rounded border border-orange-400">
      <p className="text-xs text-center mb-2">DIGIT FREQUENCY (45 TICKS)</p>
      <div className="flex justify-between items-end h-24">
        {freq.map((f, i) => (
          <div key={i} className="flex flex-col items-center w-full">
            <div
              className="w-3 bg-orange-400 rounded"
              style={{ height: `${f * 5}px` }}
            ></div>
            <span className="text-xs">{i}</span>
          </div>
        ))}
      </div>
    </div>

  </div>

  {showModal && (
    <div className="fixed inset-0 bg-black bg-opacity-95 flex flex-col items-center justify-center z-20">

      {ticks.length === 0 && (
        <div className="w-24 h-24 border-4 border-orange-400 border-t-transparent rounded-full animate-spin mb-6"></div>
      )}

      {ticks.length > 0 && (
        <>
          {/* 🟠 SCORE CIRCLE */}
          <div className="w-32 h-32 rounded-full border-4 border-orange-400 flex items-center justify-center text-3xl mb-6 shadow-lg">
            {score}
          </div>

          {/* MATCH / DIFFER UI */}
          <div className="flex gap-12">
            <div className="flex flex-col items-center">
              <div className="w-24 h-24 rounded-full border-4 border-orange-400 flex items-center justify-center text-xl">
                {matchPercent}%
              </div>
              <p className="mt-2">MATCH</p>
            </div>

            <div className="flex flex-col items-center">
              <div className="w-24 h-24 rounded-full border-4 border-red-500 flex items-center justify-center text-xl">
                {diffPercent}%
              </div>
              <p className="mt-2">DIFFERS</p>
            </div>
          </div>

          {/* 🎯 PREDICTION OUTPUT */}
          <div className="mt-6 text-orange-400 text-xl font-bold text-center">
            {prediction}
          </div>
        </>
      )}

    </div>
  )}

</div>

); }
