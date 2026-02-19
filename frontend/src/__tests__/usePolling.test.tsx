import { describe, it, expect, vi, beforeEach, afterEach } from "vitest";
import { render, screen, act } from "@testing-library/react";
import { usePolling } from "../hooks/usePolling";

function TestComponent({
  fetcher,
  intervalMs,
  enabled,
  onError,
}: {
  fetcher: () => Promise<string>;
  intervalMs: number;
  enabled?: boolean;
  onError?: (err: Error) => void;
}) {
  const { data, loading, error, refresh } = usePolling({
    fetcher,
    intervalMs,
    enabled,
    onError,
  });
  return (
    <div>
      <span data-testid="data">{data ?? "null"}</span>
      <span data-testid="loading">{String(loading)}</span>
      <span data-testid="error">{error?.message ?? "null"}</span>
      <button data-testid="refresh" onClick={() => void refresh()}>
        Refresh
      </button>
    </div>
  );
}

describe("usePolling", () => {
  beforeEach(() => {
    vi.useFakeTimers();
  });

  afterEach(() => {
    vi.useRealTimers();
  });

  it("fetches data on mount", async () => {
    const fetcher = vi.fn().mockResolvedValue("hello");
    render(<TestComponent fetcher={fetcher} intervalMs={5000} />);
    await act(async () => {
      await vi.advanceTimersByTimeAsync(100);
    });
    expect(screen.getByTestId("data").textContent).toBe("hello");
  });

  it("calls fetcher immediately", async () => {
    const fetcher = vi.fn().mockResolvedValue("data");
    render(<TestComponent fetcher={fetcher} intervalMs={5000} />);
    await act(async () => {
      await vi.advanceTimersByTimeAsync(100);
    });
    expect(fetcher).toHaveBeenCalled();
  });

  it("sets loading to true during fetch", async () => {
    let resolve: (v: string) => void;
    const fetcher = vi.fn().mockImplementation(
      () => new Promise<string>((r) => { resolve = r; }),
    );
    render(<TestComponent fetcher={fetcher} intervalMs={5000} />);
    await act(async () => {});
    expect(screen.getByTestId("loading").textContent).toBe("true");
    await act(async () => {
      resolve!("done");
    });
  });

  it("sets error on fetch failure", async () => {
    const fetcher = vi.fn().mockRejectedValue(new Error("network error"));
    render(<TestComponent fetcher={fetcher} intervalMs={5000} />);
    await act(async () => {
      await vi.advanceTimersByTimeAsync(100);
    });
    expect(screen.getByTestId("error").textContent).toBe("network error");
  });

  it("calls onError callback on failure", async () => {
    const onError = vi.fn();
    const fetcher = vi.fn().mockRejectedValue(new Error("fail"));
    render(<TestComponent fetcher={fetcher} intervalMs={5000} onError={onError} />);
    await act(async () => {
      await vi.advanceTimersByTimeAsync(100);
    });
    expect(onError).toHaveBeenCalled();
  });

  it("does not fetch when disabled", async () => {
    const fetcher = vi.fn().mockResolvedValue("data");
    render(<TestComponent fetcher={fetcher} intervalMs={5000} enabled={false} />);
    await act(async () => {
      await vi.advanceTimersByTimeAsync(6000);
    });
    expect(fetcher).not.toHaveBeenCalled();
  });

  it("polls at the specified interval", async () => {
    const fetcher = vi.fn().mockResolvedValue("data");
    render(<TestComponent fetcher={fetcher} intervalMs={1000} />);
    await act(async () => {
      await vi.advanceTimersByTimeAsync(3500);
    });
    expect(fetcher.mock.calls.length).toBeGreaterThanOrEqual(3);
  });

  it("returns null data initially", () => {
    const fetcher = vi.fn().mockImplementation(() => new Promise(() => {}));
    render(<TestComponent fetcher={fetcher} intervalMs={5000} />);
    expect(screen.getByTestId("data").textContent).toBe("null");
  });

  it("returns null error initially", () => {
    const fetcher = vi.fn().mockImplementation(() => new Promise(() => {}));
    render(<TestComponent fetcher={fetcher} intervalMs={5000} />);
    expect(screen.getByTestId("error").textContent).toBe("null");
  });

  it("handles non-Error rejection", async () => {
    const fetcher = vi.fn().mockRejectedValue("string error");
    render(<TestComponent fetcher={fetcher} intervalMs={5000} />);
    await act(async () => {
      await vi.advanceTimersByTimeAsync(100);
    });
    expect(screen.getByTestId("error").textContent).toBe("string error");
  });

  it("clears interval on unmount", async () => {
    const fetcher = vi.fn().mockResolvedValue("data");
    const { unmount } = render(<TestComponent fetcher={fetcher} intervalMs={1000} />);
    await act(async () => {
      await vi.advanceTimersByTimeAsync(1500);
    });
    const callsBefore = fetcher.mock.calls.length;
    unmount();
    await act(async () => {
      await vi.advanceTimersByTimeAsync(5000);
    });
    expect(fetcher.mock.calls.length).toBe(callsBefore);
  });
});
