import Chip from "./Chip";

const NAV_ITEMS = [
  { id: "dashboard", label: "Dashboard", hint: "Live compliance view" },
  { id: "simulator", label: "Simulator", hint: "What-if planning" },
  { id: "reports", label: "Reports", hint: "Export-ready summaries" }
];

export default function Sidebar({
  activeView,
  onSelectView,
  selectedGuidelines,
  companyName,
  mobileOpen,
  onToggleMobile
}) {
  return (
    <>
      <aside className={`sidebar ${mobileOpen ? "open" : ""}`}>
        <div className="sidebar-brand">
          <div className="brand-mark">N</div>
          <div>
            <strong>Nomora</strong>
            <span>Compliance Intelligence</span>
          </div>
        </div>

        <div className="sidebar-company">
          <p className="sidebar-label">Company</p>
          <strong>{companyName || "Setup pending"}</strong>
          <div className="chip-row">
            {selectedGuidelines.map((item) => (
              <Chip key={item} tone="knowledge">
                {item}
              </Chip>
            ))}
          </div>
        </div>

        <nav className="sidebar-nav">
          {NAV_ITEMS.map((item) => (
            <button
              key={item.id}
              type="button"
              className={`sidebar-link ${activeView === item.id ? "active" : ""}`}
              onClick={() => {
                onSelectView(item.id);
                onToggleMobile(false);
              }}
            >
              <span>{item.label}</span>
              <small>{item.hint}</small>
            </button>
          ))}
        </nav>

        <div className="sidebar-foot">
          <p>Prototype mode</p>
          <span>Guided intake + scoped dashboard</span>
        </div>
      </aside>

      {mobileOpen ? <button className="sidebar-overlay" type="button" onClick={() => onToggleMobile(false)} /> : null}
    </>
  );
}
