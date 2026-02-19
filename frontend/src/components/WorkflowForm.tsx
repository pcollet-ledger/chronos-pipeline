import { useState } from "react";
import type { TaskDefinition, ValidAction, WorkflowCreatePayload } from "../types";

const VALID_ACTIONS: ValidAction[] = [
  "log",
  "transform",
  "validate",
  "notify",
  "aggregate",
];

interface TaskEntry {
  name: string;
  action: ValidAction;
  parameters: Array<{ key: string; value: string }>;
  depends_on: string[];
}

interface FormErrors {
  name?: string;
  description?: string;
  tags?: string;
  tasks?: Record<number, { name?: string; action?: string }>;
}

interface Props {
  initialData?: {
    name: string;
    description: string;
    tags: string[];
    tasks: TaskDefinition[];
  };
  onSubmit: (data: WorkflowCreatePayload) => void;
  onCancel?: () => void;
}

function taskDefToEntry(t: TaskDefinition): TaskEntry {
  const params = Object.entries(t.parameters).map(([key, value]) => ({
    key,
    value: String(value),
  }));
  return {
    name: t.name,
    action: (VALID_ACTIONS.includes(t.action as ValidAction)
      ? t.action
      : "log") as ValidAction,
    parameters: params.length > 0 ? params : [{ key: "", value: "" }],
    depends_on: t.depends_on,
  };
}

export default function WorkflowForm({ initialData, onSubmit, onCancel }: Props) {
  const [name, setName] = useState(initialData?.name ?? "");
  const [description, setDescription] = useState(
    initialData?.description ?? "",
  );
  const [tagsInput, setTagsInput] = useState(
    initialData?.tags.join(", ") ?? "",
  );
  const [tasks, setTasks] = useState<TaskEntry[]>(
    initialData?.tasks.map(taskDefToEntry) ?? [],
  );
  const [errors, setErrors] = useState<FormErrors>({});

  function validate(): FormErrors {
    const errs: FormErrors = {};
    if (!name.trim()) {
      errs.name = "Workflow name is required";
    } else if (name.length > 200) {
      errs.name = "Name must be 200 characters or fewer";
    }

    const taskErrors: Record<number, { name?: string; action?: string }> = {};
    tasks.forEach((t, i) => {
      const te: { name?: string; action?: string } = {};
      if (!t.name.trim()) te.name = "Task name is required";
      if (!VALID_ACTIONS.includes(t.action)) te.action = "Invalid action";
      if (Object.keys(te).length > 0) taskErrors[i] = te;
    });
    if (Object.keys(taskErrors).length > 0) errs.tasks = taskErrors;

    return errs;
  }

  function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    const errs = validate();
    setErrors(errs);
    if (Object.keys(errs).length > 0) return;

    const tags = tagsInput
      .split(",")
      .map((t) => t.trim())
      .filter(Boolean);

    const payload: WorkflowCreatePayload = {
      name: name.trim(),
      description: description.trim(),
      tags,
      tasks: tasks.map((t) => {
        const params: Record<string, string> = {};
        t.parameters.forEach((p) => {
          if (p.key.trim()) params[p.key.trim()] = p.value;
        });
        return {
          name: t.name.trim(),
          action: t.action,
          parameters: params,
          depends_on: t.depends_on,
        };
      }),
    };
    onSubmit(payload);
  }

  function addTask() {
    setTasks([
      ...tasks,
      { name: "", action: "log", parameters: [{ key: "", value: "" }], depends_on: [] },
    ]);
  }

  function removeTask(index: number) {
    setTasks(tasks.filter((_, i) => i !== index));
  }

  function moveTask(index: number, direction: -1 | 1) {
    const newIndex = index + direction;
    if (newIndex < 0 || newIndex >= tasks.length) return;
    const updated = [...tasks];
    const a = updated[index];
    const b = updated[newIndex];
    if (!a || !b) return;
    updated[index] = b;
    updated[newIndex] = a;
    setTasks(updated);
  }

  function updateTask(index: number, field: keyof TaskEntry, value: unknown) {
    const updated = [...tasks];
    const existing = updated[index];
    if (!existing) return;
    updated[index] = { ...existing, [field]: value };
    setTasks(updated);
  }

  function addParam(taskIndex: number) {
    const updated = [...tasks];
    const existing = updated[taskIndex];
    if (!existing) return;
    updated[taskIndex] = {
      ...existing,
      parameters: [...existing.parameters, { key: "", value: "" }],
    };
    setTasks(updated);
  }

  function removeParam(taskIndex: number, paramIndex: number) {
    const updated = [...tasks];
    const existing = updated[taskIndex];
    if (!existing) return;
    updated[taskIndex] = {
      ...existing,
      parameters: existing.parameters.filter((_, i) => i !== paramIndex),
    };
    setTasks(updated);
  }

  function updateParam(
    taskIndex: number,
    paramIndex: number,
    field: "key" | "value",
    val: string,
  ) {
    const updated = [...tasks];
    const existing = updated[taskIndex];
    if (!existing) return;
    const params = [...existing.parameters];
    const param = params[paramIndex];
    if (!param) return;
    params[paramIndex] = { ...param, [field]: val };
    updated[taskIndex] = { ...existing, parameters: params };
    setTasks(updated);
  }

  const otherTaskNames = (currentIndex: number): string[] =>
    tasks.filter((_, i) => i !== currentIndex).map((t) => t.name).filter(Boolean);

  function toggleDependency(taskIndex: number, depName: string) {
    const updated = [...tasks];
    const existing = updated[taskIndex];
    if (!existing) return;
    const deps = existing.depends_on;
    if (deps.includes(depName)) {
      updated[taskIndex] = {
        ...existing,
        depends_on: deps.filter((d) => d !== depName),
      };
    } else {
      updated[taskIndex] = {
        ...existing,
        depends_on: [...deps, depName],
      };
    }
    setTasks(updated);
  }

  const inputStyle: React.CSSProperties = {
    padding: "8px 12px",
    borderRadius: "6px",
    border: "1px solid #334155",
    background: "#1e293b",
    color: "#e2e8f0",
    fontSize: "14px",
    outline: "none",
    width: "100%",
    boxSizing: "border-box",
  };

  const errorStyle: React.CSSProperties = {
    color: "#fca5a5",
    fontSize: "12px",
    marginTop: "4px",
  };

  return (
    <form onSubmit={handleSubmit} data-testid="workflow-form">
      <div style={{ marginBottom: "16px" }}>
        <label style={{ display: "block", color: "#94a3b8", fontSize: "13px", marginBottom: "4px" }}>
          Workflow Name *
        </label>
        <input
          type="text"
          value={name}
          onChange={(e) => setName(e.target.value)}
          placeholder="Enter workflow name"
          maxLength={200}
          style={inputStyle}
          data-testid="workflow-name-input"
        />
        {errors.name && <div style={errorStyle} data-testid="name-error">{errors.name}</div>}
      </div>

      <div style={{ marginBottom: "16px" }}>
        <label style={{ display: "block", color: "#94a3b8", fontSize: "13px", marginBottom: "4px" }}>
          Description
        </label>
        <textarea
          value={description}
          onChange={(e) => setDescription(e.target.value)}
          placeholder="Describe this workflow..."
          rows={3}
          style={{ ...inputStyle, resize: "vertical" }}
          data-testid="workflow-description-input"
        />
      </div>

      <div style={{ marginBottom: "16px" }}>
        <label style={{ display: "block", color: "#94a3b8", fontSize: "13px", marginBottom: "4px" }}>
          Tags (comma-separated)
        </label>
        <input
          type="text"
          value={tagsInput}
          onChange={(e) => setTagsInput(e.target.value)}
          placeholder="e.g. production, daily, etl"
          style={inputStyle}
          data-testid="workflow-tags-input"
        />
        {tagsInput && (
          <div style={{ display: "flex", gap: "6px", marginTop: "8px", flexWrap: "wrap" }}>
            {tagsInput
              .split(",")
              .map((t) => t.trim())
              .filter(Boolean)
              .map((tag) => (
                <span
                  key={tag}
                  style={{
                    padding: "2px 8px",
                    borderRadius: "4px",
                    background: "#334155",
                    color: "#94a3b8",
                    fontSize: "12px",
                  }}
                >
                  {tag}
                </span>
              ))}
          </div>
        )}
      </div>

      {/* Tasks */}
      <div style={{ marginBottom: "16px" }}>
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "8px" }}>
          <label style={{ color: "#94a3b8", fontSize: "13px" }}>Tasks</label>
          <button
            type="button"
            onClick={addTask}
            data-testid="add-task-button"
            style={{
              padding: "4px 12px",
              borderRadius: "4px",
              border: "1px solid #334155",
              background: "#1e293b",
              color: "#94a3b8",
              cursor: "pointer",
              fontSize: "12px",
            }}
          >
            + Add Task
          </button>
        </div>

        {tasks.map((task, ti) => (
          <div
            key={ti}
            data-testid={`task-entry-${ti}`}
            style={{
              background: "#0f172a",
              borderRadius: "8px",
              padding: "12px",
              marginBottom: "8px",
              border: "1px solid #1e293b",
            }}
          >
            <div style={{ display: "flex", justifyContent: "space-between", marginBottom: "8px" }}>
              <span style={{ color: "#64748b", fontSize: "12px" }}>Task {ti + 1}</span>
              <div style={{ display: "flex", gap: "4px" }}>
                <button type="button" onClick={() => moveTask(ti, -1)} disabled={ti === 0}
                  style={{ padding: "2px 6px", border: "none", background: "transparent", color: "#64748b", cursor: "pointer", fontSize: "12px" }}>
                  ↑
                </button>
                <button type="button" onClick={() => moveTask(ti, 1)} disabled={ti === tasks.length - 1}
                  style={{ padding: "2px 6px", border: "none", background: "transparent", color: "#64748b", cursor: "pointer", fontSize: "12px" }}>
                  ↓
                </button>
                <button type="button" onClick={() => removeTask(ti)} data-testid={`remove-task-${ti}`}
                  style={{ padding: "2px 6px", border: "none", background: "transparent", color: "#ef4444", cursor: "pointer", fontSize: "12px" }}>
                  Remove
                </button>
              </div>
            </div>

            <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "8px", marginBottom: "8px" }}>
              <div>
                <input
                  type="text"
                  value={task.name}
                  onChange={(e) => updateTask(ti, "name", e.target.value)}
                  placeholder="Task name"
                  style={inputStyle}
                  data-testid={`task-name-${ti}`}
                />
                {errors.tasks?.[ti]?.name && (
                  <div style={errorStyle}>{errors.tasks[ti].name}</div>
                )}
              </div>
              <select
                value={task.action}
                onChange={(e) => updateTask(ti, "action", e.target.value)}
                style={inputStyle}
                data-testid={`task-action-${ti}`}
              >
                {VALID_ACTIONS.map((a) => (
                  <option key={a} value={a}>{a}</option>
                ))}
              </select>
            </div>

            {/* Parameters */}
            <div style={{ marginBottom: "8px" }}>
              <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "4px" }}>
                <span style={{ color: "#64748b", fontSize: "11px" }}>Parameters</span>
                <button type="button" onClick={() => addParam(ti)}
                  style={{ padding: "2px 8px", border: "none", background: "transparent", color: "#38bdf8", cursor: "pointer", fontSize: "11px" }}>
                  + Add
                </button>
              </div>
              {task.parameters.map((p, pi) => (
                <div key={pi} style={{ display: "flex", gap: "4px", marginBottom: "4px" }}>
                  <input
                    type="text"
                    value={p.key}
                    onChange={(e) => updateParam(ti, pi, "key", e.target.value)}
                    placeholder="Key"
                    style={{ ...inputStyle, flex: 1 }}
                  />
                  <input
                    type="text"
                    value={p.value}
                    onChange={(e) => updateParam(ti, pi, "value", e.target.value)}
                    placeholder="Value"
                    style={{ ...inputStyle, flex: 1 }}
                  />
                  <button type="button" onClick={() => removeParam(ti, pi)}
                    style={{ padding: "4px 8px", border: "none", background: "transparent", color: "#ef4444", cursor: "pointer", fontSize: "12px" }}>
                    ×
                  </button>
                </div>
              ))}
            </div>

            {/* Dependencies */}
            {otherTaskNames(ti).length > 0 && (
              <div>
                <span style={{ color: "#64748b", fontSize: "11px" }}>Depends on:</span>
                <div style={{ display: "flex", gap: "6px", marginTop: "4px", flexWrap: "wrap" }}>
                  {otherTaskNames(ti).map((depName) => (
                    <label
                      key={depName}
                      style={{
                        display: "flex",
                        alignItems: "center",
                        gap: "4px",
                        padding: "2px 8px",
                        borderRadius: "4px",
                        background: task.depends_on.includes(depName) ? "#1e40af" : "#334155",
                        color: "#94a3b8",
                        fontSize: "11px",
                        cursor: "pointer",
                      }}
                    >
                      <input
                        type="checkbox"
                        checked={task.depends_on.includes(depName)}
                        onChange={() => toggleDependency(ti, depName)}
                        style={{ display: "none" }}
                      />
                      {depName}
                    </label>
                  ))}
                </div>
              </div>
            )}
          </div>
        ))}
      </div>

      {/* Form actions */}
      <div style={{ display: "flex", gap: "8px", justifyContent: "flex-end" }}>
        {onCancel && (
          <button
            type="button"
            onClick={onCancel}
            style={{
              padding: "8px 20px",
              borderRadius: "6px",
              border: "1px solid #334155",
              background: "transparent",
              color: "#94a3b8",
              cursor: "pointer",
              fontSize: "14px",
            }}
          >
            Cancel
          </button>
        )}
        <button
          type="submit"
          data-testid="submit-button"
          style={{
            padding: "8px 20px",
            borderRadius: "6px",
            border: "none",
            background: "#2563eb",
            color: "#fff",
            cursor: "pointer",
            fontWeight: 600,
            fontSize: "14px",
          }}
        >
          {initialData ? "Update Workflow" : "Create Workflow"}
        </button>
      </div>
    </form>
  );
}
