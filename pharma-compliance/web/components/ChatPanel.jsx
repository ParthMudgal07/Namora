import Chip from "./Chip";

export default function ChatPanel({ chatHistory, question, setQuestion, onAsk, busy = false }) {
  return (
    <section className="dashboard-panel chat-panel">
      <div className="panel-head">
        <div>
          <p className="section-eyebrow">RAG Copilot</p>
          <h3>Grounded compliance assistant</h3>
        </div>
        <Chip tone="llm">Knowledge + reasoning</Chip>
      </div>

      <div className="quick-prompts">
        {[
          "What should we fix first?",
          "What are our top 5 compliance risks?",
          "Show NPPA issues.",
          "What company evidence do we have for equipment calibration?"
        ].map((prompt) => (
          <button key={prompt} className="prompt-button" onClick={() => onAsk(prompt)} type="button" disabled={busy}>
            {prompt}
          </button>
        ))}
      </div>

      <div className="chat-log">
        {chatHistory.map((entry, index) => (
          <div className={`chat-bubble ${entry.role}`} key={`${entry.role}-${index}`}>
            <div className="row-between chat-topline">
              <div className="chat-role">{entry.role === "assistant" ? "Nomora Copilot" : "You"}</div>
              {entry.role === "assistant" && entry.answerSource ? (
                <Chip tone={entry.answerTone ?? "neutral"}>{entry.answerSource}</Chip>
              ) : null}
            </div>
            <pre>{entry.content}</pre>
          </div>
        ))}
      </div>

      <div className="chat-form">
        <textarea
          rows="4"
          value={question}
          onChange={(event) => setQuestion(event.target.value)}
          placeholder="Ask a policy question, a risk question, or a recommendation question..."
          disabled={busy}
        />
        <button onClick={() => onAsk(question)} type="button" disabled={busy}>
          {busy ? "Thinking..." : "Send to Copilot"}
        </button>
      </div>
    </section>
  );
}
