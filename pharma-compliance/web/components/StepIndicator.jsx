export default function StepIndicator({ steps, currentStep }) {
  return (
    <div className="step-indicator">
      {steps.map((step, index) => {
        const state =
          index < currentStep ? "done" : index === currentStep ? "active" : "upcoming";

        return (
          <div className={`step-node ${state}`} key={step.id}>
            <div className="step-bullet">{index + 1}</div>
            <div className="step-copy">
              <span>{step.label}</span>
              {step.hint ? <small>{step.hint}</small> : null}
            </div>
          </div>
        );
      })}
    </div>
  );
}
