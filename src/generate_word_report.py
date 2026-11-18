"""
generate_word_report.py
-----------------------
Generates the Results and Discussion section as a Word document.
Run:  .\\venv\\Scripts\\python src\\generate_word_report.py
Output:  outputs/BalikBisita_Results_and_Discussion.docx
"""

import pandas as pd
import numpy as np
from pathlib import Path
from docx import Document
from docx.shared import Inches, Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_ALIGN_VERTICAL
from docx.oxml.ns import qn
from docx.oxml import OxmlElement

ROOT    = Path(__file__).resolve().parent.parent
OUT     = ROOT / "outputs"
IMGS    = ROOT / "outputs"
DOCX_OUT = OUT / "BalikBisita_Results_and_Discussion.docx"

# ── Load evaluation summary ───────────────────────────────────────────────────
csv = pd.read_csv(OUT / "evaluation_summary.csv")
def get_val(metric_name):
    row = csv[csv["Metric"] == metric_name]
    if row.empty:
        return "N/A"
    return row["Value"].values[0]

# ── Helper: styled heading ────────────────────────────────────────────────────
def add_heading(doc, text, level=1):
    h = doc.add_heading(text, level=level)
    h.alignment = WD_ALIGN_PARAGRAPH.LEFT
    run = h.runs[0] if h.runs else h.add_run(text)
    run.font.color.rgb = RGBColor(0x15, 0x65, 0xC0)
    return h

def add_body(doc, text):
    p = doc.add_paragraph(text)
    p.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
    p.paragraph_format.space_after = Pt(6)
    for run in p.runs:
        run.font.size = Pt(11)
    return p

def add_figure(doc, img_filename, caption_text, width_inches=5.8):
    img_path = IMGS / img_filename
    if not img_path.exists():
        doc.add_paragraph(f"[IMAGE NOT FOUND: {img_filename}]")
        return
    p_img = doc.add_paragraph()
    p_img.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run = p_img.add_run()
    run.add_picture(str(img_path), width=Inches(width_inches))
    cap = doc.add_paragraph(caption_text)
    cap.alignment = WD_ALIGN_PARAGRAPH.CENTER
    cap.paragraph_format.space_after = Pt(12)
    for run in cap.runs:
        run.font.size = Pt(10)
        run.font.italic = True
    return cap

def add_bold_label(para, label, rest):
    run_b = para.add_run(label)
    run_b.bold = True
    run_b.font.size = Pt(11)
    run_r = para.add_run(rest)
    run_r.font.size = Pt(11)

def shade_row(row, hex_color="D6E4F7"):
    for cell in row.cells:
        tc = cell._tc
        tcPr = tc.get_or_add_tcPr()
        shd = OxmlElement("w:shd")
        shd.set(qn("w:val"), "clear")
        shd.set(qn("w:color"), "auto")
        shd.set(qn("w:fill"), hex_color)
        tcPr.append(shd)

# ══════════════════════════════════════════════════════════════════════════════
# BUILD DOCUMENT
# ══════════════════════════════════════════════════════════════════════════════
doc = Document()

# --- Page margins ---
for section in doc.sections:
    section.top_margin    = Inches(1.0)
    section.bottom_margin = Inches(1.0)
    section.left_margin   = Inches(1.25)
    section.right_margin  = Inches(1.25)

# ── Title ─────────────────────────────────────────────────────────────────────
title = doc.add_heading("RESULTS AND DISCUSSION", level=0)
title.alignment = WD_ALIGN_PARAGRAPH.CENTER
for run in title.runs:
    run.font.color.rgb = RGBColor(0x15, 0x65, 0xC0)
    run.font.size = Pt(16)

doc.add_paragraph(
    "This chapter presents the results of the machine learning component of the BalikBisita "
    "IoT-enabled patient recall system. The LightGBM model with a Poisson objective was trained "
    "on 2014–2015 emergency department hourly arrival data, validated on 2016 data, and evaluated "
    "on the held-out 2017 test year. Results are organized as follows: exploratory analysis of "
    "the dataset, model training outcomes, full evaluation metrics aligned with the study's "
    "methodology, and a concluding summary table."
).alignment = WD_ALIGN_PARAGRAPH.JUSTIFY

doc.add_page_break()

# ══════════════════════════════════════════════════════════════════════════════
# SECTION 1 — EXPLORATORY DATA ANALYSIS
# ══════════════════════════════════════════════════════════════════════════════
add_heading(doc, "1. Exploratory Data Analysis", level=1)
add_body(doc,
    "Before training the model, an exploratory data analysis (EDA) was conducted on the "
    "ed-hourly-clean dataset to understand its structure, distribution, and temporal patterns. "
    "EDA informs which features are most relevant and validates that the dataset is suitable "
    "for the forecasting task. The dataset contains 35,040 hourly records spanning January 2014 "
    "to December 2017, with no missing values and no gaps in the hourly index."
)

# 1.1 Full time series
add_heading(doc, "1.1 Full Time-Series Overview", level=2)
add_body(doc,
    "Figure 1 shows the complete hourly arrival count from 2014 to 2017. The series reveals a "
    "consistent repeating daily cycle throughout all four years, with no apparent long-term upward "
    "or downward trend. Brief irregular spikes are visible and correspond to high-demand days. "
    "The regularity of the daily pattern confirms that calendar-based and lag-based features "
    "will carry strong predictive signal for the model."
)
add_body(doc,
    "In a real-world context, this chart represents what a clinic or kiosk would observe over "
    "four years of operation: a predictable rhythm of patient arrivals that follows the working "
    "day, with periodic surges around holidays or health campaigns. The stability of this pattern "
    "is an encouraging sign that a data-driven forecasting system is viable for long-term deployment."
)
add_figure(doc, "eda_full_series.png",
           "Figure 1. Hourly ED arrivals across the full dataset (2014–2017).")

# 1.2 Hourly average
add_heading(doc, "1.2 Average Arrivals by Hour of Day", level=2)
add_body(doc,
    "Figure 2 shows the mean arrival count for each of the 24 hours of the day, averaged across "
    "all four years. The pattern shows low activity during overnight hours (midnight to 6:00), "
    "rising sharply from 7:00 onwards, peaking in the late morning and early afternoon, and "
    "declining in the evening. This pronounced intra-day cycle directly motivates the inclusion "
    "of the hour-of-day feature and the distinction between peak hours (10:00–19:00) and "
    "off-peak hours in the evaluation."
)
add_body(doc,
    "For the BalikBisita system, this means that recall messages should be prioritized for "
    "early morning delivery so that patients arrive during the peak window when staff are most "
    "prepared. The model uses this hourly pattern as a primary input, so forecasts will naturally "
    "reflect higher predicted volumes during this period."
)
add_figure(doc, "eda_hourly_avg.png",
           "Figure 2. Mean hourly arrival count by hour of day (0–23).")

# 1.3 Day of week
add_heading(doc, "1.3 Average Arrivals by Day of Week", level=2)
add_body(doc,
    "Figure 3 shows average arrivals grouped by day of the week. Weekdays consistently show "
    "higher volumes than weekends, confirming that the is_weekend binary feature and the "
    "day_of_week ordinal feature carry useful predictive information. The drop on weekends "
    "reflects reduced staffing, reduced elective visits, and patient preference to defer "
    "non-emergency visits to weekdays."
)
add_body(doc,
    "In practice, this means the system should forecast noticeably lower check-in volumes on "
    "Saturdays and Sundays. A clinic using the BalikBisita system can use this pattern to adjust "
    "weekend staffing levels without relying on historical memory alone."
)
add_figure(doc, "eda_dow_avg.png",
           "Figure 3. Mean hourly arrival count by day of the week.")

# 1.4 Monthly totals
add_heading(doc, "1.4 Monthly Total Arrivals", level=2)
add_body(doc,
    "Figure 4 aggregates arrivals into monthly totals. A mild seasonal pattern is visible, "
    "with some months showing higher overall volumes than others. This motivates the inclusion "
    "of the month feature in the model. Year-over-year comparison shows broadly stable volumes "
    "across 2014 to 2017, indicating the dataset is not affected by a major secular trend that "
    "would make earlier years misleading as training data."
)
add_body(doc,
    "Long-term, this plot supports the system's design decision to retrain the model periodically "
    "as new kiosk data accumulates. If a significant upward trend in arrivals were observed, "
    "older training data would need to be down-weighted or discarded to keep forecasts accurate."
)
add_figure(doc, "eda_monthly_totals.png",
           "Figure 4. Monthly total arrivals across all four years (2014–2017).")

# 1.5 Distribution
add_heading(doc, "1.5 Distribution of Hourly Counts", level=2)
add_body(doc,
    "Figure 5 shows a histogram of all hourly arrival counts. The distribution is right-skewed: "
    "most hours have low to moderate counts, while a smaller number of hours have very high "
    "counts. This is characteristic of count data and is the primary reason the LightGBM model "
    "was configured with a Poisson objective rather than a standard mean-squared-error regression "
    "loss. A Poisson loss is designed for non-negative count data and handles this skew more "
    "appropriately than assuming a symmetric Gaussian error distribution."
)
add_body(doc,
    "This distributional shape also explains why the model's precision on high-load detection is "
    "higher than its recall: extreme values are rare and the model is appropriately conservative "
    "about predicting them, only flagging high-load hours when the evidence is strong."
)
add_figure(doc, "eda_distribution.png",
           "Figure 5. Distribution of hourly arrival counts across the full dataset.")

doc.add_page_break()

# ══════════════════════════════════════════════════════════════════════════════
# SECTION 2 — MODEL TRAINING
# ══════════════════════════════════════════════════════════════════════════════
add_heading(doc, "2. Model Training", level=1)
add_body(doc,
    "The LightGBM model was trained using a grid search over three hyperparameters: "
    "learning rate, number of leaves, and minimum child samples. Early stopping was applied "
    "using the 2016 validation set to prevent overfitting. The best configuration found was "
    f"a learning rate of {get_val('Best learning_rate')}, "
    f"{get_val('Best num_leaves')} leaves, and a minimum child sample size of "
    f"{get_val('Best min_child_samples')}, resulting in a final model with "
    f"{get_val('Number of trees')} boosting trees."
)

# 2.1 Train/Val/Test MAE
add_heading(doc, "2.1 MAE Across Training, Validation, and Test Splits", level=2)
add_body(doc,
    "Figure 6 compares the Mean Absolute Error across the three data splits. The training MAE "
    f"({float(get_val('Train MAE')):.4f} arrivals/hour) is the lowest, as expected, since the model "
    f"was fitted on this data. The validation MAE ({float(get_val('Validation MAE')):.4f}) and "
    f"test MAE ({float(get_val('Test MAE')):.4f}) are only slightly higher, indicating that the "
    "model generalizes well and is not significantly overfitted. The small gap between validation "
    "and test performance confirms that hyperparameter selection on the validation set did not "
    "cause data leakage or over-tuning."
)
add_body(doc,
    "A large gap between training and test MAE would indicate overfitting — a model that memorized "
    "the training data rather than learning transferable patterns. The near-consistent MAE across "
    "all three splits demonstrates that the model has learned genuine demand patterns that apply "
    "to unseen dates, which is the fundamental requirement for a system intended to support "
    "forward-looking staff planning decisions."
)
add_figure(doc, "train_val_test_mae.png",
           "Figure 6. MAE on training (2014–2015), validation (2016), and test (2017) splits.")

# 2.2 Feature importance
add_heading(doc, "2.2 Feature Importance", level=2)
add_body(doc,
    "Figure 7 shows each input feature ranked by its total gain contribution to the model's "
    "decision trees. Gain measures how much a feature reduces prediction error across all the "
    "splits where it is used. The lag features — particularly lag_24h (count from exactly 24 "
    "hours ago) and lag_168h (count from exactly one week ago) — dominate the ranking. This "
    "confirms that the most informative predictor of how many patients will arrive at a given "
    "hour is how many arrived at the same hour yesterday and the same hour last week. Calendar "
    "features such as hour of day and day of week also contribute meaningfully, while rolling "
    "averages and holiday indicators provide supplementary signal."
)
add_body(doc,
    "This result has a direct operational implication: the BalikBisita system will produce the "
    "most accurate forecasts when it has access to at least two weeks of recent kiosk check-in "
    "history. During initial deployment, when fewer than 14 days of data have accumulated, "
    "forecast accuracy will be lower until sufficient history builds up. Clinics should account "
    "for this warm-up period in their deployment plan."
)
add_figure(doc, "feature_importance.png",
           "Figure 7. Feature importance by gain. Higher values indicate greater predictive contribution.")

doc.add_page_break()

# ══════════════════════════════════════════════════════════════════════════════
# SECTION 3 — MODEL EVALUATION
# ══════════════════════════════════════════════════════════════════════════════
add_heading(doc, "3. Model Evaluation", level=1)
add_body(doc,
    "The trained model was evaluated on the 2017 test year — data the model never saw during "
    "training or hyperparameter selection. All metrics described in the study's methodology are "
    "reported below: overall MAE and RMSE, peak-hour MAE, skill score against the seasonal-naïve "
    "baseline, and high-load detection performance including a confusion matrix."
)

# 3.1 Actual vs Predicted time series
add_heading(doc, "3.1 Actual vs. Predicted Arrivals (Sample Week)", level=2)
add_body(doc,
    "Figure 8 shows the model's predictions overlaid on actual arrival counts for a representative "
    "sample week (January 2–8, 2017). The predicted line closely follows the shape of the actual "
    "line, capturing the daily rise-and-fall cycle and the difference between weekdays and the "
    "weekend. The model tends to under-predict the sharpest peaks, which is expected behavior "
    "for a Poisson regression model that predicts conditional means rather than extreme values."
)
add_body(doc,
    "In practice, this visualization is what a clinic administrator would see when reviewing "
    "the system's forecast for the coming week. The close alignment between the two lines "
    "demonstrates that the system provides actionable guidance: staff scheduled based on these "
    "forecasts would arrive on the right days and at the right hours in most cases, with moderate "
    "uncertainty at the highest-demand periods."
)
add_figure(doc, "actual_vs_predicted.png",
           "Figure 8. Actual (blue) vs. predicted (red dashed) hourly arrivals for January 2–8, 2017.")

# 3.2 Scatter
add_heading(doc, "3.2 Actual vs. Predicted Scatter Plot", level=2)
add_body(doc,
    "Figure 9 plots every test-set hour as a point with its actual count on the horizontal axis "
    "and its predicted count on the vertical axis. Points along the red diagonal represent perfect "
    "predictions. The scatter shows that the model's predictions are well-centered around the "
    "diagonal for low to moderate counts, while very high actual counts are systematically "
    "under-predicted — the cloud of points does not extend as far along the vertical axis as "
    "along the horizontal. This is the expected behavior of a mean-regression model and "
    "is quantified by the lower recall in the high-load detection metrics."
)
add_body(doc,
    "The practical implication is that the system is most reliable for planning regular staffing "
    "levels. For rare surge events — such as a disease outbreak or post-holiday rush — the model "
    "will under-estimate demand. Clinics should maintain a buffer in their scheduling and treat "
    "the forecast as a floor rather than a ceiling on expected patient volume."
)
add_figure(doc, "scatter_actual_vs_predicted.png",
           "Figure 9. Scatter plot of actual versus predicted arrivals for all 8,736 test hours (2017).")

# 3.3 Overall MAE and RMSE
add_heading(doc, "3.3 Overall MAE and RMSE", level=2)
mae_val  = float(get_val("Test MAE"))
rmse_val = float(get_val("Test RMSE"))
add_body(doc,
    f"The model achieved a test-set MAE of {mae_val:.4f} arrivals per hour and an RMSE of "
    f"{rmse_val:.4f} arrivals per hour. MAE is the primary metric because it is interpretable "
    "without domain expertise: on average, the forecast is off by approximately 1.74 patients "
    "per hour. The RMSE is higher than the MAE because it squares errors before averaging, "
    "giving disproportionate weight to the larger misses that occur during peak periods. The "
    "gap between RMSE and MAE (approximately 0.58) indicates that while most predictions are "
    "close to correct, a subset of hours — predominantly the busiest ones — carry larger errors."
)
add_body(doc,
    "An error of 1.74 patients per hour is clinically meaningful in a small to medium outpatient "
    "setting. For context, if a clinic has 10 staff and expects 15 arrivals in an hour, being off "
    "by 1–2 patients is manageable. However, for a high-volume emergency department where 40 or "
    "more arrivals per hour are common, the same absolute error becomes less significant. "
    "These numbers should be interpreted relative to the facility's typical hourly volume when "
    "determining whether the forecast accuracy is sufficient for operational use."
)

# 3.4 Peak-hour MAE
add_heading(doc, "3.4 Peak-Hour MAE (10:00–19:00)", level=2)
peak_mae  = float(get_val("Peak-hour MAE (10:00-19:00)"))
offpk_mae = float(get_val("Off-peak MAE"))
add_body(doc,
    f"During the designated peak period of 10:00 to 19:00, the model's MAE rises to "
    f"{peak_mae:.4f} arrivals per hour, compared to {offpk_mae:.4f} during off-peak hours. "
    "The higher peak-hour error is consistent with the EDA finding that arrival counts are "
    "more variable during the busiest part of the day. More patients arrive, more irregularity "
    "exists in those counts, and the model's conditional mean prediction smooths over that "
    "variability."
)
add_body(doc,
    "For the BalikBisita system, peak hours are precisely when accurate forecasting matters most. "
    "A 2.14-patient error during a period when 8–12 patients might arrive per hour represents "
    "a relative error of roughly 20–25%. Clinics should treat peak-hour forecasts as approximate "
    "guidance and maintain flexible staffing arrangements — such as on-call staff or staggered "
    "shift starts — to absorb the additional uncertainty during this window."
)

# 3.5 MAE by hour
add_heading(doc, "3.5 MAE by Hour of Day", level=2)
add_body(doc,
    "Figure 10 breaks down MAE for each individual hour of the day. Red bars indicate peak hours "
    "(10:00–19:00); blue bars indicate off-peak hours. The chart confirms that prediction error "
    "rises during the busiest part of the day and falls during overnight and early morning hours, "
    "when arrival counts are low and more predictable. No single hour shows an anomalously large "
    "error that would indicate a systematic modeling failure."
)
add_figure(doc, "mae_by_hour.png",
           "Figure 10. MAE broken down by hour of day. Red bars indicate peak hours (10:00–19:00).")

# 3.6 MAE by day of week
add_heading(doc, "3.6 MAE by Day of Week", level=2)
add_body(doc,
    "Figure 11 shows MAE disaggregated by day of the week. Weekdays and weekends show comparable "
    "error levels, indicating the model handles both schedules without systematic bias toward "
    "either. Any day-of-week variation in MAE is small and within normal statistical fluctuation "
    "across the test year."
)
add_body(doc,
    "This consistency across days of the week is an important finding for real-world deployment. "
    "It means the system does not have a blind spot for a particular day — for example, it does "
    "not systematically fail on Mondays after long weekends. Clinics can trust the forecast "
    "equally across all days of the week."
)
add_figure(doc, "mae_by_dow.png",
           "Figure 11. MAE broken down by day of the week.")

# 3.7 Residuals
add_heading(doc, "3.7 Residual Analysis", level=2)
add_body(doc,
    "Figure 12 provides two residual diagnostic plots. The left panel shows a histogram of all "
    "residuals (actual minus predicted). The distribution is approximately centered near zero "
    "with a slight rightward tail, indicating that the model occasionally under-predicts high "
    "counts but does not have a systematic directional bias. The right panel plots residuals "
    "against predicted values. The spread of residuals is roughly constant across the prediction "
    "range, with no strong fanning pattern, confirming that prediction uncertainty is not "
    "dramatically larger at higher predicted values."
)
add_body(doc,
    "Residual analysis matters because a biased model — one that consistently predicts too high "
    "or too low — would lead to systematically wrong staffing decisions. The near-zero centering "
    "of residuals confirms that the BalikBisita forecasts are unbiased on average, which is the "
    "minimum requirement for a forecast to be useful in operational planning."
)
add_figure(doc, "residuals.png",
           "Figure 12. Left: distribution of residuals (actual − predicted). Right: residuals vs. predicted values.")

# 3.8 Skill score
add_heading(doc, "3.8 Skill Score vs. Seasonal-Naïve Baseline", level=2)
skill = float(get_val("Skill score vs naïve baseline"))
naive_mae = float(get_val("Seasonal-naïve baseline MAE"))
add_body(doc,
    f"The seasonal-naïve baseline — which predicts each hour's count by simply repeating the "
    f"count from the same hour one week earlier — achieves an MAE of {naive_mae:.4f} arrivals "
    f"per hour on the test set. The LightGBM model achieves an MAE of {mae_val:.4f}, giving "
    f"a skill score of {skill:.4f}. This means the model reduces forecasting error by "
    f"{skill*100:.1f}% relative to the simplest possible benchmark."
)
add_body(doc,
    "A skill score above zero means the model adds real value over doing nothing more than "
    "looking at last week's data. A score of 25.8% improvement is a meaningful result, "
    "especially considering that the seasonal-naïve baseline is surprisingly strong for "
    "regular demand patterns. For a clinical deployment, this improvement translates to fewer "
    "overstaffed and understaffed shifts compared to a manual schedule based on last week's "
    "experience alone."
)

doc.add_page_break()

# 3.9 High-load detection
add_heading(doc, "3.9 High-Load Detection", level=2)
prec = float(get_val("High-load Precision"))
rec  = float(get_val("High-load Recall"))
f1   = float(get_val("High-load F1"))
a_thr = float(get_val("Actual high-load threshold (75th pct of training)"))
p_thr = float(get_val("Predicted high-load threshold (75th pct of preds)"))
a_hrs = int(get_val("Actual high-load hours"))
p_hrs = int(get_val("Predicted high-load hours"))

add_body(doc,
    "An hour is classified as 'high-load' if its arrival count meets or exceeds the 75th "
    f"percentile of the training period counts, which is {a_thr:.1f} arrivals per hour. "
    "On the predicted side, the 75th percentile of test-set predictions "
    f"({p_thr:.2f} arrivals) is used as the detection threshold, accounting for the fact "
    "that Poisson regression predicts conditional means that are systematically lower than "
    f"raw counts. Out of 8,736 test hours, {a_hrs} were actually high-load "
    f"({a_hrs/8736*100:.1f}%), while the model flagged {p_hrs} as high-load."
)

# High-load detection bar chart
add_heading(doc, "3.9.1 Precision, Recall, and F1 Score", level=3)
add_body(doc,
    f"Figure 13 shows the three classification metrics for high-load detection. The model "
    f"achieved a precision of {prec:.4f}, a recall of {rec:.4f}, and an F1 score of "
    f"{f1:.4f}. Precision of 0.78 means that when the system raises a high-load warning, "
    "it is correct approximately 78% of the time — a high reliability rate that reduces "
    "unnecessary staffing mobilizations. Recall of 0.39 means the system detects approximately "
    "39% of all actual high-load hours, missing roughly six in ten. The F1 score of 0.52 "
    "summarizes the trade-off between these two objectives."
)
add_body(doc,
    "This precision-recall trade-off is a deliberate consequence of the modeling approach. "
    "A Poisson regression predicts the most likely count, not the worst-case count. When a "
    "high-load warning is issued, it is a strong signal — but the system will not raise an "
    "alarm for every busy hour. For a resource-constrained clinic, high precision is often "
    "preferable to high recall: staff respond to fewer but more reliable warnings, avoiding "
    "alert fatigue. If the clinic's operational priority shifts toward missing fewer busy hours "
    "at the cost of more false alarms, the detection threshold can be lowered."
)
add_figure(doc, "high_load_detection.png",
           "Figure 13. Precision, recall, and F1 score for high-load hour detection (threshold: 75th percentile of training counts).")

# Confusion matrix
add_heading(doc, "3.9.2 Confusion Matrix", level=3)
add_body(doc,
    "Figure 14 shows the confusion matrix for the high-load classification task. The four "
    "cells represent: True Negatives (TN) — normal hours correctly identified as normal; "
    "False Positives (FP) — normal hours incorrectly flagged as high-load; False Negatives "
    "(FN) — high-load hours the model missed; and True Positives (TP) — high-load hours "
    "correctly detected. The large TN count confirms that the model is conservative, correctly "
    "classifying the majority of normal hours. The larger FN relative to FP reflects the high-"
    "precision, lower-recall behavior described above."
)
add_body(doc,
    "In clinical terms: False Positives cause unnecessary preparation — extra staff called in "
    "for a shift that turns out to be manageable. False Negatives cause under-preparation — "
    "a genuinely busy period arrives without the staff or resources to handle it. The current "
    "configuration minimizes False Positives, which protects against resource waste and staff "
    "fatigue from over-mobilization. Facilities with higher tolerance for over-preparation "
    "in exchange for catching more busy periods should consider reducing the detection threshold."
)
add_figure(doc, "confusion_matrix.png",
           "Figure 14. Confusion matrix for high-load hour detection on the 2017 test set.")

doc.add_page_break()

# ══════════════════════════════════════════════════════════════════════════════
# SECTION 4 — SUMMARY TABLE
# ══════════════════════════════════════════════════════════════════════════════
add_heading(doc, "4. Summary of Results", level=1)
add_body(doc,
    "Table 1 consolidates all evaluation results reported in this chapter. The model was "
    "trained using LightGBM with a Poisson objective on 2014–2015 data and evaluated on "
    "the 2017 test year. All metrics align with those specified in the study's methodology."
)

doc.add_paragraph("Table 1. Complete evaluation results for the BalikBisita LightGBM forecasting model.",
                  style="Normal").alignment = WD_ALIGN_PARAGRAPH.CENTER

# Define table rows
table_rows = [
    # (Section header, metric, value, notes)
    ("DATASET & MODEL",    "Dataset",                "Real ED arrivals 2014–2017",    ""),
    ("",                   "Model type",             "LightGBM – Poisson objective",  ""),
    ("",                   "Training period",        "2014–2015  (17,184 hours)",      ""),
    ("",                   "Validation period",      "2016  (8,784 hours)",            ""),
    ("",                   "Test period",            "2017  (8,736 hours)",            ""),
    ("HYPERPARAMETERS",    "Learning rate",          str(get_val("Best learning_rate")), ""),
    ("",                   "Number of leaves",       str(get_val("Best num_leaves")),    ""),
    ("",                   "Min child samples",      str(get_val("Best min_child_samples")), ""),
    ("",                   "Number of trees",        str(get_val("Number of trees")),    ""),
    ("SPLIT MAE",          "Train MAE",              f"{float(get_val('Train MAE')):.4f} arrivals/hr",  ""),
    ("",                   "Validation MAE",         f"{float(get_val('Validation MAE')):.4f} arrivals/hr", ""),
    ("",                   "Test MAE",               f"{float(get_val('Test MAE')):.4f} arrivals/hr",   "Primary metric"),
    ("",                   "Test RMSE",              f"{float(get_val('Test RMSE')):.4f} arrivals/hr",  ""),
    ("PEAK-HOUR MAE",      "Peak-hour MAE (10:00–19:00)", f"{float(get_val('Peak-hour MAE (10:00-19:00)')):.4f} arrivals/hr", ""),
    ("",                   "Off-peak MAE",           f"{float(get_val('Off-peak MAE')):.4f} arrivals/hr", ""),
    ("SKILL SCORE",        "Naïve baseline MAE",     f"{float(get_val('Seasonal-naïve baseline MAE')):.4f} arrivals/hr", ""),
    ("",                   "Skill score",            f"{float(get_val('Skill score vs naïve baseline'))*100:.1f}% improvement", "vs. seasonal-naïve"),
    ("HIGH-LOAD DETECTION","Actual threshold",       f"{float(get_val('Actual high-load threshold (75th pct of training)')):.1f} arrivals/hr", "75th pct of training"),
    ("",                   "Actual high-load hours", f"{int(get_val('Actual high-load hours'))} / 8,736", ""),
    ("",                   "Precision",              f"{float(get_val('High-load Precision')):.4f}",    ""),
    ("",                   "Recall",                 f"{float(get_val('High-load Recall')):.4f}",       ""),
    ("",                   "F1 Score",               f"{float(get_val('High-load F1')):.4f}",           ""),
]

tbl = doc.add_table(rows=1, cols=4)
tbl.style = "Table Grid"
tbl.autofit = False
col_widths = [Inches(1.4), Inches(2.2), Inches(1.6), Inches(1.1)]
for i, w in enumerate(col_widths):
    for cell in tbl.columns[i].cells:
        cell.width = w

# Header row
hdr = tbl.rows[0]
shade_row(hdr, "1565C0")
for cell, text in zip(hdr.cells, ["Category", "Metric", "Value", "Notes"]):
    p = cell.paragraphs[0]
    run = p.add_run(text)
    run.bold = True
    run.font.color.rgb = RGBColor(0xFF, 0xFF, 0xFF)
    run.font.size = Pt(10)
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    cell.vertical_alignment = WD_ALIGN_VERTICAL.CENTER

current_section = ""
for category, metric, value, notes in table_rows:
    row = tbl.add_row()
    for idx, cell in enumerate(row.cells):
        cell.width = col_widths[idx] if idx < len(col_widths) else Inches(1)

    # Section header cell
    cat_cell = row.cells[0]
    if category and category != current_section:
        current_section = category
        shade_row(row, "D6E4F7")
        p = cat_cell.paragraphs[0]
        run = p.add_run(category)
        run.bold = True
        run.font.size = Pt(9)
        p.alignment = WD_ALIGN_PARAGRAPH.LEFT
    else:
        cat_cell.paragraphs[0].add_run("")

    # Metric
    p2 = row.cells[1].paragraphs[0]
    p2.add_run(str(metric)).font.size = Pt(10)

    # Value
    p3 = row.cells[2].paragraphs[0]
    r3 = p3.add_run(str(value))
    r3.font.size = Pt(10)
    r3.bold = (metric in ["Test MAE", "F1 Score", "Skill score"])
    p3.alignment = WD_ALIGN_PARAGRAPH.CENTER

    # Notes
    p4 = row.cells[3].paragraphs[0]
    r4 = p4.add_run(str(notes))
    r4.font.size = Pt(9)
    r4.font.italic = True

doc.add_paragraph()
add_body(doc,
    "Overall, the results demonstrate that the LightGBM Poisson model is a viable forecasting "
    "component for the BalikBisita system. It consistently outperforms the seasonal-naïve baseline "
    "by 25.8%, produces unbiased average predictions, and provides reliable high-load warnings "
    "with 78% precision. The primary limitation is recall on high-load detection (39%), which "
    "reflects the inherent smoothing behavior of mean-regression models. This trade-off is "
    "acceptable for the system's purpose: providing daily staffing guidance rather than emergency "
    "alerts. Future work could improve recall by augmenting the model with an anomaly-detection "
    "layer that specifically targets extreme-count hours."
)

# ── Save ──────────────────────────────────────────────────────────────────────
doc.save(DOCX_OUT)
print(f"\nWord document saved to:\n  {DOCX_OUT}")
