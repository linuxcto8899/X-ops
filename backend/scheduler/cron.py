"""Minimal 5-field cron parser and next-run computation (local timezone)."""
from datetime import datetime, timedelta, timezone as dt_timezone
from django.utils import timezone


def parse_cron(expr):
    """Parse a 5-field cron expression into a dict of allowed values."""
    parts = expr.split()
    if len(parts) != 5:
        raise ValueError('cron must have 5 fields: minute hour day month weekday')
    fields = []
    specs = [
        (0, 59, parts[0]), (0, 23, parts[1]),
        (1, 31, parts[2]), (1, 12, parts[3]), (0, 7, parts[4]),
    ]
    for low, high, part in specs:
        allowed = set()
        for item in part.split(','):
            item = item.strip()
            if item == '*':
                allowed.update(range(low, high + 1))
            elif '/' in item:
                base, step = item.split('/', 1)
                step = int(step)
                start = low if base in ('*', '') else int(base)
                allowed.update(range(start, high + 1, step))
            elif '-' in item:
                a, b = item.split('-', 1)
                allowed.update(range(int(a), int(b) + 1))
            else:
                allowed.add(int(item))
        fields.append(allowed)
    # weekday 7 == 0 (Sunday)
    if 7 in fields[4]:
        fields[4].add(0)
    return fields


def next_after(expr, anchor):
    """Return the next datetime matching expr, strictly after anchor (tz-aware)."""
    fields = parse_cron(expr)
    local = anchor.astimezone(timezone.get_current_timezone())
    for _ in range(366 * 2):
        if local.minute not in fields[0] or local.hour not in fields[1]:
            local = (local + timedelta(minutes=1)).replace(second=0, microsecond=0)
            continue
        if local.day not in fields[2] or local.month not in fields[3]:
            local = (local + timedelta(days=1)).replace(hour=0, minute=0, second=0, microsecond=0)
            continue
        weekday = (local.weekday() + 1) % 7  # Monday=1 ... Sunday=0
        if weekday not in fields[4]:
            local = (local + timedelta(days=1)).replace(hour=0, minute=0, second=0, microsecond=0)
            continue
        return local.astimezone(dt_timezone.utc)
    return None
