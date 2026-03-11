const API_BASE_URL =
  process.env.NEXT_PUBLIC_API_BASE_URL ||
  (process.env.NODE_ENV === "development" ? "http://localhost:8000" : "");

export const API = {
  CALCULATE: `${API_BASE_URL}/api/calculate`,
  MOCK_1040: `${API_BASE_URL}/api/mock-1040`,
  AGENT_RUN: `${API_BASE_URL}/api/agent-run`,
};

