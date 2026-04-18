import { useEffect, useState } from "react";

export default function StatCard({ label, value, tone = "neutral", suffix = "" }) {
  const [displayValue, setDisplayValue] = useState(0);

  useEffect(() => {
    const target = Number(value) || 0;
    let frame;
    let start;
    const duration = 700;

    const tick = (timestamp) => {
      if (!start) start = timestamp;
      const progress = Math.min((timestamp - start) / duration, 1);
      const eased = 1 - Math.pow(1 - progress, 3);
      setDisplayValue(target * eased);
      if (progress < 1) {
        frame = window.requestAnimationFrame(tick);
      }
    };

    frame = window.requestAnimationFrame(tick);
    return () => window.cancelAnimationFrame(frame);
  }, [value]);

  const formatted = Number.isInteger(Number(value))
    ? Math.round(displayValue)
    : displayValue.toFixed(1);

  return (
    <div className={`stat-card stat-${tone}`}>
      <span>{label}</span>
      <strong>
        {formatted}
        {suffix}
      </strong>
    </div>
  );
}
