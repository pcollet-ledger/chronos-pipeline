import { useState } from "react";
import type { ExecutionComparison } from "../types";
import { compareExecutions } from "../services/api";
import ErrorBanner from "./ErrorBanner";
import LoadingSpinner from "./LoadingSpinner";

interface Props {
  onBack: () => void;
}

export default function ExecutionComparisonView({ onBack }: Props) {
  const [idA, setIdA] = useState("");
  const [idB, setIdB] = useState("");
  const [result, setResult] = useState<ExecutionComparison | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleCompare = async () => {
    if (!idA.trim() || !idB.trim()) {
      setError("Both execution IDs are required");
      return;
    }
    try {
      setError(null);
      setLoading(true);
      const data = await compareExecutions(idA.trim(), idB.trim());
      setResult(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Comparison failed");
    } finally {
      setLoading(false);
    }
  };

  const inputStyle: React.CSSProperties = {
    padding: "8px 12px",
    borderRadius: "6px",
    border: "1px solid #334155",
    background: "#1e293b",
    color: "#e2e8f0",
    fontSize: "14px",
    outline: "none",
    flex: 1,
  };

  const diffColor = (statusA: string, statusB: string): string => {
    if (statusA === statusB) return "#64748b";
    if (statusB === "completed" && statusA !== "completed") return "#22c55e";
    if (statusA === "completed" && statusB !== "completed") return "#ef4444";
    return "#eab308";
  };

  return (
    <div>
      <button
        onClick={onBack}
        data-testid="back-button"
        style={{
          padding: "6px 14px",
          borderRadius: "6px",
          border: "1px solid #334155",
          background: "transparent",
          color: "#94a3b8",
          cursor: "pointer",
          fontSize: "13px",
          marginBottom: "16px",
        }}
      >
        Back
      </button>

      <h2 style={{ fontSize: "18px", color: "#e2e8f0", marginBottom: "16px" }}>
        Compare Executions
      </h2>

      {error && <ErrorBanner message={error} onDismiss={() => setError(null)} />}

      <div
        style={{
          display: "flex",
          gap: "8px",
          marginBottom: "20px",
          alignItems: "center",
        }}
      >
        <input
          type="text"
          value={idA}
          onChange={(e) => setIdA(e.target.value)}
          placeholder="Execution ID A"
          data-testid="id-a-input"
          style={inputStyle}
        />
        <span style={{ color: "#475569", fontSize: "14px" }}>vs</span>
        <input
          type="text"
          value={idB}
          onChange={(e) => setIdB(e.target.value)}
          placeholder="Execution ID B"
          data-testid="id-b-input"
          style={inputStyle}
        />
        <button
          onClick={() => void handleCompare()}
          data-testid="compare-button"
          style={{
            padding: "8px 20px",
            borderRadius: "6px",
            border: "none",
            background: "#2563eb",
            color: "#fff",
            cursor: "pointer",
            fontWeight: 600,
            fontSize: "14px",
            whiteSpace: "nowrap",
          }}
        >
          Compare
        </button>
      </div>

      {loading && <LoadingSpinner label="Comparing..." />}

      {result && !loading && (
        <div>
          {/* Summary */}
          <div
            style={{
              display: "flex",
              gap: "16px",
              marginBottom: "20px",
            }}
          >
            <SummaryCard label="Improved" value={result.summary.improved_count} color="#22c55e" />
            <SummaryCard label="Regressed" value={result.summary.regressed_count} color="#ef4444" />
            <SummaryCard label="Unchanged" value={result.summary.unchanged_count} color="#64748b" />
          </div>

          {/* Task comparison table */}
          <div
            style={{
              background: "#1e293b",
              borderRadius: "12px",
              padding: "16px",
            }}
          >
            <h3 style={{ fontSize: "14px", color: "#94a3b8", marginBottom: "12px" }}>
              Task Comparison
            </h3>
            {result.task_comparison.length === 0 ? (
              <div style={{ color: "#475569", fontSize: "14px" }}>
                No task-level differences
              </div>
            ) : (
              <table style={{ width: "100%", borderCollapse: "collapse" }}>
                <thead>
                  <tr style={{ borderBottom: "1px solid #334155" }}>
                    <th style={thStyle}>Task</th>
                    <th style={thStyle}>Status A</th>
                    <th style={thStyle}>Status B</th>
                    <th style={thStyle}>Duration Diff</th>
                  </tr>
                </thead>
                <tbody>
                  {result.task_comparison.map((tc) => (
                    <tr key={tc.task_id} style={{ borderBottom: "1px solid #1e293b" }}>
                      <td style={tdStyle}>{tc.task_id.slice(0, 8)}...</td>
                      <td style={{ ...tdStyle, textTransform: "capitalize" }}>{tc.status_a}</td>
                      <td
                        style={{
                          ...tdStyle,
                          color: diffColor(tc.status_a, tc.status_b),
                          fontWeight: 600,
                          textTransform: "capitalize",
                        }}
                      >
                        {tc.status_b}
                      </td>
                      <td style={tdStyle}>
                        {tc.duration_diff_ms != null
                          ? `${tc.duration_diff_ms > 0 ? "+" : ""}${tc.duration_diff_ms.toFixed(0)}ms`
                          : "—"}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            )}
          </div>
        </div>
      )}
    </div>
  );
}

function SummaryCard({
  label,
  value,
  color,
}: {
  label: string;
  value: number;
  color: string;
}) {
  return (
    <div
      style={{
        background: "#1e293b",
        borderRadius: "12px",
        padding: "16px 20px",
        flex: 1,
        textAlign: "center",
      }}
    >
      <div style={{ fontSize: "12px", color: "#64748b", marginBottom: "4px" }}>
        {label}
      </div>
      <div style={{ fontSize: "24px", fontWeight: 700, color }}>{value}</div>
    </div>
  );
}

const thStyle: React.CSSProperties = {
  textAlign: "left",
  padding: "8px 12px",
  fontSize: "12px",
  color: "#64748b",
  fontWeight: 600,
  textTransform: "uppercase",
};

const tdStyle: React.CSSProperties = {
  padding: "10px 12px",
  fontSize: "14px",
  color: "#cbd5e1",
};
