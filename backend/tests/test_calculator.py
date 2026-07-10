# backend/tests/test_calculator.py
#
# Unit tests for the rewards engine: per-purchase rates, top-category
# semantics, spend caps, and annual value / ROI.

import pytest

from backend.core.card_database import CreditCard, CARD_DATABASE
from backend.core.calculator import calculate_rewards
from backend.core.annual_calculator import calculate_annual_value
from backend.core.comparator import find_best_card


def get_card(card_id):
    return next(c for c in CARD_DATABASE if c.id == card_id)


# ── Per-purchase rates ───────────────────────────────────────────────────────

def test_direct_category_rate():
    csp = get_card("csp")
    calc = calculate_rewards(csp, 100, "dining")
    assert calc.reward_rate == 3
    assert calc.points == 300
    assert calc.cash_value == pytest.approx(3.75)  # 300 * 0.0125
    assert calc.note is None


def test_default_rate_for_unlisted_category():
    csp = get_card("csp")
    calc = calculate_rewards(csp, 100, "drugstores")
    assert calc.reward_rate == 1


def test_csp_general_travel_is_2x_not_portal_5x():
    """CSP earns 5x only via Chase Travel; direct travel bookings earn 2x."""
    csp = get_card("csp")
    calc = calculate_rewards(csp, 1000, "travel")
    assert calc.reward_rate == 2


def test_top_category_card_applies_rate_with_caveat():
    """Citi Custom Cash was previously scored at 1x for everything (dead key)."""
    citi = get_card("citi-custom")
    calc = calculate_rewards(citi, 100, "groceries")
    assert calc.reward_rate == 5
    assert calc.note is not None
    assert "highest-spend" in calc.note


def test_rotating_resolves_to_default_conservatively():
    discover = get_card("discover-it")
    calc = calculate_rewards(discover, 100, "groceries")
    assert calc.reward_rate == 1  # can't know the active quarter
    assert calc.note is None


def test_comparator_ranks_by_cash_value():
    results = find_best_card(CARD_DATABASE, 100, "dining")
    values = [r.calculation.cash_value for r in results]
    assert values == sorted(values, reverse=True)
    # CSR: 3x at 2.0c/pt = $6.00 leads dining
    assert results[0].card.id == "csr"


# ── Annual value: caps ───────────────────────────────────────────────────────

def test_bcp_grocery_cap_limits_annual_value():
    """BCP: 6% groceries capped at $6,000/year, then 1%."""
    bcp = get_card("amex-bcp")
    result = calculate_annual_value(bcp, {"groceries": 1000})  # $12,000/year
    # 6,000*6 + 6,000*1 = 42,000 points -> $420; minus $95 fee = $325
    assert result.total_value == pytest.approx(420.0)
    assert result.net_value == pytest.approx(325.0)


def test_uncapped_calculation_unchanged():
    bcp = get_card("amex-bcp")
    result = calculate_annual_value(bcp, {"groceries": 400})  # $4,800/yr, under cap
    assert result.total_value == pytest.approx(4800 * 6 * 0.01)


def test_citi_top_category_monthly_cap():
    """Citi: 5% on top category up to $500/month, 1% after; no fee."""
    citi = get_card("citi-custom")
    result = calculate_annual_value(citi, {"groceries": 1000})
    # capped: 6,000*5 + 6,000*1 = 36,000 points -> $360
    assert result.total_value == pytest.approx(360.0)
    assert result.net_value == pytest.approx(360.0)
    assert result.roi is None  # no annual fee


def test_top_category_assigned_to_highest_spend_only():
    """5% goes to the single top category; everything else earns 1%."""
    citi = get_card("citi-custom")
    result = calculate_annual_value(citi, {"dining": 400, "groceries": 200})
    # dining: 4,800*5% (under $500/mo cap) = 240; groceries: 2,400*1% = 24
    assert result.total_value == pytest.approx(240.0 + 24.0)


def test_roi_computed_against_fee():
    gold = get_card("amex-gold")
    result = calculate_annual_value(gold, {"dining": 500})  # 6,000*4 = 24,000 pts = $240
    assert result.net_value == pytest.approx(240 - 250)
    assert result.roi == pytest.approx((240 - 250) / 250 * 100)


def test_reward_caps_default_empty():
    card = CreditCard(
        id="t", name="T", issuer="T", annual_fee=0,
        rewards={"default": 2}, point_value=0.01, benefits=[], signup_bonus={},
    )
    result = calculate_annual_value(card, {"other": 100})
    assert result.total_value == pytest.approx(1200 * 2 * 0.01)
