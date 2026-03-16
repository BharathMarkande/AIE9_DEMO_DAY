/**
 * RiskHalo API client.
 * Base URL is configurable for different environments.
 */
const API_BASE = import.meta.env.VITE_API_BASE || "http://localhost:8000";

/**
 * Upload weekly trade file and risk per trade to the backend.
 * @param {File} file - .xlsx weekly trade file
 * @param {number} riskPerTrade - risk per trade value
 * @param {number} minRiskToRewardRatio - minimum risk:reward ratio for winning trades
 * @param {number} maxTradesPerDay - maximum trades allowed per day
 * @param {number} maxDailyLoss - maximum allowed daily loss
 * @returns {Promise<{ success: boolean, message?: string, error?: string }>}
 */
export async function uploadSession(
  file,
  riskPerTrade,
  minRiskToRewardRatio,
  maxTradesPerDay,
  maxDailyLoss
) {
  const formData = new FormData();
  formData.append("file", file);
  formData.append("risk_per_trade", String(riskPerTrade));
  formData.append("min_risk_to_reward_ratio", String(minRiskToRewardRatio));
  formData.append("max_trades_per_day", String(maxTradesPerDay));
  formData.append("max_daily_loss", String(maxDailyLoss));

  const response = await fetch(`${API_BASE}/upload`, {
    method: "POST",
    body: formData,
  });

  const data = await response.json().catch(() => ({}));

  if (!response.ok) {
    throw new Error(data.detail || data.error || response.statusText || "Upload failed");
  }

  return data;
}

/**
 * Send a question to the coach and consume streaming response.
 * @param {string} question - user question
 * @param {function(string): void} onStreamChunk - callback for each text chunk
 * @returns {Promise<void>}
 */
export async function askQuestion(question, onStreamChunk) {
  const response = await fetch(`${API_BASE}/ask`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ question }),
  });

  if (!response.ok) {
    const err = await response.json().catch(() => ({}));
    throw new Error(err.detail || err.error || response.statusText || "Ask failed");
  }

  const reader = response.body.getReader();
  const decoder = new TextDecoder();
  let buffer = "";

  while (true) {
    const { done, value } = await reader.read();
    if (done) break;
    buffer += decoder.decode(value, { stream: true });
    const lines = buffer.split("\n");
    buffer = lines.pop() || "";
    for (const line of lines) {
      if (line.startsWith("data: ")) {
        const data = line.slice(6);
        if (data === "[DONE]" || data === "[done]") continue;
        try {
          const parsed = JSON.parse(data);
          if (parsed.error) throw new Error(parsed.error);
          const text = parsed.text ?? parsed.content ?? parsed.chunk ?? "";
          if (text && onStreamChunk) onStreamChunk(text);
        } catch (e) {
          if (e instanceof Error && e.message !== data) throw e;
          if (data.trim() && onStreamChunk) onStreamChunk(data);
        }
      }
    }
  }

  if (buffer.trim()) {
    if (buffer.startsWith("data: ")) {
      const data = buffer.slice(6);
      try {
        const parsed = JSON.parse(data);
        if (parsed.error) throw new Error(parsed.error);
        const text = parsed.text ?? parsed.content ?? parsed.chunk ?? "";
        if (text && onStreamChunk) onStreamChunk(text);
      } catch (e) {
        if (e instanceof Error && e.message !== data) throw e;
        if (onStreamChunk) onStreamChunk(data);
      }
    } else if (onStreamChunk) {
      onStreamChunk(buffer);
    }
  }
}
