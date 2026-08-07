from datetime import date, datetime, timedelta, timezone
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from fastapi import FastAPI, HTTPException, Query

app = FastAPI(title="Time API", description="Простой тестовый бэкенд")


@app.get("/")
def root():
    return {"message": "Time API is running"}


@app.get("/time")
def get_server_time():
    now = datetime.now(timezone.utc)
    return {
        "utc": now.isoformat(),
        "unix": now.timestamp(),
        "timezone": "UTC",
    }


@app.get("/date")
def get_server_date():
    today = datetime.now(timezone.utc).date()
    return {
        "date": today.isoformat(),
        "year": today.year,
        "month": today.month,
        "day": today.day,
        "weekday": today.strftime("%A"),
        "timezone": "UTC",
    }


@app.get("/week")
def get_week_info(
    date_value: str | None = Query(
        default=None,
        alias="date",
        description="Дата в формате YYYY-MM-DD. Если не указана — сегодня (по tz).",
        examples=["2026-08-07"],
    ),
    tz: str = Query(
        default="UTC",
        description="Часовой пояс (IANA) для определения «сегодня», если date не передан",
    ),
):
    try:
        zone = ZoneInfo(tz)
    except ZoneInfoNotFoundError as exc:
        raise HTTPException(
            status_code=400,
            detail=f"Unknown timezone: {exc}",
        ) from exc

    if date_value is None:
        target_date = datetime.now(timezone.utc).astimezone(zone).date()
    else:
        try:
            target_date = date.fromisoformat(date_value)
        except ValueError as exc:
            raise HTTPException(
                status_code=400,
                detail="Invalid date format. Use YYYY-MM-DD, e.g. 2026-08-07",
            ) from exc

    iso_year, week_number, weekday_number = target_date.isocalendar()
    week_start = target_date - timedelta(days=target_date.weekday())
    week_end = week_start + timedelta(days=6)

    return {
        "date": target_date.isoformat(),
        "timezone": tz,
        "iso_year": iso_year,
        "week_number": week_number,
        "weekday": target_date.strftime("%A"),
        "weekday_number": weekday_number,
        "week_start": week_start.isoformat(),
        "week_end": week_end.isoformat(),
    }


@app.get("/convert")
def convert_timezone(
    time: str | None = Query(
        default=None,
        description="Время в ISO 8601. Если не указано — текущее UTC.",
        examples=["2026-08-06T12:00:00"],
    ),
    from_tz: str = Query(
        default="UTC",
        alias="from",
        description="Исходный часовой пояс (IANA), например UTC или Europe/Moscow",
    ),
    to_tz: str = Query(
        ...,
        alias="to",
        description="Целевой часовой пояс (IANA), например Asia/Bangkok",
    ),
):
    try:
        source_zone = ZoneInfo(from_tz)
        target_zone = ZoneInfo(to_tz)
    except ZoneInfoNotFoundError as exc:
        raise HTTPException(
            status_code=400,
            detail=f"Unknown timezone: {exc}",
        ) from exc

    if time is None:
        source_dt = datetime.now(timezone.utc).astimezone(source_zone)
    else:
        try:
            parsed = datetime.fromisoformat(time)
        except ValueError as exc:
            raise HTTPException(
                status_code=400,
                detail="Invalid time format. Use ISO 8601, e.g. 2026-08-06T12:00:00",
            ) from exc

        if parsed.tzinfo is None:
            source_dt = parsed.replace(tzinfo=source_zone)
        else:
            source_dt = parsed.astimezone(source_zone)

    target_dt = source_dt.astimezone(target_zone)

    return {
        "input": time,
        "from": from_tz,
        "to": to_tz,
        "source": source_dt.isoformat(),
        "converted": target_dt.isoformat(),
        "unix": target_dt.timestamp(),
    }
