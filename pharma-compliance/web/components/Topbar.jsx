import Chip from "./Chip";

export default function Topbar({
  companyName,
  selectedGuidelines,
  activeView,
  onOpenSidebar
}) {
  return (
    <header className="topbar">
      <div className="topbar-left">
        <button type="button" className="hamburger" onClick={onOpenSidebar}>
          <span />
          <span />
          <span />
        </button>
        <div>
          <p className="topbar-eyebrow">Nomora Workspace</p>
          <h2>{activeView}</h2>
        </div>
      </div>

      <div className="topbar-right">
        <div className="topbar-guidelines">
          {selectedGuidelines.map((item) => (
            <Chip key={item} tone="structured">
              {item}
            </Chip>
          ))}
        </div>

        <div className="profile-pill">
          <div className="profile-avatar">{(companyName || "N").slice(0, 1).toUpperCase()}</div>
          <div>
            <strong>{companyName || "Nomora User"}</strong>
            <span>Compliance lead</span>
          </div>
        </div>
      </div>
    </header>
  );
}
