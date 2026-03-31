import { useState, useMemo } from "react";
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from "recharts";

// Sinc function: sin(pi*x) / (pi*x), with sinc(0) = 1
function sinc(x) {
  if (Math.abs(x) < 1e-10) return 1;
  const px = Math.PI * x;
  return Math.sin(px) / px;
}

// Raised Cosine impulse response g_RC(t/T)
function rcPulse(tOverT, beta) {
  // Handle t/T = 0
  if (Math.abs(tOverT) < 1e-10) {
    return 1;
  }
  // Handle |t/T| = 1/(2*beta) — indeterminate form, use L'Hopital limit
  if (beta > 0 && Math.abs(Math.abs(tOverT) - 1 / (2 * beta)) < 1e-10) {
    return (Math.PI / 4) * sinc(1 / (2 * beta));
  }
  const denom = 1 - 4 * beta * beta * tOverT * tOverT;
  if (Math.abs(denom) < 1e-15) return 0;
  return sinc(tOverT) * Math.cos(Math.PI * beta * tOverT) / denom;
}

// Root Raised Cosine impulse response g_RRC(t/T)
function rrcPulse(tOverT, beta) {
  // Handle t/T = 0
  if (Math.abs(tOverT) < 1e-10) {
    return 1 - beta + 4 * beta / Math.PI;
  }
  // Handle |t/T| = 1/(4*beta) — indeterminate form
  if (beta > 0 && Math.abs(Math.abs(tOverT) - 1 / (4 * beta)) < 1e-10) {
    return (beta / Math.sqrt(2)) * (
      (1 + 2 / Math.PI) * Math.sin(Math.PI / (4 * beta)) +
      (1 - 2 / Math.PI) * Math.cos(Math.PI / (4 * beta))
    );
  }
  const num =
    Math.sin(Math.PI * tOverT * (1 - beta)) +
    4 * beta * tOverT * Math.cos(Math.PI * tOverT * (1 + beta));
  const denom = Math.PI * tOverT * (1 - 16 * beta * beta * tOverT * tOverT);
  if (Math.abs(denom) < 1e-15) return 0;
  return num / denom;
}

// Compute FFT magnitude (simple DFT for small arrays)
function fftMagnitude(signal) {
  const N = signal.length;
  const mag = new Array(N);
  for (let k = 0; k < N; k++) {
    let re = 0, im = 0;
    for (let n = 0; n < N; n++) {
      const angle = (-2 * Math.PI * k * n) / N;
      re += signal[n] * Math.cos(angle);
      im += signal[n] * Math.sin(angle);
    }
    mag[k] = Math.sqrt(re * re + im * im);
  }
  // fftshift
  const shifted = new Array(N);
  const half = Math.floor(N / 2);
  for (let i = 0; i < N; i++) {
    shifted[i] = mag[(i + half) % N];
  }
  return shifted;
}

function SliderControl({ label, value, min, max, step, onChange, unit = "" }) {
  return (
    <div className="flex flex-col gap-1">
      <div className="flex justify-between items-center">
        <label className="text-sm font-medium text-gray-700">{label}</label>
        <span className="text-sm font-mono bg-blue-100 text-blue-800 px-2 py-0.5 rounded">
          {value}{unit}
        </span>
      </div>
      <input
        type="range"
        min={min}
        max={max}
        step={step}
        value={value}
        onChange={(e) => onChange(parseFloat(e.target.value))}
        className="w-full h-2 bg-gray-200 rounded-lg appearance-none cursor-pointer accent-blue-600"
      />
      <div className="flex justify-between text-xs text-gray-400">
        <span>{min}{unit}</span>
        <span>{max}{unit}</span>
      </div>
    </div>
  );
}

export default function App() {
  const [rolloff, setRolloff] = useState(0.25);
  const [span, setSpan] = useState(8);
  const [sps, setSps] = useState(8);
  const [filterType, setFilterType] = useState("both");

  const { irData, spectrumData } = useMemo(() => {
    const numSamples = span * sps + 1;
    const halfSpan = span / 2;

    // Time vector: t/T from -span/2 to +span/2
    const tOverT = [];
    for (let i = 0; i < numSamples; i++) {
      tOverT.push(-halfSpan + i / sps);
    }

    // Compute impulse responses
    const rcIR = tOverT.map((t) => rcPulse(t, rolloff));
    const rrcIR = tOverT.map((t) => rrcPulse(t, rolloff));

    // Normalize energy
    const rcEnergy = Math.sqrt(rcIR.reduce((s, v) => s + v * v, 0));
    const rrcEnergy = Math.sqrt(rrcIR.reduce((s, v) => s + v * v, 0));
    const rcNorm = rcIR.map((v) => v / rcEnergy);
    const rrcNorm = rrcIR.map((v) => v / rrcEnergy);

    // Build IR data for chart
    const irData = tOverT.map((t, i) => ({
      t: parseFloat(t.toFixed(4)),
      RC: parseFloat(rcNorm[i].toFixed(6)),
      RRC: parseFloat(rrcNorm[i].toFixed(6)),
    }));

    // Compute spectrum (zero-pad for better resolution)
    const padLen = 512;
    const rcPadded = new Array(padLen).fill(0);
    const rrcPadded = new Array(padLen).fill(0);
    const offset = Math.floor((padLen - numSamples) / 2);
    for (let i = 0; i < numSamples; i++) {
      rcPadded[offset + i] = rcNorm[i];
      rrcPadded[offset + i] = rrcNorm[i];
    }

    const rcSpectrum = fftMagnitude(rcPadded);
    const rrcSpectrum = fftMagnitude(rrcPadded);

    // Normalize spectra
    const rcMax = Math.max(...rcSpectrum);
    const rrcMax = Math.max(...rrcSpectrum);

    // Frequency axis: normalized to 1/T (symbol rate)
    const spectrumData = [];
    for (let i = 0; i < padLen; i++) {
      const fNorm = (i - padLen / 2) / padLen * sps; // frequency normalized to 1/T
      if (fNorm >= -2 && fNorm <= 2) {
        spectrumData.push({
          f: parseFloat(fNorm.toFixed(4)),
          RC: parseFloat((rcSpectrum[i] / rcMax).toFixed(6)),
          RRC: parseFloat((rrcSpectrum[i] / rrcMax).toFixed(6)),
        });
      }
    }

    return { irData, spectrumData };
  }, [rolloff, span, sps]);

  const showRC = filterType === "both" || filterType === "rc";
  const showRRC = filterType === "both" || filterType === "rrc";

  return (
    <div className="min-h-screen bg-gray-50 p-6">
      <div className="max-w-6xl mx-auto">
        <h1 className="text-2xl font-bold text-gray-800 mb-1">
          Simulation RC & RRC — Pulse Shaping
        </h1>
        <p className="text-gray-500 text-sm mb-6">
          Visualisation interactive des filtres Raised Cosine et Root Raised Cosine
        </p>

        {/* Controls */}
        <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-5 mb-6">
          <h2 className="text-sm font-semibold text-gray-600 uppercase tracking-wide mb-4">
            Parametres
          </h2>
          <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
            <SliderControl
              label="Roll-off (beta)"
              value={rolloff}
              min={0}
              max={1}
              step={0.05}
              onChange={setRolloff}
            />
            <SliderControl
              label="Span"
              value={span}
              min={2}
              max={32}
              step={2}
              onChange={setSpan}
              unit=" symb"
            />
            <SliderControl
              label="SPS"
              value={sps}
              min={2}
              max={16}
              step={1}
              onChange={setSps}
              unit=" ech/symb"
            />
            <div className="flex flex-col gap-1">
              <label className="text-sm font-medium text-gray-700">Filtre</label>
              <div className="flex gap-2 mt-1">
                {[
                  { val: "both", label: "Les deux" },
                  { val: "rc", label: "RC" },
                  { val: "rrc", label: "RRC" },
                ].map(({ val, label }) => (
                  <button
                    key={val}
                    onClick={() => setFilterType(val)}
                    className={`px-3 py-1.5 rounded-lg text-sm font-medium transition-colors ${
                      filterType === val
                        ? "bg-blue-600 text-white"
                        : "bg-gray-100 text-gray-600 hover:bg-gray-200"
                    }`}
                  >
                    {label}
                  </button>
                ))}
              </div>
            </div>
          </div>
        </div>

        {/* Charts */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* Impulse Response */}
          <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-5">
            <h2 className="text-sm font-semibold text-gray-600 uppercase tracking-wide mb-3">
              Reponse impulsionnelle
            </h2>
            <p className="text-xs text-gray-400 mb-3">g(t) normalise en energie — axe horizontal : t/T</p>
            <ResponsiveContainer width="100%" height={320}>
              <LineChart data={irData} margin={{ top: 5, right: 20, left: 0, bottom: 5 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
                <XAxis
                  dataKey="t"
                  type="number"
                  domain={[-span / 2, span / 2]}
                  tickFormatter={(v) => v.toFixed(0)}
                  label={{ value: "t / T", position: "insideBottom", offset: -2, fontSize: 12 }}
                />
                <YAxis tickFormatter={(v) => v.toFixed(2)} />
                <Tooltip
                  formatter={(value, name) => [parseFloat(value).toFixed(4), name]}
                  labelFormatter={(v) => `t/T = ${parseFloat(v).toFixed(2)}`}
                />
                <Legend />
                {showRC && (
                  <Line
                    type="monotone"
                    dataKey="RC"
                    stroke="#2563eb"
                    strokeWidth={2}
                    dot={false}
                    name="Raised Cosine"
                  />
                )}
                {showRRC && (
                  <Line
                    type="monotone"
                    dataKey="RRC"
                    stroke="#dc2626"
                    strokeWidth={2}
                    dot={false}
                    name="Root Raised Cosine"
                  />
                )}
              </LineChart>
            </ResponsiveContainer>
            <div className="mt-3 p-3 bg-blue-50 rounded-lg">
              <p className="text-xs text-blue-700">
                <strong>Nombre d'echantillons :</strong> {span * sps + 1} |
                <strong> Zero-crossings RC :</strong> tous les T (sauf t=0) |
                <strong> beta = {rolloff}</strong> — {rolloff === 0 ? "sinc pur, bande minimale" : rolloff < 0.3 ? "bon compromis bande/decroissance" : rolloff < 0.7 ? "decroissance rapide, bande moderee" : "decroissance tres rapide, bande large"}
              </p>
            </div>
          </div>

          {/* Spectrum */}
          <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-5">
            <h2 className="text-sm font-semibold text-gray-600 uppercase tracking-wide mb-3">
              Spectre (module)
            </h2>
            <p className="text-xs text-gray-400 mb-3">|G(f)| normalise — axe horizontal : f x T (frequence normalisee)</p>
            <ResponsiveContainer width="100%" height={320}>
              <LineChart data={spectrumData} margin={{ top: 5, right: 20, left: 0, bottom: 5 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
                <XAxis
                  dataKey="f"
                  type="number"
                  domain={[-2, 2]}
                  tickFormatter={(v) => v.toFixed(1)}
                  label={{ value: "f x T", position: "insideBottom", offset: -2, fontSize: 12 }}
                />
                <YAxis domain={[0, 1.1]} tickFormatter={(v) => v.toFixed(1)} />
                <Tooltip
                  formatter={(value, name) => [parseFloat(value).toFixed(4), name]}
                  labelFormatter={(v) => `f·T = ${parseFloat(v).toFixed(2)}`}
                />
                <Legend />
                {showRC && (
                  <Line
                    type="monotone"
                    dataKey="RC"
                    stroke="#2563eb"
                    strokeWidth={2}
                    dot={false}
                    name="RC |G(f)|"
                  />
                )}
                {showRRC && (
                  <Line
                    type="monotone"
                    dataKey="RRC"
                    stroke="#dc2626"
                    strokeWidth={2}
                    dot={false}
                    name="RRC |G(f)|"
                  />
                )}
              </LineChart>
            </ResponsiveContainer>
            <div className="mt-3 p-3 bg-red-50 rounded-lg">
              <p className="text-xs text-red-700">
                <strong>Bande passante RC :</strong> (1+beta)/(2T) = {((1 + rolloff) / 2).toFixed(2)}/T |
                <strong> Transition :</strong> de {((1 - rolloff) / 2).toFixed(2)}/T a {((1 + rolloff) / 2).toFixed(2)}/T |
                <strong> RRC = racine carree du spectre RC</strong>
              </p>
            </div>
          </div>
        </div>

        {/* Info panel */}
        <div className="mt-6 bg-white rounded-xl shadow-sm border border-gray-200 p-5">
          <h2 className="text-sm font-semibold text-gray-600 uppercase tracking-wide mb-3">
            Resume des parametres
          </h2>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <div className="bg-gray-50 rounded-lg p-3">
              <p className="text-xs text-gray-500">Duree du filtre</p>
              <p className="text-lg font-semibold text-gray-800">{span}T</p>
            </div>
            <div className="bg-gray-50 rounded-lg p-3">
              <p className="text-xs text-gray-500">Echantillons totaux</p>
              <p className="text-lg font-semibold text-gray-800">{span * sps + 1}</p>
            </div>
            <div className="bg-gray-50 rounded-lg p-3">
              <p className="text-xs text-gray-500">Bande occupee</p>
              <p className="text-lg font-semibold text-gray-800">{((1 + rolloff) / 2).toFixed(2)} / T</p>
            </div>
            <div className="bg-gray-50 rounded-lg p-3">
              <p className="text-xs text-gray-500">Exces de bande</p>
              <p className="text-lg font-semibold text-gray-800">{(rolloff * 100).toFixed(0)}%</p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
