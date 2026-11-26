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
# Calibrated on 8 measured claude -p reading runs (2026-11-26): cache writes cost
# 2x the input price (1-hour cache), and Haiku cache reads $0.01/M. With these the
# model reproduces the measured cost per paper (see calibration() below).
PRICE = {
    "haiku":  (0.10, 0.50, 0.01, 0.20),
    "sonnet": (2.00, 10.00, 0.10, 4.00),
    "opus":   (4.00, 20.00, 0.20, 8.00),
    "fable":  (8.00, 40.00, 0.20, 16.00),
}
# Haiku 5.5 is $0.50/$2.50 for prompts over 100K tokens
HAIKU_BIG = (0.50, 2.50, 0.05, 1.00)
# Output tokens (incl. reasoning) per paper while reading: measured Haiku 18,461, Sonnet 3,362
READ_OUT = {"haiku": 18_000, "sonnet": 3_400, "opus": 3_400, "fable": 3_400}


def rates(model, ctx):
    if model == "haiku" and ctx > 100_000:
        return HAIKU_BIG
    return PRICE[model]


class Conv:
    """One conversation: every turn re-reads the whole prior context from cache."""

    def __init__(self, model):
        self.model, self.ctx, self.cost = model, 0, 0.0

    def turn(self, new_in, out, keep_out=None, cached_new=0):
        """cached_new: part of new_in already in the cache (a shared system prompt),
        billed as a cache read instead of a cache write."""
        pin, pout, pread, pwrite = rates(self.model, self.ctx + new_in)
        self.cost += (self.ctx * pread + cached_new * pread + (new_in - cached_new) * pwrite + out * pout) / 1e6
        self.ctx += new_in + (out if keep_out is None else keep_out)


# ---- assumptions (tokens) ----
A = dict(
    paper=20_000,       # full text of one paper (measured: 18,282 to 22,189 tokens)
    instr=6_600,        # skill files loaded in the session (measured: 26,313 chars / 4)
    read_out=3_000,     # output per paper incl. reasoning: quotes + cells
    read_keep=1_700,    # of which stays in context (quotes + cells JSON)
    tool_call=100,
    helper_overhead=17_000,  # a helper's system prompt + tools + task prompt (measured: ~17K)
    shared_overhead=False,   # True: later helpers in a session reuse the cached system prompt
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
        c.turn(a["paper"] + a["tool_call"], READ_OUT[model], a["read_keep"])
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
        h.turn(a["helper_overhead"], 0, cached_new=a["helper_overhead"] if a["shared_overhead"] else 0)
        for _ in range(k):
            h.turn(200, a["tool_call"])
            h.turn(a["paper"] + a["tool_call"], READ_OUT[reader], a["read_keep"])
        h.turn(100, 300)                         # writes its file, reports
        total += h.cost
        s.turn(300, 250, 250)                    # session starts the helper
        s.turn(a["status"], 0)                   # ...and reads its status
        done += k
    done = 0
    while done < n:                              # verifier helpers
        k = min(a["verify_batch"], n - done)
        h = Conv(verifier)
        h.turn(a["helper_overhead"] + k * a["read_keep"], k * a["verify_out"],
               cached_new=a["helper_overhead"] if a["shared_overhead"] else 0)
        total += h.cost
        s.turn(300, 250, 250)
        s.turn(a["status"], 0)
        done += k
    h = Conv(synth)                              # synthesis helper
    h.turn(a["helper_overhead"] + n * a["cells_per_paper"], a["synth_out"],
           cached_new=a["helper_overhead"] if a["shared_overhead"] else 0)
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


def hybrid(n, session, a=A):
    """No reading helpers: the chat (model `session`) reads every paper itself; the
    Opus verification and synthesis helpers are kept."""
    s = Conv(session)
    s.turn(a["instr"], 0)
    for _ in range(n):
        s.turn(200, a["tool_call"])
        s.turn(a["paper"] + a["tool_call"], READ_OUT[session], a["read_keep"])
    total = 0.0
    done = 0
    while done < n:
        k = min(a["verify_batch"], n - done)
        h = Conv("opus")
        h.turn(a["helper_overhead"] + k * a["read_keep"], k * a["verify_out"],
               cached_new=a["helper_overhead"] if a["shared_overhead"] else 0)
        total += h.cost
        s.turn(300, 250, 250)
        s.turn(a["status"], 0)
        done += k
    h = Conv("opus")
    h.turn(a["helper_overhead"] + n * a["cells_per_paper"], a["synth_out"],
           cached_new=a["helper_overhead"] if a["shared_overhead"] else 0)
    total += h.cost
    s.turn(300, 250, 250)
    s.turn(800, 0)
    for _ in range(a["close_turns"]):
        s.turn(500, 300)
    return total + s.cost


def reading_breakeven(session, a=A):
    """First paper count where reading helpers beat the chat reading itself."""
    return next((n for n in range(1, 61) if helpers(n, session=session, a=a) < hybrid(n, session, a)), None)


def calibration():
    """One reader helper, one paper, compared with the measured claude -p runs."""
    a = A
    print("Calibration: predicted vs measured cost of ONE paper read by ONE helper (8 real runs)")
    for m, measured in (("haiku", 0.0182), ("sonnet", 0.1956)):
        h = Conv(m)
        h.turn(a["helper_overhead"], 0)
        h.turn(200, a["tool_call"])
        h.turn(a["paper"] + a["tool_call"], READ_OUT[m], a["read_keep"])
        h.turn(100, 300)
        print(f"  {m:>6}: predicted ${h.cost:.4f}  measured ${measured:.4f}  ({h.cost / measured - 1:+.0%})")


def reading_breakeven(session, reader, a=A):
    """First paper count where reading helpers on `reader` beat the chat (on `session`) reading itself."""
    return next((n for n in range(1, 61)
                 if helpers(n, session=session, reader=reader, a=a) < hybrid(n, session, a)), None)


def main():
    print("Parameters:", {k: v for k, v in A.items()})
    calibration()
    for shared in (False, True):
        a = {**A, "shared_overhead": shared}
        label = ("helper overhead billed in full (measured claude -p, pessimistic)" if not shared
                 else "helper overhead shared via the cache (later helpers in one session)")
        print(f"\n=== {label}; 20,000-token papers; Opus checks and synthesises in every plan")
        print(f"{'papers':>6} | {'chat reads, Sonnet chat':>23} | {'chat reads, Opus chat':>21} | {'Sonnet helpers':>14} | {'Haiku helpers':>13}")
        for n in (1, 2, 3, 4, 5, 8, 10, 20):
            print(f"{n:>6} | {hybrid(n, 'sonnet', a):>22.2f}$ | {hybrid(n, 'opus', a):>20.2f}$ |"
                  f" {helpers(n, session='sonnet', reader='sonnet', a=a):>13.2f}$ | {helpers(n, session='sonnet', reader='haiku', a=a):>12.2f}$")
        print("  first paper count where helpers beat the chat reading itself:")
        for sess in ("sonnet", "opus", "fable"):
            print(f"    chat on {sess:>6}: Sonnet helpers from {reading_breakeven(sess, 'sonnet', a)}, "
                  f"Haiku helpers from {reading_breakeven(sess, 'haiku', a)}")


if __name__ == "__main__":
    main()
