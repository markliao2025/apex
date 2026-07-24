import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";

import { ReplanModal } from "./ReplanModal";

const api = vi.hoisted(() => ({
  replan: vi.fn(),
}));

vi.mock("../../lib/api", () => ({
  planningApi: api,
}));

describe("ReplanModal", () => {
  it("sends one nullable satellite id with the selected horizon and priority", async () => {
    api.replan.mockResolvedValue({ tasks: [] });
    const queryClient = new QueryClient({
      defaultOptions: {
        mutations: { retry: false },
        queries: { retry: false },
      },
    });

    render(
      <QueryClientProvider client={queryClient}>
        <ReplanModal
          requestId="request-1"
          isOpen
          onClose={vi.fn()}
          currentTasks={[]}
          satellites={[{ id: "satellite-1", name: "Synthetic One" }]}
        />
      </QueryClientProvider>,
    );

    fireEvent.click(
      screen.getByRole("button", { name: /^urgent emergency/i }),
    );
    fireEvent.click(screen.getByRole("button", { name: /24 hours/i }));
    fireEvent.click(screen.getByRole("radio", { name: /synthetic one/i }));
    fireEvent.click(screen.getByRole("button", { name: /re-plan now/i }));

    await waitFor(() =>
      expect(api.replan).toHaveBeenCalledWith("request-1", {
        priority_override: "urgent",
        satellite_id: "satellite-1",
        time_horizon_hours: 24,
      }),
    );
    expect(api.replan).toHaveBeenCalledOnce();
    expect(await screen.findByText("Schedule Changes")).toBeInTheDocument();
  });
});
