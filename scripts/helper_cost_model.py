#!/usr/bin/env python3
"""Cost model for research-matrix: reading helpers vs running the job in one chat.

    python3 scripts/helper_cost_model.py

Cost model: helpers plan vs running the whole job in one session on one model.

All token counts are ASSUMPTIONS (printed below). Prices are Anthropic list
prices ($/MTok) from the claude-api skill's model table (cached 2026-11-03).
Cache-read prices for Sonnet/Opus/Fable are from that table; Haiku's cache-read
price and every cache-write price (1.25x input) are assumptions.
"""
import itertools
import sys

# model: (in, out, cache_read, cache_write)
PRICE = {
    "haiku":  (0.10, 0.50, 0.005, 0.125),
    "sonnet": (2.00, 10.00, 0.10, 2.50),
    "opus":   (4.00, 20.00, 0.20, 5.00),
    "fable":  (8.00, 40.00, 0.20, 10.00),
}
# Haiku 5.5 is $0.50/$2.50 for prompts over 100K tokens
HAIKU_BIG = (0.50, 2.50, 0.025, 0.625)


def rates(model, ctx):
    if model == "haiku" and ctx > 100_000:
        return HAIKU_BIG
    return PRICE[model]


class Conv:
    """One conversation: every turn re-reads the whole prior context from cache."""

    def __init__(self, model):
        self.model, self.ctx, self.cost = model, 0, 0.0

    def turn(self, new_in, out, keep_out=None):
        pin, pout, pread, pwrite = rates(self.model, self.ctx + new_in)
        self.cost += (self.ctx * pread + new_in * pwrite + out * pout) / 1e6
        self.ctx += new_in + (out if keep_out is None else keep_out)


# ---- assumptions (tokens) ----
A = dict(
    paper=12_000,       # full text of one paper (varied below)
    instr=6_600,        # skill files loaded in the session (measured: 26,313 chars / 4)
    read_out=3_000,     # output per paper incl. reasoning: quotes + cells
    read_keep=1_700,    # of which stays in context (quotes + cells JSON)
    tool_call=100,
    helper_overhead=5_000,   # a helper's system prompt + task prompt + rules
    batch=3,            # papers per reading helper
    verify_batch=10,    # papers per verifier helper
    verify_out=1_000,   # per paper: verdict + reasoning
    verify_keep=300,
    synth_out=2_300,    # synthesis paragraph + reasoning
    cells_per_paper=500,
    close_turns=8,      # check_evidence, build, look at the sheet... (same in both plans)
    status=200,         # a helper's short status returned to the session (it writes its files itself)
)


def in_session(model, n, a=A):
    """Whole job in one chat on `model`."""
    c = Conv(model)
    c.turn(a["instr"], 0)                       # skill instructions loaded
    for _ in range(n):
        c.turn(200, a["tool_call"])             # decide to read the file
        c.turn(a["paper"] + a["tool_call"], a["read_out"], a["read_keep"])
    for _ in range(-(-n // a["verify_batch"])):  # separate verification pass (same model)
        k = min(a["verify_batch"], n)
        c.turn(300, k * a["verify_out"], k * a["verify_keep"])
    c.turn(300, a["synth_out"], 800)            # synthesis
    for _ in range(a["close_turns"]):
        c.turn(500, 300)
    return c.cost


def helpers(n, session="sonnet", reader="sonnet", verifier="opus", synth="opus", a=A):
    """Reading on `reader` helpers (batches), checking and synthesis on Opus helpers."""
    s = Conv(session)
    s.turn(a["instr"], 0)
    total = 0.0
    done = 0
    while done < n:                              # reading helpers
        k = min(a["batch"], n - done)
        h = Conv(reader)
        h.turn(a["helper_overhead"], 0)
        for _ in range(k):
            h.turn(200, a["tool_call"])
            h.turn(a["paper"] + a["tool_call"], a["read_out"], a["read_keep"])
        h.turn(100, 300)                         # writes its file, reports
        total += h.cost
        s.turn(300, 250, 250)                    # session starts the helper
        s.turn(a["status"], 0)                   # ...and reads its status
        done += k
    done = 0
    while done < n:                              # verifier helpers
        k = min(a["verify_batch"], n - done)
        h = Conv(verifier)
        h.turn(a["helper_overhead"] + k * a["read_keep"], k * a["verify_out"])
        total += h.cost
        s.turn(300, 250, 250)
        s.turn(a["status"], 0)
        done += k
    h = Conv(synth)                              # synthesis helper
    h.turn(a["helper_overhead"] + n * a["cells_per_paper"], a["synth_out"])
    total += h.cost
    s.turn(300, 250, 250)
    s.turn(800, 0)
    for _ in range(a["close_turns"]):
        s.turn(500, 300)
    return total + s.cost


def breakeven(base_model, **kw):
    for n in range(1, 61):
        if helpers(n, **kw.get("h", {}), a=kw.get("a", A)) < in_session(base_model, n, a=kw.get("a", A)):
            return n
    return None


def table(a, label):
    print(f"\n### {label}: paper = {a['paper']:,} tokens")
    ns = [1, 2, 3, 4, 5, 6, 8, 10, 15, 20, 30]
    print(f"{'papers':>7} {'helpers':>9} | " + " ".join(f"{m+'-only':>11}" for m in PRICE))
    for n in ns:
        h = helpers(n, a=a)
        row = [in_session(m, n, a=a) for m in PRICE]
        print(f"{n:>7} {'$%.2f' % h:>9} | " + " ".join(f"{'$%.2f' % r:>11}" for r in row))
    be = {m: next((n for n in range(1, 61) if helpers(n, a=a) < in_session(m, n, a=a)), None) for m in PRICE}
    print("break-even (first N where helpers are cheaper):", {m: (v if v else ">60 (never)") for m, v in be.items()})
    return be


if __name__ == "__main__":
    print("Assumptions:", {k: v for k, v in A.items()})
    for p in (8_000, 12_000, 25_000):
        table({**A, "paper": p}, "size")
    # session on Opus orchestrating the helpers
    a = {**A}
    print("\n### helpers plan when the chat itself runs on Opus (12k-token papers)")
    for n in (3, 4, 5, 8, 10, 20):
        print(f"{n:>3} papers: helpers (Opus chat) ${helpers(n, session='opus', a=a):.2f} | opus-only ${in_session('opus', n, a=a):.2f}"
              f" | helpers (Sonnet chat) ${helpers(n, a=a):.2f}")


def hybrid(n, session, a=A):
    """No reading helpers: the chat (model `session`) reads every paper itself; the
    Opus verification and synthesis helpers are kept."""
    s = Conv(session)
    s.turn(a["instr"], 0)
    for _ in range(n):
        s.turn(200, a["tool_call"])
        s.turn(a["paper"] + a["tool_call"], a["read_out"], a["read_keep"])
    total = 0.0
    done = 0
    while done < n:
        k = min(a["verify_batch"], n - done)
        h = Conv("opus")
        h.turn(a["helper_overhead"] + k * a["read_keep"], k * a["verify_out"])
        total += h.cost
        s.turn(300, 250, 250)
        s.turn(a["status"], 0)
        done += k
    h = Conv("opus")
    h.turn(a["helper_overhead"] + n * a["cells_per_paper"], a["synth_out"])
    total += h.cost
    s.turn(300, 250, 250)
    s.turn(800, 0)
    for _ in range(a["close_turns"]):
        s.turn(500, 300)
    return total + s.cost


def reading_breakeven(session, a=A):
    """First paper count where reading helpers beat the chat reading itself."""
    return next((n for n in range(1, 61) if helpers(n, session=session, a=a) < hybrid(n, session, a)), None)


if __name__ == "__main__":
    print("\nReading helpers vs the chat reading itself (Opus checks in both): first N where helpers are cheaper")
    for sess in PRICE:
        row = {p: reading_breakeven(sess, {**A, "paper": p}) for p in (8_000, 12_000, 25_000)}
        print(f"  chat on {sess:>6}: " + ", ".join(f"{p // 1000}k-token papers: {v if v else 'never'}" for p, v in row.items()))
