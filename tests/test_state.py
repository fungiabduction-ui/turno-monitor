import state as s


def test_notify_count_cero_para_slot_nuevo():
    st = {}
    assert s.notify_count(st, "endocrinologia_drperez_2026-06-19_10:30") == 0


def test_increment_crea_entrada():
    st = {}
    st = s.increment(st, "slot_key")
    assert s.notify_count(st, "slot_key") == 1


def test_increment_acumula():
    st = {}
    for _ in range(3):
        st = s.increment(st, "slot_key")
    assert s.notify_count(st, "slot_key") == 3


def test_should_notify_bajo_maximo():
    st = {}
    st = s.increment(st, "slot_key")
    assert s.should_notify(st, "slot_key", 6) is True


def test_should_not_notify_en_maximo():
    st = {}
    for _ in range(6):
        st = s.increment(st, "slot_key")
    assert s.should_notify(st, "slot_key", 6) is False


def test_make_slot_key_sin_espacios_y_lowercase():
    key = s.make_slot_key("Endocrinología", "Dr. Pérez", "2026-06-25", "10:30")
    assert " " not in key
    assert key == key.lower()


def test_nuevo_dia_resetea_contador(monkeypatch):
    monkeypatch.setattr(s, "today", lambda: "2026-06-18")
    st = {}
    for _ in range(6):
        st = s.increment(st, "slot")
    assert s.should_notify(st, "slot", 6) is False

    monkeypatch.setattr(s, "today", lambda: "2026-06-19")
    assert s.should_notify(st, "slot", 6) is True
