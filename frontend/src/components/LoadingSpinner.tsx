interface Props {
  label?: string;
  size?: number;
}

export default function LoadingSpinner({ label, size = 32 }: Props) {
  return (
    <div
      role="status"
      style={{
        display: "flex",
        flexDirection: "column",
        alignItems: "center",
        gap: "12px",
        padding: "40px",
      }}
    >
      <div
        data-testid="spinner"
        style={{
          width: size,
          height: size,
          border: "3px solid #334155",
          borderTopColor: "#38bdf8",
          borderRadius: "50%",
          animation: "spin 0.8s linear infinite",
        }}
      />
      {label && (
        <span style={{ color: "#94a3b8", fontSize: "14px" }}>{label}</span>
      )}
      <style>{`@keyframes spin { to { transform: rotate(360deg); } }`}</style>
    </div>
  );
}
