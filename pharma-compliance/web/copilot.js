export function detectBody(question) {
  const upper = question.toUpperCase();
  const bodies = ["CDSCO", "GMP", "NPPA", "SLA"];
  return bodies.find((body) => upper.includes(body)) ?? null;
}

function formatBullets(lines) {
  return lines.map((line) => `- ${line}`).join("\n");
}

function answerSummary(riskReport) {
  const counts = riskReport.status_counts;
  const bodyLines = Object.entries(riskReport.risk_by_regulatory_body).map(
    ([body, details]) =>
      `${body}: score ${details.average_score} (${details.risk_band}), compliant ${details.status_counts.compliant}, partial ${details.status_counts.partial}, non-compliant ${details.status_counts.non_compliant}`
  );

  return {
    content: [
      `Overall risk score is ${riskReport.overall_risk_score} (${riskReport.overall_risk_band}).`,
      `Status counts: compliant ${counts.compliant}, partial ${counts.partial}, non-compliant ${counts.non_compliant}, insufficient data ${counts.insufficient_data}.`,
      "By regulatory body:",
      formatBullets(bodyLines)
    ].join("\n"),
    answerSource: "Structured compliance outputs",
    answerTone: "structured"
  };
}

function answerFixFirst(recommendationsData) {
  const recommendations = recommendationsData.recommendations ?? [];
  if (!recommendations.length) {
    return {
      content: "Recommendations are not available yet.",
      answerSource: "Structured compliance outputs",
      answerTone: "structured"
    };
  }

  const lines = recommendations.slice(0, 5).map(
    (item) =>
      `${item.priority} - ${item.requirement_id} (${item.regulatory_body}): ${item.recommended_action} [reason: ${item.reason}]`
  );

  return {
    content: `Fix these first:\n${formatBullets(lines)}`,
    answerSource: "Structured compliance outputs",
    answerTone: "structured"
  };
}

function answerTopRisks(riskReport) {
  const items = riskReport.top_risk_drivers ?? [];
  if (!items.length) {
    return {
      content: "Top risk drivers are not available yet.",
      answerSource: "Structured compliance outputs",
      answerTone: "structured"
    };
  }

  const lines = items.slice(0, 5).map(
    (item) =>
      `${item.requirement_id} (${item.regulatory_body}, ${item.domain}): ${item.risk_band} risk ${item.risk_score} because ${item.evaluation_reason}`
  );

  return {
    content: `Top risk drivers:\n${formatBullets(lines)}`,
    answerSource: "Structured compliance outputs",
    answerTone: "structured"
  };
}

function answerBodyQuestion(body, assessmentData, riskReport, recommendationsData) {
  const assessments = (assessmentData.assessments ?? []).filter(
    (item) => item.regulatory_body === body
  );
  if (!assessments.length) {
    return {
      content: `No assessment data found for ${body}.`,
      answerSource: "Structured compliance outputs",
      answerTone: "structured"
    };
  }

  const riskInfo = riskReport.risk_by_regulatory_body?.[body];
  const recommendations = (recommendationsData.recommendations ?? []).filter(
    (item) => item.regulatory_body === body
  );

  const lines = [];
  if (riskInfo) {
    lines.push(
      `${body} score is ${riskInfo.average_score} (${riskInfo.risk_band}). Status counts: compliant ${riskInfo.status_counts.compliant}, partial ${riskInfo.status_counts.partial}, non-compliant ${riskInfo.status_counts.non_compliant}.`
    );
  }

  const failing = assessments.filter((item) => item.status !== "compliant");
  if (failing.length) {
    lines.push("Main issues:");
    failing.slice(0, 5).forEach((item) => {
      lines.push(`${item.requirement_id}: ${item.status} because ${item.evaluation_reason}`);
    });
  }

  if (recommendations.length) {
    lines.push("Recommended next actions:");
    recommendations.slice(0, 3).forEach((item) => {
      lines.push(
        `${item.priority}: ${item.recommended_action} (owner: ${item.owner}, timeline: ${item.timeline})`
      );
    });
  }

  return {
    content: lines.join("\n"),
    answerSource: "Structured compliance outputs",
    answerTone: "structured"
  };
}

function answerRag(question, ragAnswerData) {
  if (!ragAnswerData?.answer) {
    return {
      content: "I do not have a stored RAG answer yet. Run a RAG question through the Python pipeline first.",
      answerSource: "Knowledge base unavailable",
      answerTone: "warning"
    };
  }

  const isLlm = ragAnswerData.answer_mode === "openrouter";
  const sourceLabel = isLlm ? "LLM + retrieved context" : "Local knowledge base only";
  const sourceTone = isLlm ? "llm" : "knowledge";
  const statusLine = ragAnswerData.llm_error
    ? `LLM unavailable: ${ragAnswerData.llm_error}`
    : null;

  return {
    content: [
      ragAnswerData.answer,
      statusLine,
      "",
      "Sources:",
      ...(ragAnswerData.sources ?? []).map(
        (source) =>
          `- ${source.source_name} | type=${source.source_type} | page=${source.page} | score=${source.score}`
      )
    ]
      .filter(Boolean)
      .join("\n"),
    answerSource: sourceLabel,
    answerTone: sourceTone
  };
}

export function answerQuestion(question, assessmentData, riskReport, recommendationsData, ragAnswerData) {
  const normalized = question.trim().toLowerCase();

  if (!normalized) {
    return {
      content: [
        "Ask something like:",
        "- What are our top 5 compliance risks?",
        "- What should we fix first?",
        "- Give me a compliance summary.",
        "- Show NPPA issues.",
        "- What does NPPA require for ceiling price compliance?"
      ].join("\n"),
      answerSource: "System guidance",
      answerTone: "structured"
    };
  }

  if (normalized.includes("summary") || normalized.includes("overall")) {
    return answerSummary(riskReport);
  }

  if (normalized.includes("fix first") || normalized.includes("what should we fix") || normalized.includes("recommend")) {
    return answerFixFirst(recommendationsData);
  }

  if (normalized.includes("top") && normalized.includes("risk")) {
    return answerTopRisks(riskReport);
  }

  const body = detectBody(question);
  if (body) {
    return answerBodyQuestion(body, assessmentData, riskReport, recommendationsData);
  }

  return answerRag(question, ragAnswerData);
}
