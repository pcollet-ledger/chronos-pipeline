import { useState } from "react";
import type {
  ActionName,
  TaskFieldErrors,
  TaskFormEntry,
  Workflow,
  WorkflowFormErrors,
} from "../types";
import { ACTION_NAMES, PRIORITY_OPTIONS } from "../types";
import { createWorkflow, updateWorkflow } from "../services/api";
import {
  colors,
  fontSizes,
  fontWeights,
  radii,
  spacing,
} from "../styles/theme";

// ---------------------------------------------------------------------------
// Constants
// ---------------------------------------------------------------------------

const MAX_NAME_LENGTH = 200;

// ---------------------------------------------------------------------------
// Props
// ---------------------------------------------------------------------------

interface Props {
  /** When provided the form operates in edit mode and pre-fills values. */
  workflow?: Workflow;
  onSuccess: () => void;
  onCancel: () => void;
}

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

function emptyTask(): TaskFormEntry {
  return {
    name: "",
    action: "log",
    parameters: {},
    depends_on: [],
    pre_hook: "",
    post_hook: "",
    priority: "medium",
  };
}

function workflowToFormTasks(wf: Workflow): TaskFormEntry[] {
  return wf.tasks.map((t) => ({
    name: t.name,
    action: t.action as ActionName,
    parameters: Object.fromEntries(
      Object.entries(t.parameters).map(([k, v]) => [k, String(v)]),
    ),
    depends_on: [...t.depends_on],
    pre_hook: t.pre_hook ?? "",
    post_hook: t.post_hook ?? "",
    priority: t.priority,
  }));
}

// ---------------------------------------------------------------------------
// Validation
// ---------------------------------------------------------------------------

/** Validate the entire form and return an errors object (empty = valid). */
export function validateForm(
  name: string,
  description: string,
  tasks: TaskFormEntry[],
): WorkflowFormErrors {
  const errors: WorkflowFormErrors = {};

  if (!name.trim()) {
    errors.name = "Workflow name is required.";
  } else if (name.length > MAX_NAME_LENGTH) {
    errors.name = `Name must be at most ${MAX_NAME_LENGTH} characters.`;
  }

  if (description.length > 5000) {
    errors.description = "Description must be at most 5 000 characters.";
  }

  const taskErrors: Record<number, TaskFieldErrors> = {};
  const taskNames = new Set<string>();

  tasks.forEach((task, idx) => {
    const te: TaskFieldErrors = {};

    if (!task.name.trim()) {
      te.name = "Task name is required.";
    } else if (taskNames.has(task.name.trim())) {
      te.name = "Duplicate task name.";
    }
    taskNames.add(task.name.trim());

    if (!ACTION_NAMES.includes(task.action)) {
      te.action = "Please select a valid action.";
    }

    for (const dep of task.depends_on) {
      const available = tasks
        .filter((_, i) => i !== idx)
        .map((t) => t.name.trim());
      if (!available.includes(dep)) {
        te.depends_on = `Unknown dependency: "${dep}".`;
        break;
      }
    }

    if (Object.keys(te).length > 0) {
      taskErrors[idx] = te;
    }
  });

  if (Object.keys(taskErrors).length > 0) {
    errors.taskErrors = taskErrors;
  }

  return errors;
}

/** Returns true when the errors object has no entries. */
function isValid(errors: WorkflowFormErrors): boolean {
  return (
    !errors.name &&
    !errors.description &&
    !errors.tags &&
    !errors.tasks &&
    (!errors.taskErrors || Object.keys(errors.taskErrors).length === 0)
  );
}

// ---------------------------------------------------------------------------
// Shared inline styles
// ---------------------------------------------------------------------------

const inputStyle: React.CSSProperties = {
  width: "100%",
  padding: `${spacing.sm} ${spacing.md}`,
  borderRadius: radii.md,
  border: `1px solid ${colors.neutral[700]}`,
  background: colors.neutral[900],
  color: colors.neutral[200],
  fontSize: fontSizes.base,
  outline: "none",
  boxSizing: "border-box",
};

const labelStyle: React.CSSProperties = {
  display: "block",
  fontSize: fontSizes.sm,
  color: colors.neutral[400],
  marginBottom: spacing.xs,
  fontWeight: fontWeights.medium,
};

const errorTextStyle: React.CSSProperties = {
  fontSize: fontSizes.sm,
  color: colors.error.main,
  marginTop: "2px",
};

const smallBtnStyle = (bg: string): React.CSSProperties => ({
  padding: `${spacing.xs} ${spacing.sm}`,
  borderRadius: radii.sm,
  border: "none",
  background: bg,
  color: "#fff",
  cursor: "pointer",
  fontSize: fontSizes.sm,
  fontWeight: fontWeights.medium,
});

// ---------------------------------------------------------------------------
// Component
// ---------------------------------------------------------------------------

export default function WorkflowForm({ workflow, onSuccess, onCancel }: Props) {
  const isEdit = Boolean(workflow);

  const [name, setName] = useState(workflow?.name ?? "");
  const [description, setDescription] = useState(workflow?.description ?? "");
  const [tagsInput, setTagsInput] = useState(workflow?.tags.join(", ") ?? "");
  const [tasks, setTasks] = useState<TaskFormEntry[]>(
    workflow ? workflowToFormTasks(workflow) : [],
  );
  const [errors, setErrors] = useState<WorkflowFormErrors>({});
  const [submitting, setSubmitting] = useState(false);
  const [submitError, setSubmitError] = useState<string | null>(null);

  // --- tag helpers ---------------------------------------------------------

  const parseTags = (raw: string): string[] =>
    raw
      .split(",")
      .map((t) => t.trim())
      .filter(Boolean);

  // --- task list mutations --------------------------------------------------

  const addTask = () => setTasks([...tasks, emptyTask()]);

  const removeTask = (idx: number) =>
    setTasks(tasks.filter((_, i) => i !== idx));

  const moveTask = (idx: number, direction: -1 | 1) => {
    const target = idx + direction;
    if (target < 0 || target >= tasks.length) return;
    const copy = [...tasks];
    [copy[idx], copy[target]] = [copy[target], copy[idx]];
    setTasks(copy);
  };

  const updateTask = (idx: number, patch: Partial<TaskFormEntry>) =>
    setTasks(tasks.map((t, i) => (i === idx ? { ...t, ...patch } : t)));

  // --- parameter key-value helpers ------------------------------------------

  const addParam = (idx: number) => {
    const task = tasks[idx];
    const key = `param_${Object.keys(task.parameters).length + 1}`;
    updateTask(idx, { parameters: { ...task.parameters, [key]: "" } });
  };

  const removeParam = (taskIdx: number, key: string) => {
    const copy = { ...tasks[taskIdx].parameters };
    delete copy[key];
    updateTask(taskIdx, { parameters: copy });
  };

  const setParamKey = (taskIdx: number, oldKey: string, newKey: string) => {
    const params = tasks[taskIdx].parameters;
    const entries = Object.entries(params).map(([k, v]) =>
      k === oldKey ? [newKey, v] : [k, v],
    );
    updateTask(taskIdx, { parameters: Object.fromEntries(entries) });
  };

  const setParamValue = (taskIdx: number, key: string, value: string) => {
    updateTask(taskIdx, {
      parameters: { ...tasks[taskIdx].parameters, [key]: value },
    });
  };

  // --- depends_on helpers ---------------------------------------------------

  const toggleDep = (taskIdx: number, depName: string) => {
    const task = tasks[taskIdx];
    const deps = task.depends_on.includes(depName)
      ? task.depends_on.filter((d) => d !== depName)
      : [...task.depends_on, depName];
    updateTask(taskIdx, { depends_on: deps });
  };

  // --- submit ---------------------------------------------------------------

  const handleSubmit = async () => {
    setSubmitError(null);
    const formErrors = validateForm(name, description, tasks);
    setErrors(formErrors);
    if (!isValid(formErrors)) return;

    const tags = parseTags(tagsInput);
    const payload = {
      name: name.trim(),
      description,
      tags,
      tasks: tasks.map((t) => ({
        name: t.name.trim(),
        action: t.action,
        parameters: t.parameters,
        depends_on: t.depends_on,
        priority: t.priority,
        pre_hook: t.pre_hook || null,
        post_hook: t.post_hook || null,
      })),
    };

    setSubmitting(true);
    try {
      if (isEdit && workflow) {
        await updateWorkflow(workflow.id, payload);
      } else {
        await createWorkflow(payload);
      }
      onSuccess();
    } catch (err) {
      setSubmitError(
        err instanceof Error ? err.message : "Failed to save workflow",
      );
    } finally {
      setSubmitting(false);
    }
  };

  // --- render ---------------------------------------------------------------

  return (
    <div
      style={{
        background: colors.neutral[800],
        borderRadius: radii.xl,
        padding: spacing.xl,
      }}
    >
      <h3
        style={{
          fontSize: fontSizes.lg,
          color: colors.neutral[200],
          marginBottom: spacing.lg,
          fontWeight: fontWeights.semibold,
        }}
      >
        {isEdit ? "Edit Pipeline" : "New Pipeline"}
      </h3>

      {/* ---- Name ---- */}
      <div style={{ marginBottom: spacing.lg }}>
        <label style={labelStyle}>
          Name <span style={{ color: colors.error.main }}>*</span>
        </label>
        <input
          type="text"
          placeholder="Pipeline name"
          value={name}
          onChange={(e) => setName(e.target.value)}
          maxLength={MAX_NAME_LENGTH}
          aria-label="Workflow name"
          style={inputStyle}
        />
        {errors.name && <div style={errorTextStyle}>{errors.name}</div>}
      </div>

      {/* ---- Description ---- */}
      <div style={{ marginBottom: spacing.lg }}>
        <label style={labelStyle}>Description</label>
        <textarea
          placeholder="Optional description"
          value={description}
          onChange={(e) => setDescription(e.target.value)}
          rows={3}
          aria-label="Workflow description"
          style={{ ...inputStyle, resize: "vertical" }}
        />
        {errors.description && (
          <div style={errorTextStyle}>{errors.description}</div>
        )}
      </div>

      {/* ---- Tags ---- */}
      <div style={{ marginBottom: spacing.lg }}>
        <label style={labelStyle}>Tags (comma-separated)</label>
        <input
          type="text"
          placeholder="e.g. production, etl, daily"
          value={tagsInput}
          onChange={(e) => setTagsInput(e.target.value)}
          aria-label="Tags"
          style={inputStyle}
        />
        {/* Chip preview */}
        {parseTags(tagsInput).length > 0 && (
          <div
            style={{
              display: "flex",
              gap: spacing.xs,
              flexWrap: "wrap",
              marginTop: spacing.sm,
            }}
          >
            {parseTags(tagsInput).map((tag) => (
              <span
                key={tag}
                style={{
                  padding: `2px ${spacing.sm}`,
                  borderRadius: radii.sm,
                  background: colors.neutral[700],
                  color: colors.neutral[300],
                  fontSize: fontSizes.sm,
                }}
              >
                {tag}
              </span>
            ))}
          </div>
        )}
        {errors.tags && <div style={errorTextStyle}>{errors.tags}</div>}
      </div>

      {/* ---- Tasks ---- */}
      <div style={{ marginBottom: spacing.lg }}>
        <div
          style={{
            display: "flex",
            justifyContent: "space-between",
            alignItems: "center",
            marginBottom: spacing.sm,
          }}
        >
          <label style={{ ...labelStyle, marginBottom: 0 }}>Tasks</label>
          <button
            type="button"
            onClick={addTask}
            style={smallBtnStyle(colors.primary.main)}
          >
            + Add Task
          </button>
        </div>
        {errors.tasks && <div style={errorTextStyle}>{errors.tasks}</div>}

        {tasks.map((task, idx) => {
          const te = errors.taskErrors?.[idx];
          const otherNames = tasks
            .filter((_, i) => i !== idx)
            .map((t) => t.name.trim())
            .filter(Boolean);

          return (
            <div
              key={idx}
              data-testid={`task-entry-${idx}`}
              style={{
                background: colors.neutral[900],
                borderRadius: radii.lg,
                padding: spacing.lg,
                marginBottom: spacing.sm,
                borderLeft: `3px solid ${colors.primary.light}`,
              }}
            >
              {/* Task header with reorder / remove */}
              <div
                style={{
                  display: "flex",
                  justifyContent: "space-between",
                  alignItems: "center",
                  marginBottom: spacing.sm,
                }}
              >
                <span
                  style={{
                    fontSize: fontSizes.md,
                    color: colors.neutral[400],
                    fontWeight: fontWeights.medium,
                  }}
                >
                  Task {idx + 1}
                </span>
                <div style={{ display: "flex", gap: spacing.xs }}>
                  <button
                    type="button"
                    onClick={() => moveTask(idx, -1)}
                    disabled={idx === 0}
                    aria-label={`Move task ${idx + 1} up`}
                    style={smallBtnStyle(colors.neutral[700])}
                  >
                    &uarr;
                  </button>
                  <button
                    type="button"
                    onClick={() => moveTask(idx, 1)}
                    disabled={idx === tasks.length - 1}
                    aria-label={`Move task ${idx + 1} down`}
                    style={smallBtnStyle(colors.neutral[700])}
                  >
                    &darr;
                  </button>
                  <button
                    type="button"
                    onClick={() => removeTask(idx)}
                    aria-label={`Remove task ${idx + 1}`}
                    style={smallBtnStyle(colors.error.dark)}
                  >
                    Remove
                  </button>
                </div>
              </div>

              {/* Task name */}
              <div style={{ marginBottom: spacing.sm }}>
                <label style={labelStyle}>Task Name *</label>
                <input
                  type="text"
                  value={task.name}
                  onChange={(e) => updateTask(idx, { name: e.target.value })}
                  placeholder="Task name"
                  aria-label={`Task ${idx + 1} name`}
                  style={inputStyle}
                />
                {te?.name && <div style={errorTextStyle}>{te.name}</div>}
              </div>

              {/* Action + Priority row */}
              <div
                style={{
                  display: "flex",
                  gap: spacing.sm,
                  marginBottom: spacing.sm,
                }}
              >
                <div style={{ flex: 1 }}>
                  <label style={labelStyle}>Action *</label>
                  <select
                    value={task.action}
                    onChange={(e) =>
                      updateTask(idx, { action: e.target.value as ActionName })
                    }
                    aria-label={`Task ${idx + 1} action`}
                    style={inputStyle}
                  >
                    {ACTION_NAMES.map((a) => (
                      <option key={a} value={a}>
                        {a}
                      </option>
                    ))}
                  </select>
                  {te?.action && <div style={errorTextStyle}>{te.action}</div>}
                </div>
                <div style={{ flex: 1 }}>
                  <label style={labelStyle}>Priority</label>
                  <select
                    value={task.priority}
                    onChange={(e) =>
                      updateTask(idx, {
                        priority: e.target.value as TaskFormEntry["priority"],
                      })
                    }
                    aria-label={`Task ${idx + 1} priority`}
                    style={inputStyle}
                  >
                    {PRIORITY_OPTIONS.map((p) => (
                      <option key={p} value={p}>
                        {p}
                      </option>
                    ))}
                  </select>
                </div>
              </div>

              {/* Hooks row */}
              <div
                style={{
                  display: "flex",
                  gap: spacing.sm,
                  marginBottom: spacing.sm,
                }}
              >
                <div style={{ flex: 1 }}>
                  <label style={labelStyle}>Pre-hook</label>
                  <select
                    value={task.pre_hook}
                    onChange={(e) =>
                      updateTask(idx, { pre_hook: e.target.value })
                    }
                    aria-label={`Task ${idx + 1} pre-hook`}
                    style={inputStyle}
                  >
                    <option value="">None</option>
                    {ACTION_NAMES.map((a) => (
                      <option key={a} value={a}>
                        {a}
                      </option>
                    ))}
                  </select>
                </div>
                <div style={{ flex: 1 }}>
                  <label style={labelStyle}>Post-hook</label>
                  <select
                    value={task.post_hook}
                    onChange={(e) =>
                      updateTask(idx, { post_hook: e.target.value })
                    }
                    aria-label={`Task ${idx + 1} post-hook`}
                    style={inputStyle}
                  >
                    <option value="">None</option>
                    {ACTION_NAMES.map((a) => (
                      <option key={a} value={a}>
                        {a}
                      </option>
                    ))}
                  </select>
                </div>
              </div>

              {/* Parameters key-value editor */}
              <div style={{ marginBottom: spacing.sm }}>
                <div
                  style={{
                    display: "flex",
                    justifyContent: "space-between",
                    alignItems: "center",
                    marginBottom: spacing.xs,
                  }}
                >
                  <label style={{ ...labelStyle, marginBottom: 0 }}>
                    Parameters
                  </label>
                  <button
                    type="button"
                    onClick={() => addParam(idx)}
                    style={smallBtnStyle(colors.neutral[700])}
                  >
                    + Param
                  </button>
                </div>
                {Object.entries(task.parameters).map(([key, val]) => (
                  <div
                    key={key}
                    style={{
                      display: "flex",
                      gap: spacing.xs,
                      marginBottom: spacing.xs,
                    }}
                  >
                    <input
                      type="text"
                      value={key}
                      onChange={(e) => setParamKey(idx, key, e.target.value)}
                      placeholder="key"
                      aria-label={`Task ${idx + 1} param key`}
                      style={{ ...inputStyle, flex: 1 }}
                    />
                    <input
                      type="text"
                      value={val}
                      onChange={(e) => setParamValue(idx, key, e.target.value)}
                      placeholder="value"
                      aria-label={`Task ${idx + 1} param value`}
                      style={{ ...inputStyle, flex: 1 }}
                    />
                    <button
                      type="button"
                      onClick={() => removeParam(idx, key)}
                      aria-label={`Remove param ${key}`}
                      style={smallBtnStyle(colors.error.dark)}
                    >
                      x
                    </button>
                  </div>
                ))}
                {te?.parameters && (
                  <div style={errorTextStyle}>{te.parameters}</div>
                )}
              </div>

              {/* Depends-on multi-select */}
              {otherNames.length > 0 && (
                <div>
                  <label style={labelStyle}>Depends On</label>
                  <div
                    style={{
                      display: "flex",
                      gap: spacing.xs,
                      flexWrap: "wrap",
                    }}
                  >
                    {otherNames.map((depName) => {
                      const selected = task.depends_on.includes(depName);
                      return (
                        <button
                          key={depName}
                          type="button"
                          onClick={() => toggleDep(idx, depName)}
                          aria-label={`Toggle dependency ${depName}`}
                          style={{
                            padding: `2px ${spacing.sm}`,
                            borderRadius: radii.sm,
                            border: `1px solid ${selected ? colors.primary.main : colors.neutral[700]}`,
                            background: selected
                              ? colors.primary.dark
                              : "transparent",
                            color: selected
                              ? "#fff"
                              : colors.neutral[400],
                            cursor: "pointer",
                            fontSize: fontSizes.sm,
                          }}
                        >
                          {depName}
                        </button>
                      );
                    })}
                  </div>
                  {te?.depends_on && (
                    <div style={errorTextStyle}>{te.depends_on}</div>
                  )}
                </div>
              )}
            </div>
          );
        })}
      </div>

      {/* ---- Submit error ---- */}
      {submitError && (
        <div
          style={{
            ...errorTextStyle,
            marginBottom: spacing.md,
            padding: spacing.sm,
            background: colors.error.bg,
            borderRadius: radii.md,
          }}
        >
          {submitError}
        </div>
      )}

      {/* ---- Action buttons ---- */}
      <div style={{ display: "flex", gap: spacing.sm, justifyContent: "flex-end" }}>
        <button
          type="button"
          onClick={onCancel}
          style={{
            padding: `${spacing.sm} ${spacing.lg}`,
            borderRadius: radii.md,
            border: `1px solid ${colors.neutral[700]}`,
            background: "transparent",
            color: colors.neutral[400],
            cursor: "pointer",
            fontSize: fontSizes.base,
          }}
        >
          Cancel
        </button>
        <button
          type="button"
          onClick={handleSubmit}
          disabled={submitting}
          style={{
            padding: `${spacing.sm} ${spacing.xl}`,
            borderRadius: radii.md,
            border: "none",
            background: submitting ? colors.neutral[600] : colors.primary.main,
            color: "#fff",
            cursor: submitting ? "default" : "pointer",
            fontWeight: fontWeights.semibold,
            fontSize: fontSizes.base,
          }}
        >
          {submitting
            ? "Saving..."
            : isEdit
              ? "Update Pipeline"
              : "Create Pipeline"}
        </button>
      </div>
    </div>
  );
}
