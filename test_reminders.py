"""Unit tests for reminder tools."""

from unittest.mock import AsyncMock, MagicMock, patch


def _mock_client(responses: dict) -> MagicMock:
    client = MagicMock()
    for method, response in responses.items():
        setattr(client, method, AsyncMock(return_value=response))
    return client


async def test_list_reminders_empty():
    mock = _mock_client({"get_reminders": {"_embedded": {"elements": []}}})
    with patch("src.tools.reminders.get_client", return_value=mock):
        from src.tools.reminders import list_reminders

        result = await list_reminders.fn(work_package_id=42)
        assert "no reminders" in result.lower()


async def test_list_reminders_results():
    reminders = [
        {
            "id": 3,
            "remindAt": "2026-06-25T09:00:00Z",
            "note": "Review this",
            "completed": False,
        }
    ]
    mock = _mock_client({"get_reminders": {"_embedded": {"elements": reminders}}})
    with patch("src.tools.reminders.get_client", return_value=mock):
        from src.tools.reminders import list_reminders

        result = await list_reminders.fn(work_package_id=42)
        assert "Review this" in result
        assert "2026-06-25" in result


async def test_create_reminder():
    created = {"id": 3, "remindAt": "2026-06-25T09:00:00Z", "note": "Don't forget"}
    mock = _mock_client({"create_reminder": created})
    with patch("src.tools.reminders.get_client", return_value=mock):
        from src.tools.reminders import create_reminder

        result = await create_reminder.fn(
            work_package_id=42,
            remind_at="2026-06-25T09:00:00Z",
            note="Don't forget",
        )
        assert "3" in result or "created" in result.lower()
        mock.create_reminder.assert_called_once_with(
            42, "2026-06-25T09:00:00Z", note="Don't forget"
        )


async def test_create_reminder_no_note():
    created = {"id": 4, "remindAt": "2026-06-26T09:00:00Z"}
    mock = _mock_client({"create_reminder": created})
    with patch("src.tools.reminders.get_client", return_value=mock):
        from src.tools.reminders import create_reminder

        result = await create_reminder.fn(
            work_package_id=42,
            remind_at="2026-06-26T09:00:00Z",
        )
        mock.create_reminder.assert_called_once_with(
            42, "2026-06-26T09:00:00Z", note=None
        )
        assert "4" in result or "created" in result.lower()
