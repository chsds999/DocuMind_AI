const API_BASE = "/api";

export async function ingestPdf(file) {
  const form = new FormData();
  form.append("file", file);

  const res = await fetch(`${API_BASE}/ingest`, {
    method: "POST",
    body: form
  });

  if (!res.ok) {
    const text = await res.text();
    throw new Error(text || "Failed to ingest PDF");
  }
  return res.json();
}

export async function askQuestion({ docId, question, k = 5 }) {
  const res = await fetch(`${API_BASE}/ask`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ doc_id: docId, question, k })
  });

  if (!res.ok) {
    const text = await res.text();
    throw new Error(text || "Failed to ask question");
  }
  return res.json();
}
