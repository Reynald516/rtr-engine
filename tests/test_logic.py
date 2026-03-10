# tests/test_logic.py 

from app.logic import rtr_logic


def test_rtr_logic_danger():
    risk = rtr_logic(
        cluster=1,
        anomaly_flag=[-1],
        night_ratio=0.7
    )
    assert risk == "DANGER"


def test_rtr_logic_high():
    risk = rtr_logic(
        cluster=1,
        anomaly_flag=[-1],
        night_ratio=0.5
    )
    assert risk == "HIGH"


def test_rtr_logic_medium():
    risk = rtr_logic(
        cluster=0,
        anomaly_flag=[-1],
        night_ratio=0.2
    )
    assert risk == "MEDIUM"


def test_rtr_logic_low():
    risk = rtr_logic(
        cluster=0,
        anomaly_flag=[],
        night_ratio=0.1
    )
    assert risk == "LOW"