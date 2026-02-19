import { describe, it, expect, vi } from "vitest";
import { render, screen, act } from "@testing-library/react";
import { useAsync } from "../hooks/useAsync";

function TestComponent({ asyncFn }: { asyncFn: (...args: unknown[]) => Promise<string> }) {
  const { data, loading, error, execute, reset } = useAsync(asyncFn);
  return (
    <div>
      <span data-testid="data">{data ?? "null"}</span>
      <span data-testid="loading">{String(loading)}</span>
      <span data-testid="error">{error?.message ?? "null"}</span>
      <button data-testid="execute" onClick={() => void execute("arg1")}>Execute</button>
      <button data-testid="reset" onClick={reset}>Reset</button>
    </div>
  );
}

describe("useAsync", () => {
  it("starts with null data", () => {
    render(<TestComponent asyncFn={vi.fn().mockResolvedValue("ok")} />);
    expect(screen.getByTestId("data").textContent).toBe("null");
  });

  it("starts with loading false", () => {
    render(<TestComponent asyncFn={vi.fn().mockResolvedValue("ok")} />);
    expect(screen.getByTestId("loading").textContent).toBe("false");
  });

  it("starts with null error", () => {
    render(<TestComponent asyncFn={vi.fn().mockResolvedValue("ok")} />);
    expect(screen.getByTestId("error").textContent).toBe("null");
  });

  it("sets data after execute", async () => {
    const fn = vi.fn().mockResolvedValue("result");
    render(<TestComponent asyncFn={fn} />);
    await act(async () => {
      screen.getByTestId("execute").click();
    });
    expect(screen.getByTestId("data").textContent).toBe("result");
  });

  it("calls the async function with arguments", async () => {
    const fn = vi.fn().mockResolvedValue("ok");
    render(<TestComponent asyncFn={fn} />);
    await act(async () => {
      screen.getByTestId("execute").click();
    });
    expect(fn).toHaveBeenCalledWith("arg1");
  });

  it("sets error on rejection", async () => {
    const fn = vi.fn().mockRejectedValue(new Error("failed"));
    render(<TestComponent asyncFn={fn} />);
    await act(async () => {
      screen.getByTestId("execute").click();
    });
    expect(screen.getByTestId("error").textContent).toBe("failed");
  });

  it("sets loading to false after success", async () => {
    const fn = vi.fn().mockResolvedValue("ok");
    render(<TestComponent asyncFn={fn} />);
    await act(async () => {
      screen.getByTestId("execute").click();
    });
    expect(screen.getByTestId("loading").textContent).toBe("false");
  });

  it("sets loading to false after error", async () => {
    const fn = vi.fn().mockRejectedValue(new Error("err"));
    render(<TestComponent asyncFn={fn} />);
    await act(async () => {
      screen.getByTestId("execute").click();
    });
    expect(screen.getByTestId("loading").textContent).toBe("false");
  });

  it("resets state on reset", async () => {
    const fn = vi.fn().mockResolvedValue("data");
    render(<TestComponent asyncFn={fn} />);
    await act(async () => {
      screen.getByTestId("execute").click();
    });
    expect(screen.getByTestId("data").textContent).toBe("data");
    await act(async () => {
      screen.getByTestId("reset").click();
    });
    expect(screen.getByTestId("data").textContent).toBe("null");
    expect(screen.getByTestId("error").textContent).toBe("null");
    expect(screen.getByTestId("loading").textContent).toBe("false");
  });

  it("handles non-Error rejection", async () => {
    const fn = vi.fn().mockRejectedValue("string error");
    render(<TestComponent asyncFn={fn} />);
    await act(async () => {
      screen.getByTestId("execute").click();
    });
    expect(screen.getByTestId("error").textContent).toBe("string error");
  });

  it("clears previous error on new execute", async () => {
    const fn = vi.fn()
      .mockRejectedValueOnce(new Error("first"))
      .mockResolvedValueOnce("ok");
    render(<TestComponent asyncFn={fn} />);
    await act(async () => {
      screen.getByTestId("execute").click();
    });
    expect(screen.getByTestId("error").textContent).toBe("first");
    await act(async () => {
      screen.getByTestId("execute").click();
    });
    expect(screen.getByTestId("error").textContent).toBe("null");
    expect(screen.getByTestId("data").textContent).toBe("ok");
  });

  it("can be executed multiple times", async () => {
    const fn = vi.fn()
      .mockResolvedValueOnce("first")
      .mockResolvedValueOnce("second");
    render(<TestComponent asyncFn={fn} />);
    await act(async () => {
      screen.getByTestId("execute").click();
    });
    expect(screen.getByTestId("data").textContent).toBe("first");
    await act(async () => {
      screen.getByTestId("execute").click();
    });
    expect(screen.getByTestId("data").textContent).toBe("second");
  });
});
