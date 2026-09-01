"""
Tests for the Phase 15 demo script.

Ensures the demo actually runs end to end without error and produces
the expected sections — this is what caught the risk_category bug
that no other test suite happened to exercise.
"""

from __future__ import annotations

import io
from contextlib import redirect_stdout


class TestDemoRuns:
    def test_demo_main_runs_without_exception(self) -> None:
        from examples.demo import main

        buffer = io.StringIO()
        with redirect_stdout(buffer):
            main()
        output = buffer.getvalue()
        assert "FINAL RECOMMENDATION" in output
        assert "EXPLANATION" in output

    def test_demo_output_labels_mock_data(self) -> None:
        from examples.demo import main

        buffer = io.StringIO()
        with redirect_stdout(buffer):
            main()
        output = buffer.getvalue()
        assert "MOCK" in output.upper()

    def test_demo_shows_all_pipeline_stages(self) -> None:
        from examples.demo import main

        buffer = io.StringIO()
        with redirect_stdout(buffer):
            main()
        output = buffer.getvalue()
        for marker in [
            "PHASE 1 REJECTED",
            "PHASE 1+2 FEASIBLE",
            "COST / RISK / RANKING",
            "DECISION ALTERNATIVES",
            "FINAL RECOMMENDATION",
            "EXPLANATION",
        ]:
            assert marker in output, f"Missing section: {marker}"

    def test_demo_never_shows_none_risk_category(self) -> None:
        """Regression test for the bug this demo run originally caught:
        risk_category being hardcoded to None and crashing str formatting."""
        from examples.demo import main

        buffer = io.StringIO()
        with redirect_stdout(buffer):
            main()
        output = buffer.getvalue()
        assert "(None)" not in output
        assert "Risk score:" in output
