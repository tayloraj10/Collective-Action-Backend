"""Fetch 'Interesting People' rows from Google Sheets and upsert DirectoryOfGood.

Expected sheet layout (typical 16-column tab):

- **A** Name, **B** Focus, **C** Instagram (handle)
- **D** Instagram follower count (ignored — often unlabeled)
- **E** TikTok (handle), **F** TikTok follower count (ignored)
- **G** YouTube (handle or channel id), **H** YouTube subscriber count (ignored)
- **I** Total (ignored)
- **J** Website, **K** Category, **L** Image
- **M** City, **N** State, **O** Zip Code, **P** Country

Columns are matched by **header row text** (case-insensitive), not position. Count columns are
never stored; handles are cleaned so numeric follower strings are not saved as social handles.
"""

from __future__ import annotations

import os
import re
from dataclasses import dataclass
from typing import Any

from google.auth import default as google_auth_default
from google.auth.exceptions import DefaultCredentialsError
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models.action import Action
from app.models.category import Category
from app.models.directory_of_good import DirectoryOfGood
from app.schemas.action_types import ActionTypeValuesEnum

SCOPES = ("https://www.googleapis.com/auth/spreadsheets.readonly",)


def _load_sheets_credentials(credentials_path: str | None):
    """Use a service account JSON file if path is set and exists; else ADC.

    On Cloud Run / GCE, ADC uses the runtime service account (no key file needed).
    """
    path = (credentials_path or "").strip()
    if path:
        if not os.path.isfile(path):
            raise FileNotFoundError(f"GOOGLE_APPLICATION_CREDENTIALS path does not exist: {path}")
        return service_account.Credentials.from_service_account_file(path, scopes=SCOPES)
    creds, _ = google_auth_default(scopes=SCOPES)
    return creds


@dataclass
class SheetSyncResult:
    created: int
    updated: int
    skipped: int
    rows_seen: int
    errors: list[str]


def _normalize_header(cell: str) -> str:
    return cell.strip().lower().replace("_", " ")


def _header_to_key(header: str) -> str | None:
    h = _normalize_header(header)
    aliases = {
        "name": "name",
        "focus": "focus",
        "instagram": "instagram",
        "instagram followers": None,
        "ig followers": None,
        "tiktok": "tiktok",
        "tiktok followers": None,
        "youtube": "youtube",
        "youtube subscribers": None,
        "total": None,
        "website": "website",
        "category": "category",
        "image": "image",
        "city": "city",
        "state": "state",
        "zip": "zip",
        "zip code": "zip",
        "country": "country",
    }
    return aliases.get(h)


def _follower_count_display(value: str) -> bool:
    s = value.strip()
    if not s:
        return False
    return bool(re.match(r"^[\d.,]+[KkMm]?$", s.replace(" ", "")))


def _clean_handle(value: str | None) -> str | None:
    if not value or not str(value).strip():
        return None
    s = str(value).strip().lstrip("@")
    if _follower_count_display(s):
        return None
    if len(s) > 200:
        return None
    return s


def _build_social_links(row: dict[str, str]) -> dict[str, str]:
    out: dict[str, str] = {}
    ig = _clean_handle(row.get("instagram"))
    if ig:
        out["instagram"] = ig
    tt = _clean_handle(row.get("tiktok"))
    if tt:
        out["tiktok"] = tt
    yt = _clean_handle(row.get("youtube"))
    if yt:
        out["youtube"] = yt
    web = row.get("website")
    if web and str(web).strip():
        out["website"] = str(web).strip()
    return out


def _build_location(row: dict[str, str]) -> dict[str, str] | None:
    city = (row.get("city") or "").strip() or None
    state = (row.get("state") or "").strip() or None
    country = (row.get("country") or "").strip() or None
    zip_code = (row.get("zip") or "").strip() or None
    loc: dict[str, str] = {}
    if city:
        loc["city"] = city
    if state:
        loc["state"] = state
    if country:
        loc["country"] = country
    if zip_code:
        loc["zip_code"] = zip_code
    return loc or None


def _resolve_category_id(db: Session, category_cell: str | None) -> str | None:
    if not category_cell or not category_cell.strip():
        return None
    parts = [p.strip() for p in category_cell.split("|") if p.strip()]
    if not parts:
        return None
    categories = {c.name.lower(): c.id for c in db.query(Category).all()}
    for part in parts:
        cid = categories.get(part.lower())
        if cid:
            return str(cid)
    return None


def _parse_header_row(values: list[list[Any]]) -> tuple[dict[int, str], int] | tuple[None, int]:
    if not values:
        return None, 0
    for i, row in enumerate(values):
        col_map: dict[int, str] = {}
        for j, cell in enumerate(row):
            if cell is None:
                continue
            key = _header_to_key(str(cell))
            if key:
                col_map[j] = key
        if "name" in col_map.values():
            return col_map, i
    return None, 0


def _row_to_dict(
    col_map: dict[int, str], row: list[Any], errors: list[str], row_num: int
) -> dict[str, str] | None:
    out: dict[str, str] = {}
    for j, key in col_map.items():
        if j < len(row) and row[j] is not None:
            out[key] = str(row[j]).strip()
        else:
            out[key] = ""
    name = out.get("name", "").strip()
    if not name:
        errors.append(f"Row {row_num}: empty name, skipped")
        return None
    return out


def _find_existing(db: Session, name: str, instagram: str | None) -> DirectoryOfGood | None:
    if instagram:
        ig_lower = instagram.lower()
        q = (
            db.query(DirectoryOfGood)
            .filter(DirectoryOfGood.social_links.isnot(None))
            .filter(func.lower(DirectoryOfGood.social_links["instagram"].as_string()) == ig_lower)
        )
        hit = q.first()
        if hit:
            return hit

    name_lower = name.strip().lower()
    return (
        db.query(DirectoryOfGood)
        .filter(func.lower(DirectoryOfGood.name) == name_lower)
        .order_by(DirectoryOfGood.created_at.asc())
        .first()
    )


def fetch_sheet_values(
    spreadsheet_id: str,
    sheet_gid: int,
    credentials_path: str | None,
) -> list[list[Any]]:
    creds = _load_sheets_credentials(credentials_path)
    service = build("sheets", "v4", credentials=creds, cache_discovery=False)
    meta = service.spreadsheets().get(spreadsheetId=spreadsheet_id).execute()
    sheets = meta.get("sheets", [])
    title: str | None = None
    for s in sheets:
        props = s.get("properties", {})
        if props.get("sheetId") == sheet_gid:
            title = props.get("title")
            break
    if not title:
        raise ValueError(f"No sheet with gid={sheet_gid} in spreadsheet {spreadsheet_id}")

    safe_title = title.replace("'", "''")
    range_a1 = f"'{safe_title}'"
    result = (
        service.spreadsheets().values().get(spreadsheetId=spreadsheet_id, range=range_a1).execute()
    )
    return result.get("values", []) or []


def sync_interesting_people(  # noqa: C901
    db: Session,
    spreadsheet_id: str,
    sheet_gid: int,
    credentials_path: str | None,
) -> SheetSyncResult:
    errors: list[str] = []
    try:
        values = fetch_sheet_values(spreadsheet_id, sheet_gid, credentials_path)
    except HttpError as e:
        return SheetSyncResult(0, 0, 0, 0, [f"Google Sheets API error: {e!s}"])
    except DefaultCredentialsError as e:
        msg = f"No Google credentials (set GOOGLE_APPLICATION_CREDENTIALS or use ADC): {e!s}"
        return SheetSyncResult(0, 0, 0, 0, [msg])
    except OSError as e:
        return SheetSyncResult(0, 0, 0, 0, [f"Credentials or IO error: {e!s}"])
    except ValueError as e:
        return SheetSyncResult(0, 0, 0, 0, [str(e)])

    col_map, header_idx = _parse_header_row(values)
    if not col_map:
        return SheetSyncResult(0, 0, 0, 0, ["Could not find a header row with a Name column"])

    created = updated = skipped = 0
    rows_seen = 0
    data_rows = values[header_idx + 1 :]

    for offset, row in enumerate(data_rows):
        row_num = header_idx + 2 + offset
        parsed = _row_to_dict(col_map, row, errors, row_num)
        if not parsed:
            continue
        rows_seen += 1
        name = parsed["name"]
        social = _build_social_links(parsed)
        instagram = social.get("instagram")
        location = _build_location(parsed)
        category_id = _resolve_category_id(db, parsed.get("category"))
        image_url = (parsed.get("image") or "").strip() or None
        focus = (parsed.get("focus") or "").strip() or None

        entry = _find_existing(db, name, instagram)
        if entry and entry.user_id is not None:
            skipped += 1
            continue

        if entry is None:
            entry = DirectoryOfGood(
                name=name[:255],
                focus=focus,
                category_id=category_id,
                image_url=image_url,
                location=location,
                social_links=social or None,
            )
            db.add(entry)
            db.flush()
            db.add(
                Action(
                    action_type=ActionTypeValuesEnum.directory_of_good.value,
                    linked_id=entry.id,
                )
            )
            created += 1
        else:
            entry.name = name[:255]
            entry.focus = focus
            entry.category_id = category_id
            entry.image_url = image_url
            entry.location = location
            entry.social_links = social or None
            updated += 1

    try:
        db.commit()
    except Exception as e:
        db.rollback()
        return SheetSyncResult(0, 0, 0, rows_seen, [f"Database error: {e!s}"])

    return SheetSyncResult(
        created=created,
        updated=updated,
        skipped=skipped,
        rows_seen=rows_seen,
        errors=errors,
    )
