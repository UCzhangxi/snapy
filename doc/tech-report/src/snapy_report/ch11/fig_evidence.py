"""Executed formulas versus pending runtime evidence."""
from .diagrams import flow

def make_fig():
    return flow(["report identities: symbolic / rational checks", "committed check output: formula evidence", "source solver assertions: pinned decks and thresholds", "CPU / CUDA / ranks: runtime results still required"])
