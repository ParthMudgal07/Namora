export function getRiskBand(score) {
  if (score >= 70) return "High";
  if (score >= 35) return "Medium";
  return "Low";
}

export function buildFilteredRiskReport(baseRiskReport, baseAssessmentData, selectedGuidelines) {
  const selectedSet = new Set(selectedGuidelines);
  const filteredScores = (baseRiskReport.requirement_scores ?? []).filter((item) =>
    selectedSet.has(item.regulatory_body)
  );

  if (!filteredScores.length) {
    return {
      overall_risk_score: 0,
      overall_risk_band: "Low",
      total_requirements: 0,
      status_counts: {
        compliant: 0,
        partial: 0,
        non_compliant: 0,
        insufficient_data: 0
      },
      risk_by_regulatory_body: {},
      risk_by_domain: {},
      top_risk_drivers: [],
      requirement_scores: []
    };
  }

  const statusCounts = filteredScores.reduce(
    (accumulator, item) => {
      accumulator[item.status] += 1;
      return accumulator;
    },
    {
      compliant: 0,
      partial: 0,
      non_compliant: 0,
      insufficient_data: 0
    }
  );

  const overallRiskScore =
    filteredScores.reduce((sum, item) => sum + item.risk_score, 0) / filteredScores.length;

  const riskByBody = Object.fromEntries(
    Object.entries(baseRiskReport.risk_by_regulatory_body ?? {}).filter(([body]) =>
      selectedSet.has(body)
    )
  );

  const domainAccumulator = {};
  filteredScores.forEach((item) => {
    if (!domainAccumulator[item.domain]) {
      domainAccumulator[item.domain] = {
        scores: [],
        status_counts: {
          compliant: 0,
          partial: 0,
          non_compliant: 0,
          insufficient_data: 0
        }
      };
    }

    domainAccumulator[item.domain].scores.push(item.risk_score);
    domainAccumulator[item.domain].status_counts[item.status] += 1;
  });

  const riskByDomain = Object.fromEntries(
    Object.entries(domainAccumulator).map(([domain, value]) => {
      const averageScore = value.scores.reduce((sum, score) => sum + score, 0) / value.scores.length;
      return [
        domain,
        {
          average_score: Number(averageScore.toFixed(2)),
          risk_band: getRiskBand(averageScore),
          requirement_count: value.scores.length,
          status_counts: value.status_counts
        }
      ];
    })
  );

  const topRiskDrivers = [...filteredScores]
    .sort((left, right) => right.risk_score - left.risk_score)
    .slice(0, 5)
    .map((item) => {
      const assessment = (baseAssessmentData.assessments ?? []).find(
        (entry) => entry.requirement_id === item.requirement_id
      );
      return {
        ...item,
        evaluation_reason:
          item.evaluation_reason ?? assessment?.evaluation_reason ?? "No explanation available.",
        evaluation_evidence: item.evaluation_evidence ?? assessment?.evaluation_evidence ?? []
      };
    });

  return {
    ...baseRiskReport,
    overall_risk_score: Number(overallRiskScore.toFixed(2)),
    overall_risk_band: getRiskBand(overallRiskScore),
    total_requirements: filteredScores.length,
    status_counts: statusCounts,
    risk_by_regulatory_body: riskByBody,
    risk_by_domain: riskByDomain,
    top_risk_drivers: topRiskDrivers,
    requirement_scores: filteredScores
  };
}

export function createScopedAssessmentData(baseAssessmentData, selectedGuidelines) {
  return {
    ...baseAssessmentData,
    assessments: (baseAssessmentData.assessments ?? []).filter((item) =>
      selectedGuidelines.includes(item.regulatory_body)
    )
  };
}

export function createScopedRecommendations(baseRecommendationsData, selectedGuidelines) {
  const recommendations = (baseRecommendationsData.recommendations ?? []).filter((item) =>
    selectedGuidelines.includes(item.regulatory_body)
  );

  return {
    ...baseRecommendationsData,
    recommendations,
    total_recommendations: recommendations.length
  };
}

export function renderValue(value) {
  if (Array.isArray(value)) {
    return value.join(", ");
  }
  return value ?? "";
}
