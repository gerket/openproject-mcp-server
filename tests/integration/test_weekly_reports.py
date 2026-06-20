"""Integration tests: weekly report generation.

These tools are client-side computation over get_work_packages — no dedicated
endpoint. The integration test verifies the full pipeline runs against a real
instance without raising.
"""

import datetime

import pytest

from src.tools.weekly_reports import (
    GenerateWeeklyReportInput,
    GetReportDataInput,
    generate_weekly_report,
    get_report_data,
)

pytestmark = pytest.mark.integration


async def test_get_report_data(project_id: int) -> None:
    today = datetime.date.today()
    week_start = (today - datetime.timedelta(days=today.weekday())).isoformat()
    week_end = today.isoformat()

    result = await get_report_data(
        GetReportDataInput(
            project_id=project_id,
            from_date=week_start,
            to_date=week_end,
        )
    )
    assert isinstance(result, str)
    assert len(result) > 0


async def test_generate_weekly_report(project_id: int) -> None:
    today = datetime.date.today()
    week_start = (today - datetime.timedelta(days=today.weekday())).isoformat()
    week_end = today.isoformat()

    result = await generate_weekly_report(
        GenerateWeeklyReportInput(
            project_id=project_id,
            from_date=week_start,
            to_date=week_end,
        )
    )
    assert isinstance(result, str)
    assert len(result) > 0
