import { useEffect, useMemo, useState } from "react";
import { INTAKE_SECTIONS, REGULATORY_OPTIONS, createEmptyItem } from "./complianceIntakeConfig";
import { analyzeCompany, chatWithCopilot } from "./api";
import Chip from "./components/Chip";
import ChatPanel from "./components/ChatPanel";
import { BarChart, DonutChart } from "./components/Charts";
import LoadingSkeleton from "./components/LoadingSkeleton";
import RecommendationCard from "./components/RecommendationCard";
import Sidebar from "./components/Sidebar";
import StatCard from "./components/StatCard";
import StepIndicator from "./components/StepIndicator";
import Topbar from "./components/Topbar";
import { renderValue } from "./utils";

const APP_FLOW = [
  { id: "landing", label: "Landing", hint: "Intro" },
  { id: "setup", label: "Company Setup", hint: "Scope" },
  { id: "form", label: "Guided Input", hint: "Data collection" },
  { id: "processing", label: "Processing", hint: "Analysis" },
  { id: "workspace", label: "Dashboard", hint: "Insights" }
];

const PROCESSING_STEPS = [
  "Analyzing regulations...",
  "Matching selected guidelines...",
  "Detecting risks...",
  "Preparing recommendations..."
];

function createInitialCompanyData() {
  const base = {
    company_name: "",
    manufacturer_name: "",
    regulatory_scope: []
  };

  INTAKE_SECTIONS.forEach((section) => {
    if (section.collectionKey) {
      base[section.collectionKey] = [createEmptyItem(section)];
    } else {
      section.fields.forEach((field) => {
        base[field.key] = "";
      });
    }
  });

  return base;
}

function PageShell({ children }) {
  return <div className="page-shell">{children}</div>;
}

function Section({ eyebrow, title, subtitle, actions, children, className = "" }) {
  return (
    <section className={`dashboard-panel ${className}`}>
      <div className="panel-head">
        <div>
          <p className="section-eyebrow">{eyebrow}</p>
          <h3>{title}</h3>
          {subtitle ? <p className="section-subtitle">{subtitle}</p> : null}
        </div>
        {actions}
      </div>
      {children}
    </section>
  );
}

function InputField({ field, value, onChange }) {
  const commonProps = {
    value: field.type === "tags" ? renderValue(value) : value ?? "",
    onChange,
    placeholder: field.placeholder ?? ""
  };

  if (field.type === "textarea") {
    return <textarea rows="4" {...commonProps} />;
  }

  return <input type={field.type} {...commonProps} />;
}

function LandingPage({ onStart }) {
  return (
    <PageShell>
      <section className="landing-hero">
        <div className="landing-copy">
          <div className="hero-badge">
            <span className="hero-badge-dot" />
            AI-native compliance cockpit for pharma manufacturing
          </div>
          <h1>Nomora</h1>
          <p className="landing-tagline">
            Nomora is an AI-powered compliance intelligence system that not only detects
            regulatory risks but allows companies to simulate decisions and understand their
            impact in real time.
          </p>
          <div className="landing-actions">
            <button className="primary-button" type="button" onClick={onStart}>
              Start Analysis
            </button>
            <button className="secondary-button" type="button">
              Explore Demo Flow
            </button>
          </div>
        </div>

        <div className="landing-preview">
          <div className="preview-window">
            <div className="preview-top">
              <Chip tone="llm">RAG knowledge base</Chip>
              <Chip tone="knowledge">Simulator-ready</Chip>
            </div>
            <div className="preview-score">
              <span>Compliance Pulse</span>
              <strong>84</strong>
              <small>Low-to-medium risk posture after simulation</small>
            </div>
            <div className="preview-bars">
              <div className="preview-bar high" style={{ width: "78%" }} />
              <div className="preview-bar medium" style={{ width: "52%" }} />
              <div className="preview-bar low" style={{ width: "89%" }} />
            </div>
          </div>
        </div>
      </section>

      <section className="feature-grid">
        {[
          {
            title: "Compliance Detection",
            text: "Map uploaded company evidence against regulator-specific requirements and instantly surface the gaps."
          },
          {
            title: "Risk Analysis",
            text: "Summarize the high, medium, and low risk areas with dashboard cards, charts, and recommendation trails."
          },
          {
            title: "Simulator",
            text: "Test how CAPA closure, pricing correction, or documentation improvements change the compliance posture."
          }
        ].map((feature) => (
          <div className="feature-card" key={feature.title}>
            <p className="section-eyebrow">Feature</p>
            <h3>{feature.title}</h3>
            <p>{feature.text}</p>
          </div>
        ))}
      </section>
    </PageShell>
  );
}

function SetupPage({
  companyName,
  setCompanyName,
  selectedGuidelines,
  onToggleGuideline,
  onContinue
}) {
  const canContinue = companyName.trim().length > 0 && selectedGuidelines.length > 0;

  return (
    <PageShell>
      <div className="centered-flow">
        <div className="flow-header">
          <p className="section-eyebrow">Step 1</p>
          <h2>Company setup</h2>
          <p>
            Define the company context and choose which guidelines should be checked right now.
          </p>
        </div>

        <StepIndicator steps={APP_FLOW.slice(1, 4)} currentStep={0} />

        <div className="setup-card">
          <label className="field">
            <span>Company name</span>
            <input
              type="text"
              value={companyName}
              onChange={(event) => setCompanyName(event.target.value)}
              placeholder="Nomora Life Sciences Pvt Ltd"
            />
          </label>

          <div className="field">
            <span>Guideline selector</span>
            <div className="regulator-grid">
              {REGULATORY_OPTIONS.map((option) => {
                const active = selectedGuidelines.includes(option.id);
                return (
                  <button
                    key={option.id}
                    type="button"
                    className={`regulator-card ${option.gradient} ${active ? "active" : ""}`}
                    onClick={() => onToggleGuideline(option.id)}
                  >
                    <div className="row-between">
                      <h3>{option.title}</h3>
                      <Chip tone={active ? "knowledge" : "neutral"}>
                        {active ? "Included" : "Select"}
                      </Chip>
                    </div>
                    <p>{option.description}</p>
                  </button>
                );
              })}
            </div>
          </div>

          <div className="setup-actions">
            <div className="chip-row">
              {selectedGuidelines.map((item) => (
                <Chip key={item} tone="structured">
                  {item}
                </Chip>
              ))}
            </div>
            <button
              className="primary-button"
              type="button"
              onClick={onContinue}
              disabled={!canContinue}
            >
              Continue
            </button>
          </div>

          {!canContinue ? (
            <p className="validation-note">
              Enter a company name and select at least one guideline to continue.
            </p>
          ) : (
            <p className="validation-note success">
              Setup complete. You can continue to the guided input form.
            </p>
          )}
        </div>
      </div>
    </PageShell>
  );
}

function GuidedFormPage({
  companyData,
  setCompanyData,
  selectedGuidelines,
  onBack,
  onSubmit
}) {
  const visibleSections = useMemo(
    () =>
      INTAKE_SECTIONS.filter((section) =>
        section.bodies.some((body) => selectedGuidelines.includes(body))
      ),
    [selectedGuidelines]
  );

  const [stepIndex, setStepIndex] = useState(0);
  const totalSteps = visibleSections.length + 1;
  const currentSection = visibleSections[stepIndex];
  const isReview = stepIndex === visibleSections.length;
  const completionPercent = ((stepIndex + 1) / totalSteps) * 100;

  const formSteps = [
    ...visibleSections.map((section) => ({ id: section.id, label: section.title, hint: "Data" })),
    { id: "review", label: "Review & Submit", hint: "Final check" }
  ];

  const updateField = (key, value) => {
    setCompanyData((current) => ({ ...current, [key]: value }));
  };

  const updateRecordField = (collectionKey, index, field, rawValue) => {
    const value =
      field.type === "tags"
        ? rawValue
            .split(",")
            .map((item) => item.trim())
            .filter(Boolean)
        : field.type === "number"
          ? rawValue === ""
            ? ""
            : Number(rawValue)
          : rawValue;

    setCompanyData((current) => ({
      ...current,
      [collectionKey]: (current[collectionKey] ?? []).map((item, itemIndex) =>
        itemIndex === index ? { ...item, [field.key]: value } : item
      )
    }));
  };

  const addRecord = (section) => {
    setCompanyData((current) => ({
      ...current,
      [section.collectionKey]: [...(current[section.collectionKey] ?? []), createEmptyItem(section)]
    }));
  };

  const removeRecord = (section, index) => {
    setCompanyData((current) => ({
      ...current,
      [section.collectionKey]: (current[section.collectionKey] ?? []).filter(
        (_, itemIndex) => itemIndex !== index
      )
    }));
  };

  return (
    <PageShell>
      <div className="guided-layout">
        <div className="guided-head">
          <p className="section-eyebrow">Step 2</p>
          <h2>Guided input form</h2>
          <p>Only the sections required by your selected guidelines are shown.</p>
        </div>

        <div className="progress-shell">
          <div className="progress-meta">
            <span>Completion</span>
            <strong>{Math.round(completionPercent)}%</strong>
          </div>
          <div className="progress-bar">
            <div className="progress-fill" style={{ width: `${completionPercent}%` }} />
          </div>
        </div>

        <StepIndicator steps={formSteps} currentStep={stepIndex} />

        <div className="guided-card">
          {!isReview && currentSection ? (
            <>
              <div className="guided-section-head">
                <div>
                  <h3>{currentSection.title}</h3>
                  <p>{currentSection.description}</p>
                </div>
                <div className="chip-row">
                  {currentSection.bodies.map((item) => (
                    <Chip key={item} tone={selectedGuidelines.includes(item) ? "knowledge" : "neutral"}>
                      {item}
                    </Chip>
                  ))}
                </div>
              </div>

              {!currentSection.collectionKey ? (
                <div className="form-grid">
                  {currentSection.fields.map((field) => (
                    <label className="field" key={field.key}>
                      <span>{field.label}</span>
                      <InputField
                        field={field}
                        value={companyData[field.key] ?? ""}
                        onChange={(event) => updateField(field.key, event.target.value)}
                      />
                    </label>
                  ))}
                </div>
              ) : (
                <div className="record-stack">
                  {(companyData[currentSection.collectionKey] ?? []).map((record, index) => (
                    <div className="record-card" key={`${currentSection.collectionKey}-${index}`}>
                      <div className="row-between record-topline">
                        <strong>
                          {currentSection.title} #{index + 1}
                        </strong>
                        {(companyData[currentSection.collectionKey] ?? []).length > 1 ? (
                          <button
                            type="button"
                            className="text-button danger"
                            onClick={() => removeRecord(currentSection, index)}
                          >
                            Remove
                          </button>
                        ) : null}
                      </div>

                      <div className="form-grid">
                        {currentSection.fields.map((field) => (
                          <label className="field" key={`${currentSection.collectionKey}-${index}-${field.key}`}>
                            <span>{field.label}</span>
                            <InputField
                              field={field}
                              value={record[field.key]}
                              onChange={(event) =>
                                updateRecordField(
                                  currentSection.collectionKey,
                                  index,
                                  field,
                                  event.target.value
                                )
                              }
                            />
                          </label>
                        ))}
                      </div>
                    </div>
                  ))}

                  <button type="button" className="secondary-button" onClick={() => addRecord(currentSection)}>
                    {currentSection.addLabel}
                  </button>
                </div>
              )}
            </>
          ) : (
            <div className="review-grid">
              <div className="review-card">
                <p className="section-eyebrow">Review</p>
                <h3>Ready to submit</h3>
                <p>
                  This prototype keeps the entered data in the frontend state and then moves into
                  the processing/dashboard flow.
                </p>
                <div className="chip-row">
                  {selectedGuidelines.map((item) => (
                    <Chip key={item} tone="structured">
                      {item}
                    </Chip>
                  ))}
                </div>
              </div>

              <div className="review-card">
                <p className="section-eyebrow">Snapshot</p>
                <h3>{companyData.company_name || "Unnamed company"}</h3>
                <p>Manufacturer: {companyData.manufacturer_name || "Not provided yet"}</p>
                <pre>{JSON.stringify(companyData, null, 2)}</pre>
              </div>
            </div>
          )}

          <div className="guided-actions">
            <button className="secondary-button" type="button" onClick={() => (stepIndex === 0 ? onBack() : setStepIndex((value) => value - 1))}>
              Back
            </button>
            {isReview ? (
              <button className="primary-button" type="button" onClick={onSubmit}>
                Review & Submit
              </button>
            ) : (
              <button className="primary-button" type="button" onClick={() => setStepIndex((value) => value + 1)}>
                Continue
              </button>
            )}
          </div>
        </div>
      </div>
    </PageShell>
  );
}

function ProcessingPage({ errorMessage }) {
  const [activeStep, setActiveStep] = useState(0);

  useEffect(() => {
    const interval = window.setInterval(() => {
      setActiveStep((value) => Math.min(value + 1, PROCESSING_STEPS.length - 1));
    }, 900);

    return () => window.clearInterval(interval);
  }, []);

  return (
    <PageShell>
      <div className="processing-shell">
        <div className="processing-orb" />
        <div className="processing-copy">
          <p className="section-eyebrow">Step 3</p>
          <h2>Processing your compliance posture</h2>
          <p>
            The system is simulating how Nomora would analyze regulations, match data, detect
            risk, and build recommendations.
          </p>
        </div>

        <div className="processing-steps">
          {PROCESSING_STEPS.map((step, index) => (
            <div className={`processing-step ${index <= activeStep ? "active" : ""}`} key={step}>
              <span className="processing-step-dot" />
              <span>{step}</span>
            </div>
          ))}
        </div>

        {errorMessage ? <p className="api-error centered">{errorMessage}</p> : null}

        <LoadingSkeleton />
      </div>
    </PageShell>
  );
}

function DashboardView({
  risk,
  recommendations,
  assessments,
  chatHistory,
  question,
  setQuestion,
  onAsk,
  chatBusy
}) {
  return (
    <div className="view-stack">
      <div className="sticky-summary">
        <div>
          <span className="section-eyebrow">Sticky Summary</span>
          <strong>Compliance score {100 - risk.overall_risk_score}</strong>
        </div>
        <div className="chip-row">
          <Chip tone={risk.overall_risk_band.toLowerCase()}>{risk.overall_risk_band} risk</Chip>
          <Chip tone="knowledge">{risk.total_requirements} requirements in scope</Chip>
        </div>
      </div>

      <section className="hero-dashboard">
        <div className="score-card">
          <p className="section-eyebrow">Compliance score card</p>
          <h1>{Math.max(0, 100 - risk.overall_risk_score).toFixed(0)}</h1>
          <p>
            Current posture is <strong>{risk.overall_risk_band}</strong> risk based on the selected
            guideline scope.
          </p>
        </div>

        <div className="stats-grid">
          <StatCard label="High" value={risk.status_counts.non_compliant} tone="high" />
          <StatCard label="Medium" value={risk.status_counts.partial} tone="medium" />
          <StatCard label="Low" value={risk.status_counts.compliant} tone="low" />
          <StatCard label="Requirements" value={risk.total_requirements} tone="knowledge" />
        </div>
      </section>

      <div className="dashboard-grid">
        <DonutChart counts={risk.status_counts} />
        <BarChart riskByBody={risk.risk_by_regulatory_body} />
      </div>

      <Section
        eyebrow="Recommendations"
        title="Recommended actions"
        subtitle="Issue cards prioritize what's wrong, why it matters, and the suggested fix."
      >
        <div className="recommendation-stack">
          {recommendations.recommendations.slice(0, 6).map((item) => (
            <RecommendationCard item={item} key={item.requirement_id} />
          ))}
        </div>
      </Section>

      <div className="dashboard-grid dashboard-grid-wide">
        <ChatPanel
          chatHistory={chatHistory}
          question={question}
          setQuestion={setQuestion}
          onAsk={onAsk}
          busy={chatBusy}
        />

        <Section
          eyebrow="Findings"
          title="Recent compliance findings"
          subtitle="Focused view of the latest non-compliant and partial items."
        >
          <div className="finding-stack">
            {assessments.assessments
              .filter((item) => item.status !== "compliant")
              .slice(0, 6)
              .map((item) => (
                <div className={`finding-card finding-${item.status}`} key={item.requirement_id}>
                  <div className="row-between">
                    <h4>
                      {item.requirement_id} · {item.regulatory_body}
                    </h4>
                    <Chip tone={item.status}>{item.status}</Chip>
                  </div>
                  <p>{item.evaluation_reason}</p>
                  <div className="chip-row">
                    <Chip tone="structured">{item.domain}</Chip>
                    <Chip>{item.severity}</Chip>
                  </div>
                </div>
              ))}
          </div>
        </Section>
      </div>
    </div>
  );
}

function SimulatorView({ risk, recommendations }) {
  const [selectedFixes, setSelectedFixes] = useState([]);
  const [executionConfidence, setExecutionConfidence] = useState(62);
  const [monitoringStrength, setMonitoringStrength] = useState(58);

  const simulationCandidates = recommendations.recommendations.slice(0, 5);

  const simulated = useMemo(() => {
    const reductionFromFixes = selectedFixes.length * 6.5;
    const processLift = (executionConfidence - 50) * 0.22 + (monitoringStrength - 50) * 0.18;
    const improvedRisk = Math.max(5, Number((risk.overall_risk_score - reductionFromFixes - processLift).toFixed(2)));
    return {
      score: improvedRisk,
      delta: Number((risk.overall_risk_score - improvedRisk).toFixed(2))
    };
  }, [executionConfidence, monitoringStrength, risk.overall_risk_score, selectedFixes.length]);

  const toggleFix = (id) => {
    setSelectedFixes((current) =>
      current.includes(id) ? current.filter((item) => item !== id) : [...current, id]
    );
  };

  return (
    <div className="view-stack">
      <section className="simulator-hero">
        <div>
          <p className="section-eyebrow">Simulator</p>
          <h2>Model decision impact before acting</h2>
          <p>Try potential fixes and see how the risk score could shift in real time.</p>
        </div>
        <div className="simulator-score">
          <span>Projected risk</span>
          <strong>{simulated.score}</strong>
          <small>Improvement: {simulated.delta}</small>
        </div>
      </section>

      <div className="dashboard-grid dashboard-grid-wide">
        <Section
          eyebrow="Scenario Controls"
          title="Choose fixes to simulate"
          subtitle="These toggles are based on the current top recommendations."
        >
          <div className="toggle-stack">
            {simulationCandidates.map((item) => (
              <button
                key={item.requirement_id}
                type="button"
                className={`toggle-card ${selectedFixes.includes(item.requirement_id) ? "active" : ""}`}
                onClick={() => toggleFix(item.requirement_id)}
              >
                <div>
                  <strong>{item.requirement_id}</strong>
                  <p>{item.recommended_action}</p>
                </div>
                <Chip tone={item.priority.toLowerCase()}>{item.priority}</Chip>
              </button>
            ))}
          </div>
        </Section>

        <Section
          eyebrow="Real-Time Inputs"
          title="Operational readiness"
          subtitle="Simulate stronger execution and monitoring discipline."
        >
          <div className="slider-group">
            <label className="slider-card">
              <div className="row-between">
                <span>Execution confidence</span>
                <strong>{executionConfidence}</strong>
              </div>
              <input
                type="range"
                min="0"
                max="100"
                value={executionConfidence}
                onChange={(event) => setExecutionConfidence(Number(event.target.value))}
              />
            </label>

            <label className="slider-card">
              <div className="row-between">
                <span>Monitoring strength</span>
                <strong>{monitoringStrength}</strong>
              </div>
              <input
                type="range"
                min="0"
                max="100"
                value={monitoringStrength}
                onChange={(event) => setMonitoringStrength(Number(event.target.value))}
              />
            </label>
          </div>
        </Section>
      </div>
    </div>
  );
}

function ReportsView({ companyData, risk, recommendations }) {
  return (
    <div className="view-stack">
      <section className="reports-hero">
        <div>
          <p className="section-eyebrow">Reports</p>
          <h2>Executive-ready narrative</h2>
          <p>Use this area as the clean export/report layer for the product prototype.</p>
        </div>
        <Chip tone="knowledge">No export backend yet</Chip>
      </section>

      <div className="dashboard-grid dashboard-grid-wide">
        <Section eyebrow="Summary" title="Report snapshot">
          <div className="report-card">
            <p>Company</p>
            <strong>{companyData.company_name || "Unnamed company"}</strong>
          </div>
          <div className="report-card">
            <p>Risk band</p>
            <strong>{risk.overall_risk_band}</strong>
          </div>
          <div className="report-card">
            <p>Top recommendation</p>
            <strong>{recommendations.recommendations[0]?.recommended_action ?? "None"}</strong>
          </div>
        </Section>

        <Section eyebrow="Dataset" title="Current company payload">
          <div className="json-panel compact">
            <pre>{JSON.stringify(companyData, null, 2)}</pre>
          </div>
        </Section>
      </div>
    </div>
  );
}

function Workspace({
  activeView,
  setActiveView,
  selectedGuidelines,
  companyData,
  scopedRisk,
  scopedRecommendations,
  scopedAssessment,
  chatHistory,
  question,
  setQuestion,
  onAsk,
  chatBusy,
  dashboardReady,
  analysisError,
  mobileSidebarOpen,
  setMobileSidebarOpen
}) {
  return (
    <div className="workspace-shell">
      <Sidebar
        activeView={activeView}
        onSelectView={setActiveView}
        selectedGuidelines={selectedGuidelines}
        companyName={companyData.company_name}
        mobileOpen={mobileSidebarOpen}
        onToggleMobile={setMobileSidebarOpen}
      />

      <div className="workspace-main">
        <Topbar
          companyName={companyData.company_name}
          selectedGuidelines={selectedGuidelines}
          activeView={activeView}
          onOpenSidebar={() => setMobileSidebarOpen(true)}
        />

        <main className="workspace-content">
          {!dashboardReady ? (
            <LoadingSkeleton />
          ) : analysisError ? (
            <section className="dashboard-panel">
              <div className="panel-head">
                <div>
                  <p className="section-eyebrow">Backend Error</p>
                  <h3>Nomora could not load live analysis</h3>
                </div>
              </div>
              <p className="api-error">{analysisError}</p>
              <p className="section-subtitle">
                Start the FastAPI backend and then refresh the frontend. The UI is now expecting live API responses.
              </p>
            </section>
          ) : activeView === "dashboard" ? (
            <DashboardView
              risk={scopedRisk}
              recommendations={scopedRecommendations}
              assessments={scopedAssessment}
              chatHistory={chatHistory}
              question={question}
              setQuestion={setQuestion}
              onAsk={onAsk}
              chatBusy={chatBusy}
            />
          ) : activeView === "simulator" ? (
            <SimulatorView risk={scopedRisk} recommendations={scopedRecommendations} />
          ) : (
            <ReportsView
              companyData={companyData}
              risk={scopedRisk}
              recommendations={scopedRecommendations}
            />
          )}
        </main>
      </div>
    </div>
  );
}

function App() {
  const [page, setPage] = useState("landing");
  const [companyData, setCompanyData] = useState(createInitialCompanyData);
  const [selectedGuidelines, setSelectedGuidelines] = useState([]);
  const [activeView, setActiveView] = useState("dashboard");
  const [mobileSidebarOpen, setMobileSidebarOpen] = useState(false);
  const [dashboardReady, setDashboardReady] = useState(false);
  const [analysisState, setAnalysisState] = useState({
    status: "idle",
    data: null,
    error: ""
  });
  const [question, setQuestion] = useState("");
  const [chatBusy, setChatBusy] = useState(false);
  const [chatHistory, setChatHistory] = useState([
    {
      role: "assistant",
      content:
        "I'm ready to explain risks, recommendations, and retrieved policy context once you enter the workspace.",
      answerSource: "System guidance",
      answerTone: "structured"
    }
  ]);

  const scopedAssessment = analysisState.data?.assessment ?? {
    assessments: [],
    total_requirements: 0,
    status_counts: {
      compliant: 0,
      partial: 0,
      non_compliant: 0,
      insufficient_data: 0
    }
  };
  const scopedRecommendations = analysisState.data?.recommendations ?? {
    recommendations: [],
    total_recommendations: 0
  };
  const scopedRisk = analysisState.data?.risk_report ?? {
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
    top_risk_drivers: []
  };

  useEffect(() => {
    if (page !== "processing") return undefined;
    let cancelled = false;
    setAnalysisState({ status: "loading", data: null, error: "" });

    const run = async () => {
      const startedAt = Date.now();
      try {
        const analysis = await analyzeCompany(companyData, selectedGuidelines);
        const elapsed = Date.now() - startedAt;
        const minimumDelay = Math.max(0, 2400 - elapsed);
        window.setTimeout(() => {
          if (cancelled) return;
          setAnalysisState({ status: "ready", data: analysis, error: "" });
          setPage("workspace");
          setDashboardReady(false);
        }, minimumDelay);
      } catch (error) {
        const message =
          error instanceof Error ? error.message : "Unable to analyze company data.";
        if (cancelled) return;
        setAnalysisState({ status: "error", data: null, error: message });
        setPage("workspace");
        setDashboardReady(false);
      }
    };

    run();

    return () => {
      cancelled = true;
    };
  }, [companyData, page, selectedGuidelines]);

  useEffect(() => {
    if (page !== "workspace") return undefined;

    const timer = window.setTimeout(() => {
      setDashboardReady(true);
    }, 1100);

    return () => window.clearTimeout(timer);
  }, [page]);

  const handleToggleGuideline = (body) => {
    setSelectedGuidelines((current) => {
      const next = current.includes(body)
        ? current.filter((item) => item !== body)
        : [...current, body];
      return next;
    });
  };

  const handleSetupContinue = () => {
    if (!companyData.company_name.trim()) return;
    if (!selectedGuidelines.length) return;

    setCompanyData((current) => ({
      ...current,
      regulatory_scope: selectedGuidelines
    }));
    setPage("form");
  };

  const handleAsk = async (incomingQuestion) => {
    const trimmed = incomingQuestion.trim();
    if (!trimmed) return;

    setChatHistory((current) => [
      ...current,
      { role: "user", content: trimmed },
      {
        role: "assistant",
        content: "Thinking through the live compliance context...",
        answerSource: "Processing",
        answerTone: "structured"
      }
    ]);
    setQuestion("");
    setChatBusy(true);

    try {
      const response = await chatWithCopilot(trimmed, companyData, selectedGuidelines);
      setChatHistory((current) => {
        const next = [...current];
        next[next.length - 1] = {
          role: "assistant",
          content: response.answer,
          answerSource: "Live backend analysis",
          answerTone: "llm"
        };
        return next;
      });
      if (response.analysis) {
        setAnalysisState({ status: "ready", data: response.analysis, error: "" });
      }
    } catch (error) {
      const message = error instanceof Error ? error.message : "Copilot request failed.";
      setChatHistory((current) => {
        const next = [...current];
        next[next.length - 1] = {
          role: "assistant",
          content: message,
          answerSource: "Backend error",
          answerTone: "warning"
        };
        return next;
      });
    } finally {
      setChatBusy(false);
    }
  };

  if (page === "landing") {
    return <LandingPage onStart={() => setPage("setup")} />;
  }

  if (page === "setup") {
    return (
      <SetupPage
        companyName={companyData.company_name}
        setCompanyName={(value) =>
          setCompanyData((current) => ({ ...current, company_name: value, manufacturer_name: value }))
        }
        selectedGuidelines={selectedGuidelines}
        onToggleGuideline={handleToggleGuideline}
        onContinue={handleSetupContinue}
      />
    );
  }

  if (page === "form") {
    return (
      <GuidedFormPage
        companyData={companyData}
        setCompanyData={setCompanyData}
        selectedGuidelines={selectedGuidelines}
        onBack={() => setPage("setup")}
        onSubmit={() => setPage("processing")}
      />
    );
  }

  if (page === "processing") {
    return <ProcessingPage errorMessage={analysisState.status === "error" ? analysisState.error : ""} />;
  }

  return (
    <Workspace
      activeView={activeView}
      setActiveView={setActiveView}
      selectedGuidelines={selectedGuidelines}
      companyData={companyData}
      scopedRisk={scopedRisk}
      scopedRecommendations={scopedRecommendations}
      scopedAssessment={scopedAssessment}
      chatHistory={chatHistory}
      question={question}
      setQuestion={setQuestion}
      onAsk={handleAsk}
      chatBusy={chatBusy}
      dashboardReady={dashboardReady}
      analysisError={analysisState.error}
      mobileSidebarOpen={mobileSidebarOpen}
      setMobileSidebarOpen={setMobileSidebarOpen}
    />
  );
}

export default App;


