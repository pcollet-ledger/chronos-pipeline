interface Props {
  message: string;
  actionLabel?: string;
  onAction?: () => void;
}

export default function EmptyState({ message, actionLabel, onAction }: Props) {
  return (
    <div
      style={{
        textAlign: "center",
        padding: "48px 24px",
        color: "#64748b",
      }}
    >
      <div
        style={{
          fontSize: "40px",
          marginBottom: "12px",
          opacity: 0.5,
        }}
        aria-hidden="true"
      >
        ○
      </div>
      <p style={{ fontSize: "14px", marginBottom: "16px" }}>{message}</p>
      {actionLabel && onAction && (
        <button
          onClick={onAction}
          style={{
            padding: "8px 20px",
            borderRadius: "6px",
            border: "1px solid #334155",
            background: "#1e293b",
            color: "#94a3b8",
            cursor: "pointer",
            fontSize: "13px",
          }}
        >
          {actionLabel}
        </button>
      )}
    </div>
  );
}
