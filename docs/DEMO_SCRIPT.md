# AnnRakshak — 5-minute demo

Setup (once, before judging): backend on :8010, frontend on :5173,
`backend/demo_story.py` run so the dashboards have history. Phone-sized window
for the farmer app, desktop window for expert and officials.

Every step names the PS clause it proves.

## 1. The alert comes first (0:00–0:50) — *weather-based risk forecasting, pest-trap/sensor inputs*

- `/app` → pick **Sunita Bhoyar · Rice · Bhandara** (Marathi).
- Point at the crop-stage bar (78 days, flowering) and the first card under **आजची शेत तपासणी**: a high-risk alert with the reason in her language ("14 consecutive days of humidity above 80 % at 25–30 °C…") and the **two things to check**.
- Tap 🔊 — Sarvam reads it aloud.
- Say: *"Every alert carries a task. It stays until she records what she found — there is no dismiss button."*
- Scroll: weather strip (source badge) and **rain vs IMD normal** for Vidarbha.

## 2. Photo → honest answer (0:50–2:10) — *image-based identification, explainability*

- Scan → pick a held-out ICAR photo (never seen in training) → Scan. Photos are tagged with the path the live gate takes on them (`ml/sample_outcomes.py`): untagged ones advise; **asks a question** and **goes to expert** are there so you can show those paths on purpose.
- **Advise path:** diagnosis, confidence bar with the gate's own ask/advise marks, Grad-CAM overlay ("where the AI looked"), alternatives.
- The advisory opens with **Do NOT do this** in red, then field practice → natural control → chemical, collapsed. Open it: dose worked out for her 2.5 acres, label rule, "dose to be confirmed by your officer". Below it, **Proven by ICAR**: the ICAR-released bio-product for this pest (e.g. NRRI Tricho-card), the ICAR-reported result, where to get it and a tap-to-call institute number.
- **Doubt Doctor path:** switch to a maize farm (e.g. Ganesh Kolte, Pune) → the **asks a question** photo → turcicum 52 % vs curvularia 37 % side by side → "Are most spots long — longer than your thumb — and cigar-shaped?" → Yes → turcicum leaf blight, "Settled by your answer", and the answer is recorded.
- Say: *"The system is built to say 'I'm not sure' out loud. A confident wrong answer is what the PS says causes the damage."*

## 3. Stop the wrong spray (2:10–2:40) — *safe input usage, targeted pesticide use*

- फवारणी → tap **Glyphosate** → red veto: a weed killer against a disease.
- Tap **Emamectin** → wrong class (insecticide for a bacterial disease).
- Say: *"It can only veto. There is no word for 'safe' in its vocabulary — the printed label decides dose."*

## 4. The expert closes the loop (2:40–3:40) — *expert validation, referral, learning from confirmations*

- `/expert` → open the top case. Timer starts (target under 3 min).
- Show what arrived pre-packed: photos, ranked hypotheses, the farmer's Doubt Doctor answer, trap counts, recent alerts, follow-ups.
- **ICAR technologies & referral**: the ICAR repository entries for the suspected pest on this farm's crop, with the institute to route the farmer or KVK to.
- Correct or confirm → optionally tick lab referral → submit.
- Result card: farmer notified, **N nearby farms within 5 km got inspection alerts**, district counts updated.
- Say: *"'Learns from field confirmations' — a capped, inspectable prior and a field-accuracy record. Not retraining, and we say so."*

## 5. The officials' view (3:40–4:40) — *geospatial hotspots, dashboards, preventive planning*

- `/officer`: KPIs → hotspot map (confirmed / awaiting / AI-advised, 5 km radius, risk alerts) → **confidence gate** panel (how often it advised, asked, escalated) → **model card** (test accuracy, *accuracy when it advises*, benchmark vs the two papers' methods).
- **Risk outlook**: which pests are building in which districts this week → where to send scouts, and which **ICAR bio-inputs to stock** (NRRI Tricho-cards need a 45-day indent — order when the risk starts building, not when the damage shows).
- **Pesticide baseline** (MoSPI/DPPQS): Maharashtra 8,719 t in 2023-24, #3 in India — the number targeted advice has to move.
- **Rainfall vs IMD normal** per subdivision with 60 monsoons of history.
- Tap **Run risk sweep** — live weather for every farm, new alerts.

## 6. Close (4:40–5:00)

*"Four crops, 28 targets, three languages, one rule: never a confident wrong answer."*

## Questions judges will ask

- **"What happens when it's wrong?"** Show the gate panel and an escalated case; the expert correction is recorded against the label the model actually predicted.
- **"How accurate is it?"** Model card: test-set numbers on held-out ICAR photos, and accuracy *when it chooses to advise*. Field accuracy comes from expert verdicts, separately.
- **"Why is 'Expert agreed with AI' so low?"** Experts only see what the gate escalated — the photos the model was unsure about. Low agreement there means the gate sent the right photos: the ones it would have got wrong reached a human instead of a farmer.
- **"Can it detect blast?"** Not from a photo — the ICAR set has no blast images. Blast is covered by weather alerts and inspection tasks, and an escalation path. Say it plainly.
- **"Does it work offline / without a smartphone?"** Honest answer: web app installable as a PWA today; SMS/IVR is the next integration (see docs/INTEGRATIONS.md).
