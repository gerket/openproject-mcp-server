"""Report formatting utilities for weekly reports."""

from datetime import datetime
from typing import Any


def calculate_metrics(work_packages: list[dict], time_entries: list[dict]) -> dict:
    """Calculate key metrics from work packages and time entries.

    Args:
        work_packages: List of work package dictionaries
        time_entries: List of time entry dictionaries

    Returns:
        Dictionary with calculated metrics
    """
    metrics = {
        "total_wps": len(work_packages),
        "done_count": 0,
        "in_progress_count": 0,
        "planned_count": 0,
        "blocked_count": 0,
        "bug_count": 0,
        "feature_count": 0,
        "total_hours": 0.0,
        "dev_hours": 0.0,
        "qa_hours": 0.0,
        "management_hours": 0.0,
    }

    # Count work packages by status and type
    for wp in work_packages:
        # Status analysis - try _embedded first, fallback to _links.status.title
        status_obj = wp.get("_embedded", {}).get("status", {})
        status_name = status_obj.get("name", "").lower()

        # Fallback: if no status in _embedded, try _links
        if not status_name or status_name == "unknown":
            status_link = wp.get("_links", {}).get("status", {})
            status_name = status_link.get("title", "").lower()

        # Handle empty status by treating as planned
        if not status_name or status_name == "unknown":
            metrics["planned_count"] += 1
        elif (
            "closed" in status_name
            or "done" in status_name
            or "resolved" in status_name
            or "completed" in status_name
            or "finished" in status_name
        ):
            metrics["done_count"] += 1
        elif (
            "progress" in status_name
            or "development" in status_name
            or "implementing" in status_name
        ):
            metrics["in_progress_count"] += 1
        elif "blocked" in status_name:
            metrics["blocked_count"] += 1
        elif (
            "new" in status_name
            or "open" in status_name
            or "specified" in status_name
            or "to do" in status_name
        ):
            metrics["planned_count"] += 1
        else:
            # Default unknown statuses to planned
            metrics["planned_count"] += 1

        # Type analysis
        wp_type = wp.get("_embedded", {}).get("type", {}).get("name", "").lower()
        if "bug" in wp_type or "defect" in wp_type:
            metrics["bug_count"] += 1
        elif "feature" in wp_type or "story" in wp_type or "task" in wp_type:
            metrics["feature_count"] += 1

    # Calculate hours by activity
    for te in time_entries:
        hours = float(te.get("hours", 0))
        metrics["total_hours"] += hours

        activity = te.get("_embedded", {}).get("activity", {}).get("name", "").lower()
        if "development" in activity or "implement" in activity:
            metrics["dev_hours"] += hours
        elif "test" in activity or "qa" in activity:
            metrics["qa_hours"] += hours
        elif "management" in activity or "meeting" in activity:
            metrics["management_hours"] += hours

    return metrics


def group_by_status(work_packages: list[dict]) -> dict[str, list[dict]]:
    """Group work packages by status category.

    Args:
        work_packages: List of work package dictionaries

    Returns:
        Dictionary with keys: done, in_progress, planned, blocked, other
    """
    groups: dict[str, list[Any]] = {
        "done": [],
        "in_progress": [],
        "planned": [],
        "blocked": [],
        "de_scoped": [],
        "other": [],
    }

    for wp in work_packages:
        # Try _embedded first, fallback to _links.status.title
        status_obj = wp.get("_embedded", {}).get("status", {})
        status_name = status_obj.get("name", "").lower()

        # Fallback: if no status in _embedded, try _links
        if not status_name or status_name == "unknown":
            status_link = wp.get("_links", {}).get("status", {})
            status_name = status_link.get("title", "").lower()

        # If status still empty or Unknown, default to 'planned'
        if not status_name or status_name == "unknown":
            # For work packages without clear status, default to 'planned'
            # This is safer than categorizing as 'other' which won't show in main sections
            groups["planned"].append(wp)
            continue

        if (
            "closed" in status_name
            or "done" in status_name
            or "resolved" in status_name
            or "completed" in status_name
            or "finished" in status_name
        ):
            groups["done"].append(wp)
        elif (
            "progress" in status_name
            or "development" in status_name
            or "implementing" in status_name
        ):
            groups["in_progress"].append(wp)
        elif "blocked" in status_name:
            groups["blocked"].append(wp)
        elif "rejected" in status_name or "cancelled" in status_name:
            groups["de_scoped"].append(wp)
        elif (
            "new" in status_name
            or "open" in status_name
            or "specified" in status_name
            or "to do" in status_name
        ):
            groups["planned"].append(wp)
        else:
            # Unknown status types default to 'planned' to ensure visibility
            groups["planned"].append(wp)

    return groups


def detect_blockers(
    work_packages: list[dict], relations: list[dict] | None = None
) -> list[dict]:
    """Detect blocked work packages and their blockers.

    Args:
        work_packages: List of work package dictionaries
        relations: Optional list of relation dictionaries

    Returns:
        List of blocked work packages with blocker information
    """
    blockers = []

    for wp in work_packages:
        status_name = wp.get("_embedded", {}).get("status", {}).get("name", "").lower()
        if "blocked" in status_name:
            blockers.append(
                {
                    "id": wp.get("id"),
                    "subject": wp.get("subject"),
                    "assignee": wp.get("_embedded", {})
                    .get("assignee", {})
                    .get("name", "Unassigned"),
                    "status": wp.get("_embedded", {}).get("status", {}).get("name"),
                    "reason": "Status marked as blocked",
                }
            )

    return blockers


def format_work_package_row(wp: dict) -> str:
    """Format a single work package as a markdown table row.

    Args:
        wp: Work package dictionary

    Returns:
        Markdown table row string
    """
    wp_id = wp.get("id", "N/A")
    subject = wp.get("subject", "No subject")[:50]  # Truncate long subjects

    # Get assignee
    assignee = wp.get("_embedded", {}).get("assignee", {})
    assignee_name = assignee.get("name", "Unassigned") if assignee else "Unassigned"

    # Get dates
    due_date = wp.get("dueDate", "N/A")
    updated_at = wp.get("updatedAt", "")
    if updated_at:
        try:
            updated_dt = datetime.fromisoformat(updated_at.replace("Z", "+00:00"))
            updated_date = updated_dt.strftime("%Y-%m-%d")
        except Exception:
            updated_date = "N/A"
    else:
        updated_date = "N/A"

    # Get status and type
    status = wp.get("_embedded", {}).get("status", {}).get("name", "Unknown")
    wp_type = wp.get("_embedded", {}).get("type", {}).get("name", "Task")

    return f"| [{wp_type} #{wp_id}] | {subject} | {assignee_name} | {due_date or updated_date} | {status} |"


def format_weekly_report_markdown(
    project: dict,
    work_packages: list[dict],
    time_entries: list[dict],
    members: list[dict],
    from_date: str,
    to_date: str,
    sprint_goal: str | None = None,
    team_name: str | None = None,
    relations: list[dict] | None = None,
) -> str:
    """Format complete weekly report in markdown.

    Args:
        project: Project dictionary
        work_packages: List of work package dictionaries
        time_entries: List of time entry dictionaries
        members: List of project member dictionaries
        from_date: Report start date (YYYY-MM-DD)
        to_date: Report end date (YYYY-MM-DD)
        sprint_goal: Optional sprint goal text
        team_name: Optional team/squad name
        relations: Optional list of work package relations

    Returns:
        Formatted markdown report
    """
    # Calculate metrics
    metrics = calculate_metrics(work_packages, time_entries)
    grouped_wps = group_by_status(work_packages)
    blockers = detect_blockers(work_packages, relations)

    # Build report
    report = []

    # Header
    report.append("# BÁO CÁO TUẦN - AGILE SCRUM\n")
    report.append("*Tự động tạo từ OpenProject*\n")

    # A. THÔNG TIN CHUNG
    report.append("## A. THÔNG TIN CHUNG\n")
    report.append("| Tuần báo cáo | Giá trị |")
    report.append("|--------------|---------|")
    report.append(f"| Từ ngày - Đến ngày | {from_date} - {to_date} |")
    report.append(f"| Team/Squad | {team_name or 'N/A'} |")
    report.append(f"| Product/Module | {project.get('name', 'N/A')} |")
    report.append(f"| Project ID | #{project.get('id', 'N/A')} |")
    report.append(f"| Sprint Goal | {sprint_goal or 'N/A'} |")
    report.append("")

    # B. TÓM TẮT ĐIỀU HÀNH
    report.append("## B. TÓM TẮT ĐIỀU HÀNH\n")

    # Status indicator
    if metrics["blocked_count"] > 0:
        status = "🔴 Off track"
    elif metrics["done_count"] < metrics["in_progress_count"]:
        status = "🟡 At risk"
    else:
        status = "🟢 On track"

    report.append(f"**Tiến độ so với Sprint Goal:** {status}\n")

    # Top deliverables
    report.append("**Deliverables nổi bật (đã Done):**")
    done_wps = grouped_wps["done"][:3]
    if done_wps:
        for i, wp in enumerate(done_wps, 1):
            report.append(f"{i}. #{wp.get('id')} - {wp.get('subject', 'N/A')}")
    else:
        report.append("- Chưa có work package nào hoàn thành")
    report.append("")

    # Blockers summary
    if blockers:
        report.append(
            f"**Vướng mắc lớn nhất:** {len(blockers)} work package đang bị blocked\n"
        )
    else:
        report.append("**Vướng mắc lớn nhất:** Không có\n")

    report.append("**Cần hỗ trợ/quyết định:** _(Cần cập nhật thủ công)_\n")

    # C. DELIVERY & BACKLOG MOVEMENT
    report.append("## C. DELIVERY & BACKLOG MOVEMENT\n")

    # Done
    report.append("### 1) Công việc đã hoàn thành (Done)\n")
    if grouped_wps["done"]:
        report.append("| Ticket/Story | Mô tả ngắn | Owner | Ngày Done | Status |")
        report.append("|--------------|------------|-------|-----------|--------|")
        for wp in grouped_wps["done"]:
            report.append(format_work_package_row(wp))
    else:
        report.append("_Không có work package nào hoàn thành trong tuần._")
    report.append("")

    # In Progress
    report.append("### 2) Công việc đang thực hiện (In Progress)\n")
    if grouped_wps["in_progress"]:
        report.append("| Ticket/Story | Mô tả ngắn | Owner | ETA | Status |")
        report.append("|--------------|------------|-------|-----|--------|")
        for wp in grouped_wps["in_progress"]:
            report.append(format_work_package_row(wp))
    else:
        report.append("_Không có work package đang in progress._")
    report.append("")

    # Planned/Not Started
    report.append("### 3) Công việc đề ra nhưng chưa bắt đầu (Planned)\n")
    if grouped_wps["planned"]:
        report.append("| Ticket/Story | Mô tả ngắn | Owner | ETA | Status |")
        report.append("|--------------|------------|-------|-----|--------|")
        for wp in grouped_wps["planned"]:
            report.append(format_work_package_row(wp))
    else:
        report.append("_Không có work package planned._")
    report.append("")

    # De-scoped
    if grouped_wps["de_scoped"]:
        report.append("### 4) Công việc bị dừng/đổi ưu tiên (De-scoped)\n")
        report.append("| Ticket | Lý do | Status |")
        report.append("|--------|-------|--------|")
        for wp in grouped_wps["de_scoped"]:
            wp_id = wp.get("id", "N/A")
            subject = wp.get("subject", "No subject")[:40]
            status = wp.get("_embedded", {}).get("status", {}).get("name", "Unknown")
            report.append(f"| #{wp_id} {subject} | _(Cần cập nhật)_ | {status} |")
        report.append("")

    # D. NGUỒN LỰC & NĂNG LỰC
    report.append("## D. NGUỒN LỰC & NĂNG LỰC THỰC THI\n")
    report.append(f"**Quy mô team:** {len(members)} người\n")
    report.append(f"**Capacity tuần:** {metrics['total_hours']:.1f} person-hours\n")
    report.append("**Biến động nhân sự:** _(Cần cập nhật thủ công)_\n")

    # Time distribution
    if metrics["total_hours"] > 0:
        report.append("**Phân bổ theo loại việc:**\n")
        report.append("| Loại | Hours | % |")
        report.append("|------|-------|---|")
        report.append(
            f"| Development | {metrics['dev_hours']:.1f} | {metrics['dev_hours'] / metrics['total_hours'] * 100:.1f}% |"
        )
        report.append(
            f"| QA/Testing | {metrics['qa_hours']:.1f} | {metrics['qa_hours'] / metrics['total_hours'] * 100:.1f}% |"
        )
        report.append(
            f"| Management | {metrics['management_hours']:.1f} | {metrics['management_hours'] / metrics['total_hours'] * 100:.1f}% |"
        )
        report.append("")

    # E. TRỞ NGẠI & PHỤ THUỘC
    report.append("## E. TRỞ NGẠI (IMPEDIMENTS) & PHỤ THUỘC\n")

    if blockers:
        report.append("### Impediments (cản trở trực tiếp)\n")
        report.append("| Mô tả | Mức độ | Owner xử lý | Status |")
        report.append("|-------|--------|-------------|--------|")
        for blocker in blockers:
            report.append(
                f"| #{blocker['id']} {blocker['subject'][:40]} | H | {blocker['assignee']} | {blocker['status']} |"
            )
        report.append("")
    else:
        report.append("_Không có impediments._\n")

    # F. CHẤT LƯỢNG & ỔN ĐỊNH
    report.append("## F. CHẤT LƯỢNG & ỔN ĐỊNH HỆ THỐNG\n")
    report.append(f"**Bug phát sinh tuần:** {metrics['bug_count']}\n")
    report.append("**Bug đóng tuần:** _(Cần phân tích thêm)_\n")
    report.append("**Test coverage:** _(Cần cập nhật thủ công)_\n")
    report.append("**Incident/Outage:** _(Cần cập nhật thủ công)_\n")

    # G. KẾ HOẠCH TUẦN TỚI
    report.append("## G. KẾ HOẠCH TUẦN TỚI\n")
    report.append("**Top ưu tiên:**")

    # Show planned work as next week priorities
    next_week_wps = grouped_wps["planned"][:5]
    if next_week_wps:
        for i, wp in enumerate(next_week_wps, 1):
            assignee = (
                wp.get("_embedded", {}).get("assignee", {}).get("name", "Unassigned")
            )
            due_date = wp.get("dueDate", "TBD")
            report.append(
                f"{i}. #{wp.get('id')} {wp.get('subject', 'N/A')} ({assignee} - ETA: {due_date})"
            )
    else:
        report.append("_(Cần lập kế hoạch)_")
    report.append("")

    # H. SPRINT HEALTH & CẢI TIẾN
    report.append("## H. SPRINT HEALTH & CẢI TIẾN\n")
    report.append("**Điều làm tốt:** _(Cần cập nhật từ retro)_\n")
    report.append("**Điều cần cải thiện:** _(Cần cập nhật từ retro)_\n")
    report.append("**Action items:** _(Cần cập nhật từ retro)_\n")

    # PHỤ LỤC: BẢN SIÊU GỌN
    report.append("---\n")
    report.append("## PHỤ LỤC: BẢN SIÊU GỌN CHO LÃNH ĐẠO\n")
    report.append(f"**Status:** {status}")
    report.append(f"**Done:** {metrics['done_count']} work packages")
    report.append(f"**In progress:** {metrics['in_progress_count']} work packages")
    report.append(f"**Planned:** {metrics['planned_count']} work packages")
    report.append(f"**Main blockers:** {len(blockers)} blocked items")
    report.append(f"**Hours logged:** {metrics['total_hours']:.1f}h")

    return "\n".join(report)


def format_report_data_json(
    project: dict,
    work_packages: list[dict],
    time_entries: list[dict],
    members: list[dict],
    relations: list[dict] | None = None,
) -> dict[str, Any]:
    """Format report data as structured JSON for custom processing.

    Args:
        project: Project dictionary
        work_packages: List of work package dictionaries
        time_entries: List of time entry dictionaries
        members: List of project member dictionaries
        relations: Optional list of work package relations

    Returns:
        Structured dictionary with all report data
    """
    metrics = calculate_metrics(work_packages, time_entries)
    grouped_wps = group_by_status(work_packages)
    blockers = detect_blockers(work_packages, relations)

    return {
        "project": {
            "id": project.get("id"),
            "name": project.get("name"),
            "description": project.get("description", {}).get("raw", ""),
        },
        "metrics": metrics,
        "work_packages": {
            "done": grouped_wps["done"],
            "in_progress": grouped_wps["in_progress"],
            "planned": grouped_wps["planned"],
            "blocked": grouped_wps["blocked"],
            "de_scoped": grouped_wps["de_scoped"],
        },
        "time_entries": time_entries,
        "members": members,
        "blockers": blockers,
        "relations": relations or [],
    }
