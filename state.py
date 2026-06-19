import json
from datetime import date
from pathlib import Path

STATE_FILE = Path("last_seen.json")


def today():
    return str(date.today())


def load_state():
    if not STATE_FILE.exists():
        return {}
    return json.loads(STATE_FILE.read_text(encoding="utf-8"))


def save_state(st):
    STATE_FILE.write_text(json.dumps(st, indent=2, ensure_ascii=False), encoding="utf-8")


def notify_count(st, slot_key):
    return st.get(today(), {}).get(slot_key, 0)


def should_notify(st, slot_key, max_per_day):
    return notify_count(st, slot_key) < max_per_day


def increment(st, slot_key):
    day = today()
    if day not in st:
        st[day] = {}
    st[day][slot_key] = st[day].get(slot_key, 0) + 1
    return st


def make_slot_key(especialidad, medico, fecha, hora):
    raw = f"{especialidad}_{medico}_{fecha}_{hora}"
    return raw.lower().replace(" ", "_")
