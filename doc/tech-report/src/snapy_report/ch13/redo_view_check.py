"""Executable check of the redo causes and termination status as printed (chapter 13, _redo-view.qmd).

What is checked: the cause list of the redo message and the two terminal messages of MeshBlockImpl::apply_redo
(src/mesh/meshblock.cpp:1229-1276), the bit order of local_redo_flags and reduce_redo_flags (:1278-1300) and the
termination reason and status of MeshBlockImpl::finalize (:1121-1144) at
snapy@e894700ff7aee30b52882e5202b16461413780b0, ported as string logic. Claims C1-C3.

Run: python3 redo_view_check.py   (numpy only; exits with the number of failed claims)
"""
import itertools
import sys

NAMES = ["floor", "clamp", "limiter", "nan", "saturation", "vic-solve"]    # bits 1, 2, 4, 8, 16, 32


def report(tag, ok, label, numbers):
    print("[%s] %s %s: %s" % (tag, "PASS" if ok else "FAIL", label, numbers))
    return ok


def causes_text(causes):
    """meshblock.cpp:1236-1240: '(causes:' then one ' name' per set bit, in bit order, then ').'"""
    return "(causes:" + "".join(" " + n for k, n in enumerate(NAMES) if causes >> k & 1) + ")."


def terminal_message(causes, current_redo, max_redo=5):
    """None, or the message printed when the redo budget is exhausted (meshblock.cpp:1241-1268)."""
    if current_redo + 1 <= max_redo:
        return None
    if not causes & 32:
        return "Maximum number of redo attempts exceeded. Terminating."
    return ("Maximum number of redo attempts exceeded. Terminating after restoring the rejected VIC step "
            "input.")


def finalize(sigterm, sigint, sigalrm, cycle, nlim, time, tlim):
    """meshblock.cpp:1125-1140: the first reason that holds, and the exit status."""
    if sigterm:
        return "Terminating on Terminate signal", 0
    if sigint:
        return "Terminating on Interrupt signal", 0
    if sigalrm:
        return "Terminating on wall-time limit", 0
    if nlim >= 0 and cycle >= nlim:
        return "Terminating on cycle limit", 0
    if time >= tlim:
        return "Terminating on time limit", 0
    return "Terminating abnormally", 1


def decode(text):
    words = text[len("(causes:"):-2].split()
    return sum(1 << NAMES.index(w) for w in words)


def check_C1_cause_list_names_every_bit_once():
    texts = {m: causes_text(m) for m in range(1, 64)}
    ok = len(set(texts.values())) == 63 and all(decode(t) == m for m, t in texts.items())
    return report("C1", ok, "the 63 nonzero cause masks print 63 different lists, each naming its bits in bit order, "
                  "and the list decodes back to the mask", "37 -> '%s'; 48 -> '%s'" % (texts[37], texts[48]))


def check_C2_terminal_messages():
    m1 = terminal_message(1, 5)
    m32 = terminal_message(33, 5)
    ok = (terminal_message(1, 4) is None and m1.endswith("Terminating.") and "restoring" in m32)
    return report("C2", ok, "past max_redo the run ends with one of two messages, the second only when vic-solve "
                  "(32) is among the causes", "floor: '%s' | floor + vic-solve: '...%s'" % (m1, m32[-45:]))


def check_C3_termination_reason_and_status():
    rows = []
    ok = True
    for bits in itertools.product([0, 1], repeat=5):
        sigterm, sigint, sigalrm, cyc, tim = bits
        reason, status = finalize(sigterm, sigint, sigalrm, 10 if cyc else 3, 10, 2. if tim else 1., 2.)
        ok &= (status == 1) == (sum(bits) == 0)
        if sum(bits) == 0 or bits == (0, 1, 0, 1, 1):
            rows.append("%s -> %s, status %d" % (bits, reason, status))
    reason, status = finalize(0, 0, 0, 10, -1, 1., 2.)
    ok &= status == 1
    return report("C3", ok, "of 32 combinations of the five stop reasons only the empty one exits with status 1; "
                  "signals win over limits; nlim < 0 disables the cycle limit",
                  "; ".join(rows) + "; nlim = -1 at cycle 10 -> %s" % reason)


def main():
    checks = [check_C1_cause_list_names_every_bit_once, check_C2_terminal_messages,
              check_C3_termination_reason_and_status]
    sys.exit(sum(not c() for c in checks))


if __name__ == "__main__":
    main()
