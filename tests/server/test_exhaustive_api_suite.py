"""Pytest Integration Test executing the complete 60-Endpoint Verification Suite.

Guarantees that 100% of F.R.I.D.A.Y. REST API endpoints remain fully functional,
meeting aerospace and defense-grade standards.
"""

import pytest
from tools.test_all_endpoints import ApiBenchmarkRunner


@pytest.mark.asyncio
async def test_all_60_rest_endpoints_pass():
    """Verify all 60 REST endpoints return expected status codes and response schemas."""
    runner = ApiBenchmarkRunner()
    all_passed = await runner.run_all_tests()
    
    # Assert every single endpoint passed
    failures = [r for r in runner.results if not r["passed"]]
    assert len(failures) == 0, f"{len(failures)} endpoints failed: {[(f['method'], f['path'], f['status_code']) for f in failures]}"
    assert all_passed is True
