interface Props {
  message: string;
  onDismiss?: () => void;
  onRetry?: () => void;
}

export default function ErrorBanner({ message, onDismiss, onRetry }: Props) {
  return (
    <div
      role="alert"
      style={{
        padding: "12px 16px",
        background: "#7f1d1d",
        borderRadius: "8px",
        marginBottom: "16px",
        display: "flex",
        alignItems: "center",
        justifyContent: "space-between",
        gap: "12px",
      }}
    >
      <span style={{ color: "#fca5a5", fontSize: "14px", flex: 1 }}>
        {message}
      </span>
      <div style={{ display: "flex", gap: "8px" }}>
        {onRetry && (
          <button
            onClick={onRetry}
            style={{
              padding: "4px 12px",
              borderRadius: "4px",
              border: "1px solid #fca5a5",
              background: "transparent",
              color: "#fca5a5",
              cursor: "pointer",
              fontSize: "13px",
            }}
          >
            Retry
          </button>
        )}
        {onDismiss && (
          <button
            onClick={onDismiss}
            aria-label="Dismiss error"
            style={{
              padding: "4px 8px",
              borderRadius: "4px",
              border: "none",
              background: "transparent",
              color: "#fca5a5",
              cursor: "pointer",
              fontSize: "16px",
              lineHeight: 1,
            }}
          >
            ×
          </button>
        )}
      </div>
    </div>
  );
}
