# tools/sheets_tool.py
# Rewrites the sheet on every run based on aggregated data.
# Only repos with actual hours appear. Zero-hour repos are excluded.

import gspread
from google.oauth2.service_account import Credentials
import os
from dotenv import load_dotenv

load_dotenv()

SHEET_ID   = os.getenv("GOOGLE_SHEET_ID")
CREDS_PATH = os.getenv("GOOGLE_CREDS_PATH", "./credentials.json")
WORKSHEET  = "BD-Rawdata"


def get_worksheet():
    creds = Credentials.from_service_account_file(
        CREDS_PATH,
        scopes=[
            "https://www.googleapis.com/auth/spreadsheets",
            "https://www.googleapis.com/auth/drive",
        ]
    )
    client = gspread.authorize(creds)
    sheet  = client.open_by_key(SHEET_ID)
    try:
        ws = sheet.worksheet(WORKSHEET)
    except gspread.exceptions.WorksheetNotFound:
        ws = sheet.add_worksheet(title=WORKSHEET, rows=100, cols=50)
    return ws


def col_letter(index: int) -> str:
    result = ""
    while index >= 0:
        result = chr(index % 26 + 65) + result
        index  = index // 26 - 1
    return result


def write_sheet(ws, aggregated: dict):
    """
    Clears and rewrites the entire sheet on every run.
    Only repos with non-zero hours are included.
    Engineers with zero hours in a repo are excluded from that repo's row.
    """
    ws.clear()

    # Only include repos that have at least one engineer with hours
    active_repos = {
        repo: eng_data
        for repo, eng_data in aggregated.items()
        if any(
            v["planned"] > 0 or v["actual"] > 0
            for v in eng_data.values()
        )
    }

    if not active_repos:
        print("  No activity found — sheet cleared, nothing written")
        return

    repos     = sorted(active_repos.keys())
    engineers = sorted({
        eng
        for repo_data in active_repos.values()
        for eng, hours in repo_data.items()
        if hours["planned"] > 0 or hours["actual"] > 0
    })

    n_repos = len(repos)
    n_engs  = len(engineers)

    # ── Row 1 — Main headers ───────────────────────────────────
    row1 = ["S.No", "Customer Name", "", "BurnDown Hrs", ""]
    for eng in engineers:
        row1.append(eng)
        row1.append("")

    ws.update("A1", [row1], value_input_option="USER_ENTERED")

    # ── Row 2 — Sub headers ───────────────────────────────────
    row2 = ["", "", "Target", "Planned", "Actual"]
    for _ in engineers:
        row2.append("Planned")
        row2.append("Actual")

    ws.update("A2", [row2], value_input_option="USER_ENTERED")

    # ── Rows 3+ — One row per active repo ─────────────────────
    data_rows = []
    for i, repo in enumerate(repos):
        row       = [i + 1, repo, ""]
        repo_data = active_repos.get(repo, {})

        total_planned = sum(v["planned"] for v in repo_data.values())
        total_actual  = sum(v["actual"]  for v in repo_data.values())
        row.append(round(total_planned, 2))
        row.append(round(total_actual,  2))

        for eng in engineers:
            eng_data = repo_data.get(eng, {"planned": 0.0, "actual": 0.0})
            row.append(round(eng_data["planned"], 2))
            row.append(round(eng_data["actual"],  2))

        data_rows.append(row)

    start_row = 3
    end_row   = start_row + n_repos - 1

    ws.update(f"A{start_row}", data_rows, value_input_option="USER_ENTERED")

    # ── Overall row (SUM formulas) ─────────────────────────────
    overall_row_num = end_row + 1
    overall_row     = ["", "Overall", ""]
    total_cols      = 5 + (n_engs * 2)

    for col_idx in range(3, total_cols):
        col = col_letter(col_idx)
        overall_row.append(f"=SUM({col}{start_row}:{col}{end_row})")

    ws.update(
        f"A{overall_row_num}", [overall_row],
        value_input_option="USER_ENTERED"
    )

    # ── Section 2 headers ─────────────────────────────────────
    section2_start = overall_row_num + 3

    ws.update(
        f"A{section2_start}",
        [["S.No", "Resource Name", "", "BurnDown Hrs", ""]],
        value_input_option="USER_ENTERED"
    )
    ws.update(
        f"A{section2_start + 1}",
        [["", "", "Available", "Planned", "Actual"]],
        value_input_option="USER_ENTERED"
    )

    # ── One row per engineer ───────────────────────────────────
    eng_actual_cols = {}
    for idx, eng in enumerate(engineers):
        actual_col_idx       = 5 + (idx * 2) + 1
        eng_actual_cols[eng] = col_letter(actual_col_idx)

    eng_rows = []
    for i, eng in enumerate(engineers):
        actual_col = eng_actual_cols[eng]
        eng_rows.append([
            i + 1,
            eng,
            "=8*20",
            "",
            f"={actual_col}{overall_row_num}"
        ])

    eng_start_row = section2_start + 2
    ws.update(
        f"A{eng_start_row}", eng_rows,
        value_input_option="USER_ENTERED"
    )

    # ── Resource Overall row ───────────────────────────────────
    resource_overall_row = eng_start_row + n_engs
    ws.update(
        f"A{resource_overall_row}",
        [[
            "",
            "Overall",
            f"=SUM(C{eng_start_row}:C{resource_overall_row - 1})",
            f"=SUM(D{eng_start_row}:D{resource_overall_row - 1})",
            f"=SUM(E{eng_start_row}:E{resource_overall_row - 1})",
        ]],
        value_input_option="USER_ENTERED"
    )

    # ── Bold headers ───────────────────────────────────────────
    ws.format("A1:Z1", {"textFormat": {"bold": True}})
    ws.format("A2:Z2", {"textFormat": {"bold": True}})
    ws.format(
        f"A{section2_start}:Z{section2_start}",
        {"textFormat": {"bold": True}}
    )
    ws.format(
        f"A{section2_start + 1}:Z{section2_start + 1}",
        {"textFormat": {"bold": True}}
    )

    print(f"  Sheet written: {n_repos} active repos, {n_engs} active engineers")
    print(f"  Section 1: rows 1–{overall_row_num}")
    print(f"  Section 2: rows {section2_start}–{resource_overall_row}")


def run(aggregated: dict):
    print("  Connecting to Google Sheets...")
    ws = get_worksheet()
    print("  Rewriting sheet from current month activity...")
    write_sheet(ws, aggregated)