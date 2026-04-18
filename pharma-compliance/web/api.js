const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || "";

async function request(path, payload) {
  const response = await fetch(`${API_BASE_URL}${path}`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json"
    },
    body: JSON.stringify(payload)
  });

  if (!response.ok) {
    const text = await response.text();
    throw new Error(text || `Request failed with status ${response.status}`);
  }

  return response.json();
}

export async function analyzeCompany(companyData, selectedGuidelines) {
  return request("/api/analyze", {
    company_data: companyData,
    selected_guidelines: selectedGuidelines
  });
}

export async function chatWithCopilot(question, companyData, selectedGuidelines) {
  return request("/api/chat", {
    question,
    company_data: companyData,
    selected_guidelines: selectedGuidelines
  });
}
