export default function LoadingSkeleton() {
  return (
    <div className="skeleton-dashboard">
      <div className="skeleton-row large" />
      <div className="skeleton-grid">
        <div className="skeleton-card" />
        <div className="skeleton-card" />
        <div className="skeleton-card" />
        <div className="skeleton-card" />
      </div>
      <div className="skeleton-grid">
        <div className="skeleton-panel" />
        <div className="skeleton-panel" />
      </div>
    </div>
  );
}
