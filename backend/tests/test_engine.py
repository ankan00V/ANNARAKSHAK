"""The guarantees the product rests on, tested at the function level."""

import copy
from datetime import date, timedelta

import pytest

from app.config import FLOOR, GATE, MARGIN, PRIOR_MAX_BIAS
from app.engine import advisory, doubt, labelcheck, prior, risk
from app.engine.gate import Prediction, TopK, decide
from app.engine.weather import Day, Window
from app.kb import KB, get_kb, validate

kb = get_kb()


def topk(*pairs, **kw):
    return TopK([Prediction(t, c) for t, c in pairs], "test", is_stub=False, **kw)


def run_gate(tk, crop="rice"):
    return decide(
        tk, farm_crop=crop,
        tier_of=lambda t: kb.targets.get(t, {}).get("tier"),
        has_advisory=lambda t: t in kb.advisories,
        cue_for=kb.cue_for,
    )


# --- gate ------------------------------------------------------------------

def test_gate_advises_when_confident_and_clear():
    d = run_gate(topk(("rice_bacterial_leaf_blight", 0.85), ("rice_brown_spot", 0.1)))
    assert (d.outcome, d.reason) == ("advise", "ABOVE_GATE")
    assert len(d.alternatives) == 2  # alternatives shown even when advising


def test_gate_asks_when_torn_and_a_cue_exists():
    d = run_gate(topk(("rice_brown_spot", 0.51), ("rice_bacterial_leaf_blight", 0.42)))
    assert d.outcome == "clarify" and d.cue_id == "blb_vs_brown_spot_tip"


def test_gate_escalates_when_torn_without_a_cue():
    d = run_gate(topk(("rice_false_smut", 0.5), ("rice_sheath_blight", 0.45)))
    assert (d.outcome, d.reason) == ("escalate", "AMBIGUOUS_NO_CUE")


def test_gate_escalates_below_floor():
    d = run_gate(topk(("rice_brown_spot", FLOOR - 0.01), ("rice_false_smut", 0.1)))
    assert (d.outcome, d.reason) == ("escalate", "BELOW_FLOOR")


def test_gate_escalates_clear_but_under_gate():
    d = run_gate(topk(("rice_brown_spot", GATE - 0.02), ("rice_false_smut", 0.1)))
    assert (d.outcome, d.reason) == ("escalate", "BELOW_GATE")


def test_gate_escalates_crop_mismatch():
    d = run_gate(topk(("maize_aphid", 0.95), ("rice_brown_spot", 0.02)), crop="rice")
    assert d.reason == "CROP_MISMATCH"


def test_gate_escalates_inspection_tier_even_when_confident():
    d = run_gate(topk(("rice_tungro", 0.95), ("rice_brown_spot", 0.02)))
    assert (d.outcome, d.reason) == ("escalate", "NOT_PHOTO_DIAGNOSABLE")


def test_gate_asks_for_retake_on_non_crop_photo():
    d = run_gate(topk(("rice_brown_spot", 0.99), ("rice_false_smut", 0.0),
                      out_of_scope=True, oos_reason="NOT_A_CROP_PHOTO"))
    assert d.outcome == "retake"


def test_gate_healthy_is_advise_without_treatment():
    d = run_gate(topk(("rice_healthy", 0.9), ("rice_brown_spot", 0.05)))
    assert (d.outcome, d.reason) == ("advise", "HEALTHY")


@pytest.mark.parametrize("c1", [i / 20 for i in range(21)])
@pytest.mark.parametrize("gap", [0.0, 0.05, 0.14, 0.16, 0.5])
def test_gate_always_exactly_one_outcome(c1, gap):
    c2 = max(0.0, c1 - gap)
    d = run_gate(topk(("rice_brown_spot", c1), ("rice_bacterial_leaf_blight", c2)))
    assert d.outcome in {"advise", "clarify", "escalate"}
    if d.outcome == "advise":
        assert c1 >= GATE and c1 - c2 >= MARGIN


# --- Doubt Doctor ----------------------------------------------------------

def test_doubt_yes_and_no_resolve_to_each_side():
    cue = kb.cue_for("rice_brown_spot", "rice_bacterial_leaf_blight")
    assert doubt.resolve(cue, "yes") == "rice_bacterial_leaf_blight"
    assert doubt.resolve(cue, "no") == "rice_brown_spot"


def test_doubt_cant_tell_escalates_never_tiebreaks():
    cue = kb.cue_for("rice_brown_spot", "rice_bacterial_leaf_blight")
    assert doubt.resolve(cue, "unknown") is None
    assert doubt.resolve(cue, "maybe") is None


# --- prior -----------------------------------------------------------------

def test_prior_cap_cannot_cross_a_band():
    # Maximum history in favour of the runner-up of an ambiguous pair.
    tk = topk(("rice_brown_spot", 0.5), ("rice_bacterial_leaf_blight", 0.49))
    biased = prior.apply_prior(tk, {"rice_brown_spot": (999, 0)})
    top = biased.predictions[0]
    assert top.confidence - tk.predictions[0].confidence <= PRIOR_MAX_BIAS + 1e-9
    assert run_gate(biased).outcome != "advise"
    # A below-floor prediction stays out of advise however much history.
    low = prior.apply_prior(topk(("rice_brown_spot", FLOOR - 0.01), ("rice_false_smut", 0.0)),
                            {"rice_brown_spot": (999, 0)})
    assert run_gate(low).outcome == "escalate"


def test_prior_is_reported():
    biased = prior.apply_prior(topk(("rice_brown_spot", 0.6), ("rice_false_smut", 0.1)),
                               {"rice_brown_spot": (5, 0)})
    assert biased.prior_bias == {"rice_brown_spot": pytest.approx(PRIOR_MAX_BIAS / 2)}


# --- knowledge base & advisories -------------------------------------------

def test_every_advisory_is_chemical_last_and_cited():
    for target in kb.advisories:
        a = advisory.compose(kb, target, "en", area_acres=2)
        tiers = [r["tier"] for r in a["ladder"]]
        assert tiers == sorted(tiers, key=["cultural", "biological", "chemical"].index)
        assert tiers[0] != "chemical"
        assert a["citations"] and a["what_to_avoid"]


def test_kb_refuses_chemical_first_ladder():
    bad = copy.deepcopy(kb)
    lad = bad.advisories["rice_brown_spot"]["ladder"]
    lad.insert(0, lad.pop())
    assert any("chemical" in e for e in validate(bad))


def test_icar_technologies_link_to_real_targets_and_institutes():
    assert kb.technologies and not validate(kb)
    faw = {t["id"] for t in kb.technologies_for(target="maize_fall_armyworm", audience="farmer")}
    assert {"nbair_bt25_faw", "nbair_ma35_faw", "nbair_spfrnpv_faw"} <= faw
    assert "nbair_faw_lure" not in faw  # official-only item stays out of farmer advice


def test_kb_refuses_technology_on_unknown_target_or_missing_language():
    bad = copy.deepcopy(kb)
    bad.technologies[0]["targets"] = ["rice_ghost_pest"]
    assert any("unknown target" in e for e in validate(bad))
    bad = copy.deepcopy(kb)
    farmer = next(t for t in bad.technologies if t["audience"] == "farmer")
    del farmer["summary"]["mr"]
    assert any("summary missing mr" in e for e in validate(bad))


def test_advisory_carries_icar_options_with_contact():
    a = advisory.compose(kb, "rice_leaf_folder", "hi", area_acres=2)
    ids = [o["id"] for o in a["icar_options"]]
    assert "nrri_tricho_tc" in ids
    card = next(o for o in a["icar_options"] if o["id"] == "nrri_tricho_tc")
    assert card["institute"]["phone"] and card["lead_time_days"] == 45 and card["supply"]


def test_every_rule_has_at_least_two_tasks_in_every_language():
    for target, rule in kb.rules.items():
        for lang in ("en", "hi", "mr"):
            assert len(rule["tasks"][lang]) >= 2, (target, lang)


def test_dose_scales_with_field_area():
    a1 = advisory.compose(kb, "rice_brown_spot", "en", area_acres=1)
    a2 = advisory.compose(kb, "rice_brown_spot", "en", area_acres=2)
    q1 = next(r for r in a1["ladder"] if r["tier"] == "chemical")["quantity"]["amount"]
    q2 = next(r for r in a2["ladder"] if r["tier"] == "chemical")["quantity"]["amount"]
    assert q2 == pytest.approx(2 * q1)


# --- label check -----------------------------------------------------------

ENDORSE = ("safe", "approved", "you can use", "सुरक्षित", "सुरक्षित आहे")


def test_label_check_never_endorses():
    for lang in ("en", "hi", "mr"):
        for code, text in labelcheck.VERDICTS.items():
            assert not any(w in text[lang].lower() for w in ENDORSE), (code, lang)


def test_label_check_verdicts():
    chk = lambda q, t: labelcheck.check(kb, q, "rice", t, "en")["code"]  # noqa: E731
    assert chk("copper oxychloride", "rice_bacterial_leaf_blight") == "NO_OBJECTION_FOUND"
    assert chk("mancozeb", "rice_bacterial_leaf_blight") == "NOT_FOR_TARGET"
    assert chk("emamectin", "rice_bacterial_leaf_blight") == "WRONG_CLASS"
    assert chk("roundup", "rice_brown_spot") == "HERBICIDE"
    assert chk("spinetoram", "rice_leaf_folder") == "WRONG_CROP"
    assert chk("unobtainium 9000", "rice_brown_spot") == "NOT_IN_RECORDS"


# --- risk ------------------------------------------------------------------

def _window(days, rh, tmin, tmax, rain=0.0, start=date(2026, 9, 1)):
    return Window([Day(start + timedelta(i), rh, tmin, tmax, rain) for i in range(days)], "test", None)


def _score(target, window, stage, das, history=False):
    t = kb.targets[target]
    stage_names = next(s["names"] for s in kb.crops[t["crop"]]["stages"] if s["key"] == stage)
    return risk.score_rule(target, kb.rules[target], target_name=t["names"], stage=stage,
                           stage_name=stage_names, das=das, window=window, has_history=history,
                           today=date(2026, 9, 14))


def test_weather_rule_fires_on_consecutive_run_and_says_why():
    s = _score("rice_brown_spot", _window(5, 90, 23, 31), "flowering", 80)
    assert s.fired and s.level == "medium" and "5 days in a row" in s.reason["en"]
    assert s.reason["mr"] and s.reason["hi"]


def test_weather_rule_needs_the_full_run():
    assert not _score("rice_brown_spot", _window(3, 90, 23, 31), "flowering", 80).fired


def test_missing_reading_breaks_a_run():
    w = _window(6, 90, 23, 31)
    w.days[2] = Day(w.days[2].on, None, 23, 31, 0)
    assert not _score("rice_brown_spot", w, "flowering", 80).fired


def test_wrong_stage_never_fires():
    assert not _score("rice_brown_spot", _window(10, 95, 23, 31), "nursery", 10).fired


def test_history_bumps_level():
    assert _score("rice_brown_spot", _window(5, 90, 23, 31), "flowering", 80, history=True).level == "high"


def test_trap_rule_needs_consecutive_nights_over_etl():
    rule = kb.rules["cotton_pink_bollworm"]
    d = date(2026, 9, 14)
    over = [{"recorded_on": d - timedelta(i), "count": 30, "traps": 3, "nights": 1} for i in range(3)]
    assert risk.score_traps("cotton_pink_bollworm", rule, over, d).fired
    gap = over[:1] + [{"recorded_on": d - timedelta(1), "count": 3, "traps": 3, "nights": 1}] + over[2:]
    assert not risk.score_traps("cotton_pink_bollworm", rule, gap, d).fired


# --- vegetation check (reject non-crop photos before trusting the softmax) --

@pytest.mark.parametrize("rgb", [(128, 128, 128), (160, 110, 60), (190, 150, 100), (120, 85, 55), (205, 150, 120)])
def test_non_plant_colours_fail_the_vegetation_check(rgb):
    from PIL import Image

    from app.config import MIN_VEGETATION_FRACTION
    from app.engine.vision import vegetation_fraction

    assert vegetation_fraction(Image.new("RGB", (64, 64), rgb)) < MIN_VEGETATION_FRACTION


@pytest.mark.parametrize("rgb", [(70, 130, 50), (200, 200, 60), (210, 190, 120)])
def test_leaf_and_straw_colours_pass_the_vegetation_check(rgb):
    from PIL import Image

    from app.config import MIN_VEGETATION_FRACTION
    from app.engine.vision import vegetation_fraction

    assert vegetation_fraction(Image.new("RGB", (64, 64), rgb)) >= MIN_VEGETATION_FRACTION
