#!/usr/bin/env python3
"""test_check_redo_species_clip on CUDA; exits 125 (skipped) without a GPU."""
import sys

import test_check_redo_species_clip

if __name__ == "__main__":
    sys.exit(test_check_redo_species_clip.main(["--device", "cuda"]))
