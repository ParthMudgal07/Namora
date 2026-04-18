import Chip from "./Chip";

export function DonutChart({ counts }) {
  const segments = [
    { label: "Compliant", value: counts.compliant ?? 0, className: "segment-low" },
    { label: "Partial", value: counts.partial ?? 0, className: "segment-medium" },
    { label: "Non-Compliant", value: counts.non_compliant ?? 0, className: "segment-high" },
    { label: "Insufficient", value: counts.insufficient_data ?? 0, className: "segment-neutral" }
  ];

  const total = segments.reduce((sum, item) => sum + item.value, 0) || 1;
  const radius = 52;
  const circumference = 2 * Math.PI * radius;
  let runningOffset = 0;

  return (
    <div className="chart-card">
      <div className="chart-head">
        <div>
          <p className="section-eyebrow">Chart</p>
          <h3>Compliance Breakdown</h3>
        </div>
        <Chip tone="knowledge">{total} checks</Chip>
      </div>

      <div className="donut-layout">
        <svg viewBox="0 0 140 140" className="donut-svg">
          <circle cx="70" cy="70" r={radius} className="donut-track" />
          {segments.map((segment) => {
            const ratio = segment.value / total;
            const dash = ratio * circumference;
            const circle = (
              <circle
                key={segment.label}
                cx="70"
                cy="70"
                r={radius}
                className={`donut-segment ${segment.className}`}
                strokeDasharray={`${dash} ${circumference - dash}`}
                strokeDashoffset={-runningOffset}
              />
            );
            runningOffset += dash;
            return circle;
          })}
        </svg>

        <div className="donut-center">
          <strong>{counts.non_compliant ?? 0}</strong>
          <span>high-risk findings</span>
        </div>
      </div>

      <div className="legend-list">
        {segments.map((segment) => (
          <div className="legend-row" key={segment.label}>
            <span className={`legend-swatch ${segment.className}`} />
            <span>{segment.label}</span>
            <strong>{segment.value}</strong>
          </div>
        ))}
      </div>
    </div>
  );
}

export function BarChart({ riskByBody }) {
  const rows = Object.entries(riskByBody ?? {});
  const maxValue = Math.max(...rows.map(([, item]) => item.average_score), 100);

  return (
    <div className="chart-card">
      <div className="chart-head">
        <div>
          <p className="section-eyebrow">Chart</p>
          <h3>Risk Distribution</h3>
        </div>
        <Chip tone="structured">Regulator view</Chip>
      </div>

      <div className="bar-chart">
        {rows.map(([body, details]) => (
          <div className="bar-row" key={body}>
            <div className="bar-labels">
              <span>{body}</span>
              <small>{details.average_score}</small>
            </div>
            <div className="bar-track">
              <div
                className={`bar-fill bar-${details.risk_band.toLowerCase()}`}
                style={{ width: `${(details.average_score / maxValue) * 100}%` }}
              />
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
