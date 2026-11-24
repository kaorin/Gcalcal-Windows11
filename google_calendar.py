from __future__ import annotations
from datetime import datetime, date, time, timedelta, timezone
from pathlib import Path
from typing import Any

from config import APP_DIR, TOKEN_FILE

SCOPES = ["https://www.googleapis.com/auth/calendar"]


class GoogleCalendarService:
    """Google Calendar API wrapper. OAuth credentials are selected by the user."""
    def __init__(self, credentials_file: str = ""):
        self.credentials_file = credentials_file
        self.service = None

    def connect(self, force_login: bool = False):
        try:
            from google.oauth2.credentials import Credentials
            from google_auth_oauthlib.flow import InstalledAppFlow
            from google.auth.transport.requests import Request
            from googleapiclient.discovery import build
        except ImportError as exc:
            raise RuntimeError("Google API関連ライブラリがありません。requirements.txt の依存関係をインストールしてください。") from exc

        APP_DIR.mkdir(parents=True, exist_ok=True)
        creds = None
        if TOKEN_FILE.exists() and not force_login:
            creds = Credentials.from_authorized_user_file(str(TOKEN_FILE), SCOPES)
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        if not creds or not creds.valid:
            if not self.credentials_file or not Path(self.credentials_file).is_file():
                raise RuntimeError("Google Cloud Consoleで作成したOAuthクライアントJSONファイルを設定画面から指定してください。")
            flow = InstalledAppFlow.from_client_secrets_file(self.credentials_file, SCOPES)
            creds = flow.run_local_server(port=0, open_browser=True)
        TOKEN_FILE.write_text(creds.to_json(), encoding="utf-8")
        self.service = build("calendar", "v3", credentials=creds, cache_discovery=False)
        return self.service

    def ensure_connected(self):
        if self.service is None:
            self.connect()
        return self.service

    @staticmethod
    def _event_datetime(event: dict[str, Any], key: str) -> datetime:
        value = event.get(key, {})
        if "dateTime" in value:
            dt = datetime.fromisoformat(value["dateTime"].replace("Z", "+00:00"))
            return dt.astimezone().replace(tzinfo=None) if dt.tzinfo else dt
        d = date.fromisoformat(value["date"])
        return datetime.combine(d, time.min)

    def list_events(self, calendar_id: str, start: date, end: date) -> list[dict]:
        service = self.ensure_connected()
        # Google API's timeMax is exclusive. Include the day after the requested end.
        time_min = datetime.combine(start, time.min).astimezone().isoformat()
        time_max = datetime.combine(end + timedelta(days=1), time.min).astimezone().isoformat()
        items, token = [], None
        while True:
            response = service.events().list(
                calendarId=calendar_id or "primary", timeMin=time_min,
                timeMax=time_max, maxResults=2500, singleEvents=True,
                orderBy="startTime", pageToken=token
            ).execute()
            items.extend(response.get("items", []))
            token = response.get("nextPageToken")
            if not token:
                break
        for item in items:
            item["_start"] = self._event_datetime(item, "start")
            item["_end"] = self._event_datetime(item, "end")
            item["_calendar_id"] = calendar_id or "primary"
        return items

    def list_all_calendar_events(self, start: date, end: date) -> tuple[list[dict], list[dict], list[str]]:
        """Fetch events from every calendar visible in the user's Calendar List."""
        calendars = self.list_calendars()
        events: list[dict] = []
        errors: list[str] = []
        for cal in calendars:
            calendar_id = cal.get("id")
            if not calendar_id:
                continue
            try:
                calendar_events = self.list_events(calendar_id, start, end)
                for event in calendar_events:
                    event["_calendar_name"] = cal.get("summary", calendar_id)
                    event["_calendar_color"] = cal.get("backgroundColor", "")
                events.extend(calendar_events)
            except Exception as exc:
                errors.append(f'{cal.get("summary", calendar_id)}: {exc}')
        events.sort(key=lambda event: (event["_start"], event.get("summary", "").casefold()))
        return events, calendars, errors

    def create_event(self, calendar_id: str, title: str, start: datetime,
                     end: datetime, description: str = "", all_day: bool = False):
        service = self.ensure_connected()
        body = {"summary": title, "description": description}
        if all_day:
            body["start"] = {"date": start.date().isoformat()}
            body["end"] = {"date": (end.date() + timedelta(days=1)).isoformat()}
        else:
            body["start"] = {"dateTime": start.astimezone().isoformat()}
            body["end"] = {"dateTime": end.astimezone().isoformat()}
        return service.events().insert(calendarId=calendar_id or "primary", body=body).execute()

    def delete_event(self, calendar_id: str, event_id: str):
        return self.ensure_connected().events().delete(calendarId=calendar_id or "primary", eventId=event_id).execute()

    def list_calendars(self) -> list[dict]:
        service = self.ensure_connected()
        result, token = [], None
        while True:
            response = service.calendarList().list(pageToken=token).execute()
            result.extend(response.get("items", []))
            token = response.get("nextPageToken")
            if not token:
                break
        return result
