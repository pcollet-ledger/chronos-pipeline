import { useCallback, useEffect, useState } from "react";
import type { Workflow, WorkflowExecution } from "../types";
import * as api from "../services/api";
import TaskCard from "./TaskCard";
import ProgressBar from "./ProgressBar";
import LoadingSpinner from "./LoadingSpinner";
import ErrorBanner from "./ErrorBanner";

interface WorkflowDetailProps {
  workflowId: string;
  onBack: () => void;
}

export default function WorkflowDetail({ workflowId, onBack }: WorkflowDetailProps) {
  const [workflow, setWorkflow] = useState<Workflow | null>(null);
  const [executions, setExecutions] = useState<WorkflowExecution[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [executing, setExecuting] = useState(false);

  const load = useCallback(() => {
    setLoading(true);
    setError(null);
    Promise.all([
      api.getWorkflow(workflowId),
      api.listWorkflowExecutions(workflowId, 10),
    ])
      .then(([w, execs]) => {
        setWorkflow(w);
        setExecutions(execs);
      })
      .catch((err: Error) => setError(err.message))
      .finally(() => setLoading(false));
  }, [workflowId]);

  useEffect(() => {
    load();
  }, [load]);

  const handleExecute = async () => {
    setExecuting(true);
    try {
      await api.executeWorkflow(workflowId);
      load();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Execution failed");
    } finally {
      setExecuting(false);
    }
  };

  const handleClone = async () => {
    try {
      await api.cloneWorkflow(workflowId);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Clone failed");
    }
  };

  const handleDryRun = async () => {
    try {
      await api.dryRunWorkflow(workflowId);
      load();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Dry-run failed");
    }
  };

  if (loading) return <LoadingSpinner />;
  if (error) return <ErrorBanner message={error} onRetry={load} />;
  if (!workflow) return <ErrorBanner message="Workflow not found" />;

  const latestExec = executions[0] ?? null;
  const completedTasks = latestExec
    ? latestExec.task_results.filter((t) => t.status === "completed").length
    : 0;

  return (
    <div data-testid="workflow-detail">
      <div style={{ display: "flex", alignItems: "center", gap: 12, marginBottom: 16 }}>
        <button onClick={onBack} data-testid="back-btn" style={{ cursor: "pointer" }}>
          Back
        </button>
        <h2 style={{ margin: 0 }}>{workflow.name}</h2>
        <span style={{ color: "#6b7280", fontSize: 14 }}>v{workflow.version}</span>
      </div>

      {workflow.description && (
        <p style={{ color: "#6b7280", marginBottom: 16 }}>{workflow.description}</p>
      )}

      {workflow.tags.length > 0 && (
        <div style={{ display: "flex", gap: 6, marginBottom: 16, flexWrap: "wrap" }}>
          {workflow.tags.map((tag) => (
            <span
              key={tag}
              style={{
                padding: "2px 8px",
                borderRadius: 4,
                backgroundColor: "#e0e7ff",
                color: "#3730a3",
                fontSize: 12,
              }}
            >
              {tag}
            </span>
          ))}
        </div>
      )}

      <div style={{ display: "flex", gap: 8, marginBottom: 24 }}>
        <button onClick={handleExecute} disabled={executing} data-testid="execute-btn">
          {executing ? "Executing..." : "Execute"}
        </button>
        <button onClick={handleClone} data-testid="clone-btn">
          Clone
        </button>
        <button onClick={handleDryRun} data-testid="dry-run-btn">
          Dry Run
        </button>
      </div>

      {latestExec && (
        <div style={{ marginBottom: 24 }}>
          <h3>Latest Execution</h3>
          <ProgressBar
            completed={completedTasks}
            total={latestExec.task_results.length}
            status={latestExec.status}
          />
          <p style={{ fontSize: 14, color: "#6b7280", marginTop: 4 }}>
            {latestExec.status} &mdash; {completedTasks}/{latestExec.task_results.length} tasks
          </p>
        </div>
      )}

      <h3>Tasks ({workflow.tasks.length})</h3>
      <div style={{ display: "flex", flexDirection: "column", gap: 8 }}>
        {workflow.tasks.map((task) => (
          <TaskCard key={task.id} task={task} />
        ))}
      </div>

      {executions.length > 0 && (
        <>
          <h3 style={{ marginTop: 24 }}>Recent Executions</h3>
          <table style={{ width: "100%", borderCollapse: "collapse" }}>
            <thead>
              <tr>
                <th style={{ textAlign: "left", padding: 8 }}>ID</th>
                <th style={{ textAlign: "left", padding: 8 }}>Status</th>
                <th style={{ textAlign: "left", padding: 8 }}>Trigger</th>
                <th style={{ textAlign: "left", padding: 8 }}>Started</th>
              </tr>
            </thead>
            <tbody>
              {executions.map((exec) => (
                <tr key={exec.id} data-testid="execution-row">
                  <td style={{ padding: 8, fontFamily: "monospace", fontSize: 12 }}>
                    {exec.id.slice(0, 8)}
                  </td>
                  <td style={{ padding: 8 }}>{exec.status}</td>
                  <td style={{ padding: 8 }}>{exec.trigger}</td>
                  <td style={{ padding: 8, fontSize: 12 }}>
                    {exec.started_at ? new Date(exec.started_at).toLocaleString() : "—"}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </>
      )}
    </div>
  );
}
