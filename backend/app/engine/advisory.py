"""Compose a farmer-facing advisory from the knowledge base.

Deterministic: every sentence comes from the KB entry for the target, so there
is nothing to hallucinate and every advisory carries its citations. The ladder
order is re-checked here even though the KB loader already enforces it — a
structural promise should hold at the last step, not just the first.

Chemical rungs also carry a quantity worked out for the farm's own area, which
replaces a separate "dosage calculator": the dose, the water volume and the
product amount come from one place.
"""

from __future__ import annotations

from app.kb import KB, TIER_ORDER, tr

UNIT_WORDS = {
    "g": {"en": "g per litre of water", "hi": "ग्राम प्रति लीटर पानी", "mr": "ग्रॅम प्रति लिटर पाणी"},
    "ml": {"en": "ml per litre of water", "hi": "मिली प्रति लीटर पानी", "mr": "मिली प्रति लिटर पाणी"},
}
FOR_AREA = {
    "en": "For your {area} acre field: about {qty} {unit} in {water} litres of water.",
    "hi": "आपके {area} एकड़ खेत के लिए: लगभग {qty} {unit}, {water} लीटर पानी में।",
    "mr": "तुमच्या {area} एकर शेतासाठी: सुमारे {qty} {unit}, {water} लिटर पाण्यात.",
}
LABEL_RULE = {
    "en": "Follow the printed label. Wear gloves and a mask; keep children and animals away.",
    "hi": "छपे लेबल का पालन करें। दस्ताने और मास्क पहनें; बच्चों और पशुओं को दूर रखें।",
    "mr": "छापील लेबलचे पालन करा. हातमोजे व मास्क वापरा; मुले व जनावरे दूर ठेवा.",
}
HEALTHY = {
    "en": "No disease or pest found in this photo. Keep checking your crop every week.",
    "hi": "इस फोटो में कोई रोग या कीट नहीं मिला। हर हफ्ते फसल देखते रहें।",
    "mr": "या फोटोत कोणताही रोग किंवा कीड आढळली नाही. दर आठवड्याला पीक तपासत राहा.",
}


UNIT_SHORT = {
    "g": {"en": "g", "hi": "ग्राम", "mr": "ग्रॅम"},
    "ml": {"en": "ml", "hi": "मिली", "mr": "मिली"},
}


class LadderOrderError(ValueError):
    pass


def _fmt(n: float) -> str:
    return f"{n:.0f}" if n >= 10 else f"{n:.1f}".rstrip("0").rstrip(".")


def compose(kb: KB, target: str, lang: str, area_acres: float | None = None) -> dict:
    adv = kb.advisories[target]
    ladder_out = []
    for rung in adv["ladder"]:
        item: dict = {"tier": rung["tier"]}
        if rung["tier"] != "chemical":
            item["action"] = tr(rung["action"], lang)
        else:
            pest = kb.pesticides[rung["ingredient"]]
            item |= {
                "ingredient": rung["ingredient"],
                "product": pest["name"],
                "class": pest["class"],
                "timing": tr(rung.get("timing"), lang),
                "verified": bool(rung.get("verified")),
                "label_rule": LABEL_RULE.get(lang, LABEL_RULE["en"]),
            }
            dose, unit = rung.get("dose_per_litre"), rung.get("dose_unit")
            if dose is not None and unit:
                item["dose"] = f"{_fmt(dose)} {tr(UNIT_WORDS[unit], lang)}"
                water = rung.get("water_l_per_acre")
                if area_acres and water:
                    litres = water * area_acres
                    qty = dose * litres
                    item["for_field"] = FOR_AREA.get(lang, FOR_AREA["en"]).format(
                        area=_fmt(area_acres), qty=_fmt(qty), unit=tr(UNIT_SHORT[unit], lang), water=_fmt(litres)
                    )
                    item["quantity"] = {"amount": round(qty, 1), "unit": unit, "water_l": round(litres)}
            else:
                item["dose"] = rung.get("dose_basis", "")
        ladder_out.append(item)

    order = [TIER_ORDER[r["tier"]] for r in ladder_out]
    if order != sorted(order):
        raise LadderOrderError(f"{target}: ladder not chemical-last at composition")

    t = kb.targets[target]
    return {
        "target": target,
        "name": tr(t["names"], lang),
        "signature": tr(t["signature"], lang),
        "what_to_check": tr(adv["what_to_check"], lang),
        "what_to_avoid": [tr(x, lang) for x in adv["what_to_avoid"]],
        "ladder": ladder_out,
        "expert_trigger": tr(adv["expert_trigger"], lang),
        "citations": adv["citations"],
        # ICAR-released products and tools for this problem, with who to call.
        "icar_options": [kb.tech_view(x, lang) for x in kb.technologies_for(target=target, audience="farmer")],
    }


def healthy_note(lang: str) -> str:
    return HEALTHY.get(lang, HEALTHY["en"])
