import Chip from "./Chip";

export default function RecommendationCard({ item }) {
  const riskTone =
    item.priority === "Critical" || item.priority === "High"
      ? "high"
      : item.priority === "Medium"
        ? "medium"
        : "low";

  return (
    <article className={`recommendation-card recommendation-${riskTone}`}>
      <div className="recommendation-top">
        <div>
          <p className="recommendation-meta">
            {item.requirement_id} · {item.regulatory_body}
          </p>
          <h4>{item.issue_title ?? item.recommended_action}</h4>
        </div>
        <Chip tone={item.priority.toLowerCase()}>{item.priority}</Chip>
      </div>

      <div className="recommendation-grid">
        <div>
          <span>What’s wrong</span>
          <p>{item.reason}</p>
        </div>
        <div>
          <span>Why it matters</span>
          <p>{item.why_it_matters ?? `This affects ${item.regulatory_body} compliance posture and can increase risk exposure.`}</p>
        </div>
        <div>
          <span>Suggested fix</span>
          <p>{item.recommended_action}</p>
        </div>
      </div>
    </article>
  );
}
