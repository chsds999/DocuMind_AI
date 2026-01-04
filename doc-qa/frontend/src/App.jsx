import React, { useMemo, useState } from "react";
import { ingestPdf, askQuestion } from "./api";

export default function App() {
  const [file, setFile] = useState(null);
  const [docId, setDocId] = useState("");
  const [status, setStatus] = useState("");
  const [question, setQuestion] = useState("");
  const [chat, setChat] = useState([]); // {role, content, citations?}
  const canAsk = useMemo(() => docId && question.trim().length > 0, [docId, question]);

  async function handleUpload() {
    if (!file) return;
    try {
      setStatus("Uploading & indexing...");
      const data = await ingestPdf(file);
      setDocId(data.doc_id);
      setStatus(`Indexed ✅ Pages: ${data.pages}, Chunks: ${data.chunks}`);
      setChat((c) => [
        ...c,
        { role: "system", content: `Document ready (doc_id: ${data.doc_id})` }
      ]);
    } catch (e) {
      setStatus(`Error: ${e.message}`);
    }
  }

  async function handleAsk() {
    if (!canAsk) return;
    const q = question.trim();
    setChat((c) => [...c, { role: "user", content: q }]);
    setQuestion("");

    try {
      const res = await askQuestion({ docId, question: q, k: 5 });
      setChat((c) => [
        ...c,
        { role: "assistant", content: res.answer, citations: res.citations || [] }
      ]);
    } catch (e) {
      setChat((c) => [...c, { role: "assistant", content: `Error: ${e.message}` }]);
    }
  }

  return (
    <div className="container">
      <header>
        <h1>Document Q&A (PDF)</h1>
        <p>Upload a PDF, then ask questions grounded in its content.</p>
      </header>

      <section className="card">
        <h2>1) Upload PDF</h2>
        <div className="row">
          <input
            type="file"
            accept="application/pdf"
            onChange={(e) => setFile(e.target.files?.[0] || null)}
          />
          <button onClick={handleUpload} disabled={!file}>
            Upload & Index
          </button>
        </div>
        <div className="muted">{status}</div>
        {docId && <div className="muted">doc_id: <code>{docId}</code></div>}
      </section>

      <section className="card">
        <h2>2) Ask</h2>
        <div className="row">
          <input
            className="grow"
            placeholder="Ask something about the PDF..."
            value={question}
            onChange={(e) => setQuestion(e.target.value)}
            onKeyDown={(e) => {
              if (e.key === "Enter") handleAsk();
            }}
          />
          <button onClick={handleAsk} disabled={!canAsk}>
            Ask
          </button>
        </div>
      </section>

      <section className="card">
        <h2>Chat</h2>
        <div className="chat">
          {chat.map((m, idx) => (
            <div key={idx} className={`msg ${m.role}`}>
              <div className="role">{m.role}</div>
              <div className="content">{m.content}</div>

              {m.citations?.length > 0 && (
                <div className="citations">
                  <div className="muted">Citations:</div>
                  <ul>
                    {m.citations.map((c, i) => (
                      <li key={i}>
                        <strong>Page {c.page}:</strong> {c.snippet}…
                      </li>
                    ))}
                  </ul>
                </div>
              )}
            </div>
          ))}
        </div>
      </section>

      <footer className="muted">
        Tip: PDFs with scanned images won’t extract text well unless you add OCR later.
      </footer>
    </div>
  );
}
