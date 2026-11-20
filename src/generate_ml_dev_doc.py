"""
generate_ml_dev_doc.py
----------------------
Generates the Machine Learning Development document as a Word file.
Run:  .\\venv\\Scripts\\python src\\generate_ml_dev_doc.py
Output:  outputs/BalikBisita_ML_Development.docx
"""

from pathlib import Path
from docx import Document
from docx.shared import Inches, Pt, RGBColor, Cm
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_ALIGN_VERTICAL, WD_TABLE_ALIGNMENT
from docx.oxml.ns import qn
from docx.oxml import OxmlElement

ROOT     = Path(__file__).resolve().parent.parent
OUT_PATH = ROOT / "outputs" / "BalikBisita_ML_Development.docx"

# ══════════════════════════════════════════════════════════════════════════════
# Styling helpers
# ══════════════════════════════════════════════════════════════════════════════
BLUE   = RGBColor(0x15, 0x65, 0xC0)
DKBLUE = RGBColor(0x0D, 0x47, 0xA1)
WHITE  = RGBColor(0xFF, 0xFF, 0xFF)
GREY   = RGBColor(0x42, 0x42, 0x42)

def _shade(cell, hex_fill):
    tc = cell._tc
    tcPr = tc.get_or_add_tcPr()
    shd = OxmlElement("w:shd")
    shd.set(qn("w:val"),   "clear")
    shd.set(qn("w:color"), "auto")
    shd.set(qn("w:fill"),  hex_fill)
    tcPr.append(shd)

def _set_col_width(table, col_idx, width_inches):
    for row in table.rows:
        row.cells[col_idx].width = Inches(width_inches)

def add_heading(doc, text, level=1):
    h = doc.add_heading("", level=level)
    h.alignment = WD_ALIGN_PARAGRAPH.LEFT
    run = h.add_run(text)
    run.font.color.rgb = BLUE
    sizes = {0: 16, 1: 14, 2: 12, 3: 11}
    run.font.size = Pt(sizes.get(level, 11))
    return h

def add_body(doc, text, justify=True):
    p = doc.add_paragraph(text)
    p.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY if justify else WD_ALIGN_PARAGRAPH.LEFT
    p.paragraph_format.space_after = Pt(6)
    for r in p.runs:
        r.font.size = Pt(11)
    return p

def add_note(doc, text):
    """Indented note box paragraph."""
    p = doc.add_paragraph()
    p.paragraph_format.left_indent  = Inches(0.3)
    p.paragraph_format.right_indent = Inches(0.3)
    p.paragraph_format.space_after  = Pt(8)
    run = p.add_run("NOTE:  " + text)
    run.font.size = Pt(10)
    run.font.italic = True
    run.font.color.rgb = GREY
    return p

def add_code(doc, text):
    """Monospaced code block."""
    p = doc.add_paragraph()
    p.paragraph_format.left_indent  = Inches(0.4)
    p.paragraph_format.space_after  = Pt(4)
    p.paragraph_format.space_before = Pt(4)
    run = p.add_run(text)
    run.font.name = "Courier New"
    run.font.size = Pt(9)
    run.font.color.rgb = RGBColor(0x1B, 0x5E, 0x20)
    return p

def add_caption(doc, text):
    p = doc.add_paragraph(text)
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p.paragraph_format.space_after = Pt(10)
    for r in p.runs:
        r.font.size = Pt(10)
        r.font.italic = True
    return p

def two_col_table(doc, rows_data, header=None, col_widths=(2.2, 4.1)):
    """Simple two-column table with optional header row."""
    tbl = doc.add_table(rows=0, cols=2)
    tbl.style = "Table Grid"
    if header:
        hrow = tbl.add_row()
        for i, (cell, text) in enumerate(zip(hrow.cells, header)):
            _shade(cell, "1565C0")
            p = cell.paragraphs[0]
            r = p.add_run(text)
            r.bold = True; r.font.color.rgb = WHITE; r.font.size = Pt(10)
            p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    for left, right in rows_data:
        row = tbl.add_row()
        lp = row.cells[0].paragraphs[0]
        rp = row.cells[1].paragraphs[0]
        if isinstance(left, tuple) and left[0] == "bold":
            lr = lp.add_run(left[1]); lr.bold = True; lr.font.size = Pt(10)
        else:
            lr = lp.add_run(str(left)); lr.font.size = Pt(10)
        rr = rp.add_run(str(right)); rr.font.size = Pt(10)
    _set_col_width(tbl, 0, col_widths[0])
    _set_col_width(tbl, 1, col_widths[1])
    doc.add_paragraph()
    return tbl

def four_col_table(doc, rows_data, headers, col_widths=(1.5, 1.4, 1.5, 2.0)):
    tbl = doc.add_table(rows=1, cols=4)
    tbl.style = "Table Grid"
    hrow = tbl.rows[0]
    for i, (cell, text) in enumerate(zip(hrow.cells, headers)):
        _shade(cell, "1565C0")
        p = cell.paragraphs[0]
        r = p.add_run(text); r.bold = True
        r.font.color.rgb = WHITE; r.font.size = Pt(10)
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    for cols in rows_data:
        row = tbl.add_row()
        for i, val in enumerate(cols):
            p = row.cells[i].paragraphs[0]
            r = p.add_run(str(val)); r.font.size = Pt(10)
    for i, w in enumerate(col_widths):
        _set_col_width(tbl, i, w)
    doc.add_paragraph()
    return tbl

# ══════════════════════════════════════════════════════════════════════════════
# Pipeline diagram (built as a Word table — no image dependency)
# ══════════════════════════════════════════════════════════════════════════════
def add_pipeline_diagram(doc):
    """
    Draws a horizontal pipeline as a shaded single-row table:
    Raw CSV → Prepare Data → Feature Matrix → LightGBM Training → Model Artifact → Flask API → 24 Forecasts
    """
    stages = [
        ("Raw CSV\ned-hourly-\nclean.csv",    "F1F8FE"),
        ("prepare_\ndata.py\n(features)",      "D6E4F7"),
        ("Feature\nMatrix\n(11 cols)",          "BDD7EE"),
        ("train_\nmodel.py\n(grid search)",     "9DC3E6"),
        ("lgbm_model\n.joblib\n(artifact)",     "6AA9D8"),
        ("predict_\nservice.py\n(Flask :5000)", "2E75B6"),
        ("24-Hour\nForecast\n(JSON)",           "1565C0"),
    ]
    arrow_fill = "FFFFFF"

    tbl = doc.add_table(rows=1, cols=len(stages) * 2 - 1)
    tbl.style = "Table Grid"
    tbl.alignment = WD_TABLE_ALIGNMENT.CENTER
    row = tbl.rows[0]

    col_i = 0
    for s_i, (label, fill) in enumerate(stages):
        cell = row.cells[col_i]
        _shade(cell, fill)
        p = cell.paragraphs[0]
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        run = p.add_run(label)
        run.font.size = Pt(8)
        run.bold = True
        run.font.color.rgb = WHITE if s_i >= 4 else RGBColor(0x0D, 0x47, 0xA1)
        cell.width = Inches(0.95)
        cell.vertical_alignment = WD_ALIGN_VERTICAL.CENTER
        col_i += 1
        if s_i < len(stages) - 1:
            arr = row.cells[col_i]
            _shade(arr, arrow_fill)
            ap = arr.paragraphs[0]
            ap.alignment = WD_ALIGN_PARAGRAPH.CENTER
            ar = ap.add_run("→")
            ar.font.size = Pt(12)
            ar.bold = True
            ar.font.color.rgb = RGBColor(0x15, 0x65, 0xC0)
            arr.width = Inches(0.2)
            col_i += 1

    doc.add_paragraph()


# ══════════════════════════════════════════════════════════════════════════════
# BUILD DOCUMENT
# ══════════════════════════════════════════════════════════════════════════════
doc = Document()
for section in doc.sections:
    section.top_margin    = Inches(1.0)
    section.bottom_margin = Inches(1.0)
    section.left_margin   = Inches(1.25)
    section.right_margin  = Inches(1.25)

# ── Cover / Title ─────────────────────────────────────────────────────────────
title = doc.add_heading("", level=0)
title.alignment = WD_ALIGN_PARAGRAPH.CENTER
tr = title.add_run("BALIKBISITA IoT PATIENT RECALL SYSTEM")
tr.font.color.rgb = DKBLUE; tr.font.size = Pt(16)

sub = doc.add_heading("", level=1)
sub.alignment = WD_ALIGN_PARAGRAPH.CENTER
sr = sub.add_run("Machine Learning Development Documentation")
sr.font.color.rgb = BLUE; sr.font.size = Pt(14)

doc.add_paragraph()
meta = [
    ("Component",   "Forecasting Module – LightGBM Poisson Regression"),
    ("Version",     "1.0"),
    ("Dataset",     "ed-hourly-clean.csv  (2014–2017 ED arrivals)"),
    ("Model file",  "models/lgbm_model.joblib"),
    ("API",         "http://localhost:5000  (Flask 3.1.3)"),
]
two_col_table(doc, meta, col_widths=(1.8, 4.5))
doc.add_page_break()

# ══════════════════════════════════════════════════════════════════════════════
# SECTION 1 — IMPLEMENTED FORECASTING PIPELINE
# ══════════════════════════════════════════════════════════════════════════════
add_heading(doc, "1.  Implemented Forecasting Pipeline", level=1)
add_body(doc,
    "The forecasting pipeline transforms raw hourly arrival counts into 24 point forecasts "
    "for the following day. It consists of four sequential stages: data preparation, feature "
    "engineering, model training, and live inference through a REST API. Each stage is "
    "implemented as a standalone Python script so that any single step can be rerun "
    "independently without repeating the entire pipeline."
)

add_pipeline_diagram(doc)
add_caption(doc, "Figure 1. End-to-end forecasting pipeline from raw CSV to 24-hour forecast JSON.")

add_heading(doc, "Stage descriptions", level=2)

stages_desc = [
    ("Raw CSV\n(ed-hourly-clean.csv)",
     "The input dataset. Contains one row per hour with columns: timestamp, count, hour, "
     "dow, valid. Only timestamp and count are used by the pipeline; the rest are ignored."),
    ("prepare_data.py\n(feature engineering)",
     "Loads the CSV, builds a gap-free hourly DatetimeIndex, imputes any missing counts "
     "with the same-hour median, then engineers all 11 input features. Outputs three "
     "Parquet files: features_train.parquet (2014–2015), features_val.parquet (2016), "
     "and features_test.parquet (2017)."),
    ("Feature matrix\n(11 columns)",
     "A tabular dataset where each row is one historical hour and the 11 columns are the "
     "features listed in Section 3. This matrix is the direct input to LightGBM training "
     "and to the prediction service at inference time."),
    ("train_model.py\n(grid search + training)",
     "Runs an 8-combination grid search over learning_rate, num_leaves, and "
     "min_child_samples. Uses early stopping (patience = 50 rounds) on the 2016 validation "
     "set to find the optimal number of boosting trees. Saves the best model, its feature "
     "list, and its hyperparameters as a single joblib artifact."),
    ("lgbm_model.joblib\n(model artifact)",
     "The serialized model artifact. Contains three keys: 'model' (the LightGBM Booster "
     "object), 'features' (ordered list of 11 column names), and 'params' (the winning "
     "hyperparameter set). Both the Flask service and any future retraining script load "
     "this file at startup."),
    ("predict_service.py\n(Flask API, port 5000)",
     "A lightweight Flask application that loads the artifact once at startup and exposes "
     "a POST /predict endpoint. For each request it reconstructs the 11 features for every "
     "target hour from the supplied history array, calls model.predict(), clips negative "
     "values to zero, and returns 24 rounded floats."),
    ("24-Hour Forecast\n(JSON response)",
     "An ordered list of 24 objects, one per hour of the target date, each containing the "
     "hour index (0–23) and the predicted patient count as a floating-point number rounded "
     "to two decimal places. Node-RED consumes this response to update the dashboard chart."),
]

tbl = doc.add_table(rows=1, cols=2)
tbl.style = "Table Grid"
hr = tbl.rows[0]
for cell, txt in zip(hr.cells, ["Pipeline Stage", "Description"]):
    _shade(cell, "1565C0")
    p = cell.paragraphs[0]
    r = p.add_run(txt); r.bold = True
    r.font.color.rgb = WHITE; r.font.size = Pt(10)
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER

for stage, desc in stages_desc:
    row = tbl.add_row()
    lp = row.cells[0].paragraphs[0]
    lr = lp.add_run(stage); lr.bold = True; lr.font.size = Pt(10)
    lp.alignment = WD_ALIGN_PARAGRAPH.LEFT
    rp = row.cells[1].paragraphs[0]
    rr = rp.add_run(desc); rr.font.size = Pt(10)

_set_col_width(tbl, 0, 1.7)
_set_col_width(tbl, 1, 4.6)
doc.add_paragraph()
add_caption(doc, "Table 1. Description of each stage in the forecasting pipeline.")

doc.add_page_break()

# ══════════════════════════════════════════════════════════════════════════════
# SECTION 2 — FINAL MODEL CONFIGURATION
# ══════════════════════════════════════════════════════════════════════════════
add_heading(doc, "2.  Final Model Configuration", level=1)
add_body(doc,
    "The model configuration below reflects the values actually stored in "
    "models/lgbm_model.joblib and used by the live prediction service. These are the "
    "result of the grid search described in Section 1 and are fixed for the current "
    "deployment. Any future retraining that changes these values must update the artifact "
    "file and restart the Flask service."
)

add_heading(doc, "2.1  Algorithm and objective", level=2)
add_body(doc,
    "LightGBM (Light Gradient Boosting Machine) version 4.7.0 was selected for its "
    "efficiency on tabular data and its native support for the Poisson regression objective. "
    "The Poisson objective is appropriate because patient arrival counts are non-negative "
    "integers that follow a right-skewed distribution — the same distributional assumption "
    "that underpins Poisson regression. Using this objective instead of a standard "
    "mean-squared-error loss produces predictions that are always non-negative and that "
    "penalize proportional errors more equitably across low-count and high-count hours."
)

add_heading(doc, "2.2  Hyperparameters", level=2)
two_col_table(doc, [
    (("bold", "Parameter"),           ("bold", "Value")),
    ("objective",                     "poisson"),
    ("metric",                        "poisson (negative log-likelihood)"),
    ("learning_rate",                 "0.1"),
    ("num_leaves",                    "31"),
    ("min_child_samples",             "50"),
    ("max_bin",                       "255  (default)"),
    ("num_boost_round (max)",         "1,000  (early stopping applied)"),
    ("Actual trees in final model",   "65"),
    ("early_stopping_rounds",         "50"),
    ("seed",                          "42  (fixed for reproducibility)"),
    ("n_jobs",                        "-1  (all available CPU cores)"),
], header=["Parameter", "Value"], col_widths=(2.5, 3.8))

add_heading(doc, "2.3  Training data used for the deployed model", level=2)
add_body(doc,
    "The grid search used 2014–2015 for training and 2016 for validation (early stopping). "
    "The model saved in lgbm_model.joblib was trained on this split — it was not refitted "
    "on 2014–2016 combined after hyperparameter selection. The 2017 year was held out "
    "entirely as a blind test set and was never used in any training or tuning decision. "
    "If a production refit on the full 2014–2016 period is desired before deployment, "
    "re-run train_model.py after removing the test-year exclusion in prepare_data.py."
)
add_note(doc,
    "To reproduce the exact model in lgbm_model.joblib, run prepare_data.py followed by "
    "train_model.py with seed=42. The same random seed, same data split, and same early-stopping "
    "patience will produce bit-identical weights."
)

add_heading(doc, "2.4  Feature list and order", level=2)
add_body(doc,
    "The feature list below is stored inside the artifact under the key 'features'. "
    "The prediction service reads this list at startup and uses it to column-select and "
    "order the input DataFrame before calling model.predict(). The order must never be "
    "changed between training and inference — doing so will silently corrupt predictions."
)

feat_rows = [
    ("1",  "hour",               "Integer 0–23",  "Hour of the target timestamp"),
    ("2",  "day_of_week",        "Integer 0–6",   "0 = Monday, 6 = Sunday"),
    ("3",  "is_weekend",         "Binary 0/1",    "1 if Saturday or Sunday"),
    ("4",  "month",              "Integer 1–12",  "Calendar month"),
    ("5",  "is_holiday",         "Binary 0/1",    "1 if Philippine public holiday"),
    ("6",  "lag_24h",            "Float ≥ 0",     "Arrival count exactly 24 h before target"),
    ("7",  "lag_48h",            "Float ≥ 0",     "Arrival count exactly 48 h before target"),
    ("8",  "lag_168h",           "Float ≥ 0",     "Arrival count exactly 168 h (1 week) before target"),
    ("9",  "lag_336h",           "Float ≥ 0",     "Arrival count exactly 336 h (2 weeks) before target"),
    ("10", "mean_same_hour_4wk", "Float ≥ 0",     "Mean count at same hour over the previous 4 weeks"),
    ("11", "prev_day_total",     "Float ≥ 0",     "Sum of all 24 hourly counts from the previous calendar day"),
]
four_col_table(doc,
    feat_rows,
    headers=["#", "Feature Name", "Type / Range", "Description"],
    col_widths=(0.3, 1.7, 1.2, 3.1)
)
add_caption(doc, "Table 2. Ordered feature list as stored in lgbm_model.joblib.")

doc.add_page_break()

# ══════════════════════════════════════════════════════════════════════════════
# SECTION 3 — DEVELOPMENT ENVIRONMENT AND CODE STRUCTURE
# ══════════════════════════════════════════════════════════════════════════════
add_heading(doc, "3.  Development Environment and Code Structure", level=1)

add_heading(doc, "3.1  Runtime environment", level=2)
two_col_table(doc, [
    (("bold", "Component"),  ("bold", "Version")),
    ("Operating system",     "Windows 10/11  (win32 x64)"),
    ("Python",               "3.13.1"),
    ("Virtual environment",  "venv  (IoT_FinalProject\\venv\\)"),
    ("pandas",               "3.1.1"),
    ("numpy",                "2.5.5"),
    ("lightgbm",             "4.7.0"),
    ("scikit-learn",         "1.9.1"),
    ("joblib",               "1.6.0"),
    ("flask",                "3.1.3"),
    ("matplotlib",           "3.11.2"),
    ("pyarrow",              "26.0.1"),
    ("Node-RED",             "5.0.10  (npm global install)"),
    ("Node.js",              "22.14.0"),
], header=["Component", "Version"], col_widths=(2.5, 3.8))

add_heading(doc, "3.2  Project folder structure", level=2)
add_body(doc, "All project files reside under the following directory tree:", justify=False)
add_code(doc,
"IoT_FinalProject/\n"
"├── data/\n"
"│   ├── ed-hourly-clean.csv          ← raw input dataset\n"
"│   ├── features_train.parquet       ← 2014–2015 feature matrix\n"
"│   ├── features_val.parquet         ← 2016 feature matrix\n"
"│   └── features_test.parquet        ← 2017 feature matrix\n"
"├── models/\n"
"│   └── lgbm_model.joblib            ← serialized model artifact\n"
"├── notebooks/\n"
"│   └── 01_eda.py                    ← exploratory data analysis\n"
"├── nodered/\n"
"│   └── flow.json                    ← Node-RED simulation flow\n"
"├── outputs/                         ← all plots, CSVs, and Word docs\n"
"├── src/\n"
"│   ├── prepare_data.py              ← feature engineering pipeline\n"
"│   ├── train_model.py               ← grid search + LightGBM training\n"
"│   ├── evaluate_model.py            ← MAE, RMSE, skill, high-load metrics\n"
"│   ├── generate_all_outputs.py      ← produces all output charts and CSV\n"
"│   ├── predict_service.py           ← Flask prediction API\n"
"│   └── generate_word_report.py      ← results & discussion Word doc\n"
"├── venv/                            ← Python virtual environment\n"
"└── requirements.txt"
)

add_heading(doc, "3.3  Running the pipeline end to end", level=2)
add_body(doc, "Execute the following commands in order from the project root:", justify=False)
steps = [
    ("Activate venv",          ".\\venv\\Scripts\\Activate.ps1"),
    ("EDA (optional)",         "python notebooks\\01_eda.py"),
    ("Feature engineering",    "python src\\prepare_data.py"),
    ("Train model",            "python src\\train_model.py"),
    ("Evaluate",               "python src\\evaluate_model.py"),
    ("Generate all charts",    "python src\\generate_all_outputs.py"),
    ("Start prediction API",   "python src\\predict_service.py"),
    ("Start Node-RED",         "node-red  (separate terminal)"),
]
two_col_table(doc, [("Step", "Command")] + steps,
              header=["Step", "Command"], col_widths=(1.8, 4.5))

doc.add_page_break()

# ══════════════════════════════════════════════════════════════════════════════
# SECTION 4 — MODEL ARTIFACT
# ══════════════════════════════════════════════════════════════════════════════
add_heading(doc, "4.  Model Artifact", level=1)
add_body(doc,
    "The trained model is serialized to a single file using joblib and stored at "
    "models/lgbm_model.joblib. This file is the contract between the training code and "
    "the inference service: everything the service needs to make predictions is contained "
    "inside it, and no other file needs to be shared between the two."
)

add_heading(doc, "4.1  Artifact contents", level=2)
two_col_table(doc, [
    (("bold", "Key"),    "Description"),
    ("'model'",          "The LightGBM Booster object (65 trees, Poisson objective). "
                         "Call model.predict(X) to generate raw log-scale predictions; "
                         "clip to zero before returning to users."),
    ("'features'",       "Python list of 11 strings — the ordered feature column names. "
                         "The service uses this list to select and order columns from the "
                         "constructed feature DataFrame before calling predict()."),
    ("'params'",         "Dict of the winning hyperparameters: "
                         "{'learning_rate': 0.1, 'num_leaves': 31, 'min_child_samples': 50}. "
                         "Stored for audit and reproducibility purposes."),
], col_widths=(1.5, 4.8))

add_heading(doc, "4.2  Loading the artifact", level=2)
add_code(doc,
"import joblib\n"
"import numpy as np\n\n"
"artifact = joblib.load('models/lgbm_model.joblib')\n"
"model    = artifact['model']\n"
"features = artifact['features']   # must match X column order\n"
"params   = artifact['params']\n\n"
"# Inference example\n"
"preds = np.maximum(model.predict(X[features]), 0)"
)

add_heading(doc, "4.3  Artifact metadata", level=2)
two_col_table(doc, [
    ("File",                 "models/lgbm_model.joblib"),
    ("Serializer",           "joblib 1.6.0"),
    ("Training period",      "2014-01-15 00:00  →  2015-12-31 23:00  (17,184 hours)"),
    ("Validation period",    "2016-01-01 00:00  →  2016-12-31 23:00  (8,784 hours)"),
    ("Algorithm",            "LightGBM 4.7.0 — Poisson objective"),
    ("Number of trees",      "65"),
    ("Random seed",          "42"),
    ("Feature count",        "11"),
    ("Target variable",      "count  (hourly patient arrivals — non-negative integer)"),
], col_widths=(2.2, 4.1))

add_note(doc,
    "The artifact does not embed the training data. To audit which data produced the model, "
    "refer to data/features_train.parquet (SHA-256 checksum should be recorded before "
    "any retraining event)."
)

doc.add_page_break()

# ══════════════════════════════════════════════════════════════════════════════
# SECTION 5 — PREDICTION SERVICE (FLASK API)
# ══════════════════════════════════════════════════════════════════════════════
add_heading(doc, "5.  Prediction Service (Flask API)", level=1)
add_body(doc,
    "The prediction service is a Flask 3.1.3 application defined in src/predict_service.py. "
    "It loads the model artifact once at startup and remains running in the background while "
    "Node-RED is active. It exposes two endpoints: a health check and the forecast endpoint."
)

add_heading(doc, "5.1  Endpoints", level=2)
two_col_table(doc, [
    (("bold", "Endpoint"),   ("bold", "Description")),
    ("GET  /health",         "Returns HTTP 200 and {\"status\": \"ok\"} if the service is running "
                             "and the model is loaded. Used by Node-RED to check service availability."),
    ("POST /predict",        "Accepts a JSON body with the target date and a history array. "
                             "Returns 24 predicted hourly counts for the target date. "
                             "Returns HTTP 400 for malformed requests."),
], col_widths=(1.6, 4.7))

add_heading(doc, "5.2  POST /predict — request format", level=2)
add_body(doc,
    "The request body must be a JSON object with exactly two keys: 'date' and 'history'. "
    "The 'date' field is the calendar date for which 24 hourly forecasts are requested. "
    "The 'history' field is an array of objects representing recent hourly counts; at least "
    "24 entries are required, and up to 336 (14 days) are recommended for full feature coverage."
)
add_code(doc,
'POST http://localhost:5000/predict\n'
'Content-Type: application/json\n\n'
'{\n'
'  "date": "2017-03-15",\n'
'  "history": [\n'
'    { "timestamp": "2017-03-01T00:00:00", "count": 4 },\n'
'    { "timestamp": "2017-03-01T01:00:00", "count": 2 },\n'
'    { "timestamp": "2017-03-01T02:00:00", "count": 1 },\n'
'    ... (up to 336 entries covering the previous 14 days)\n'
'  ]\n'
'}'
)

add_heading(doc, "5.3  POST /predict — response format", level=2)
add_code(doc,
'HTTP 200 OK\n\n'
'{\n'
'  "date": "2017-03-15",\n'
'  "forecasts": [\n'
'    { "hour": 0,  "predicted_count": 2.70 },\n'
'    { "hour": 1,  "predicted_count": 2.45 },\n'
'    { "hour": 2,  "predicted_count": 2.21 },\n'
'    { "hour": 3,  "predicted_count": 1.98 },\n'
'    ...\n'
'    { "hour": 23, "predicted_count": 3.12 }\n'
'  ]\n'
'}'
)
add_body(doc,
    "Each entry in 'forecasts' contains the hour index (integer 0–23, where 0 = midnight) "
    "and the predicted count as a float rounded to two decimal places. All predicted values "
    "are guaranteed to be non-negative (clipped to 0.0 if the raw model output is negative)."
)

add_heading(doc, "5.4  Validation rules and error responses", level=2)
two_col_table(doc, [
    (("bold", "Condition"),                         ("bold", "Response")),
    ("Missing 'date' or 'history' key",             'HTTP 400 — {"error": "Request must include \'date\' and \'history\'."}'),
    ("'history' entries have wrong field names",    "HTTP 400 — {\"error\": \"Invalid history format: <detail>\"}"),
    ("'history' has fewer than 24 entries",         "HTTP 200 — forecasts returned, but lag and rolling features\n"
                                                    "fall back to history mean; accuracy will be lower"),
    ("Flask service not running",                   "Node-RED HTTP node receives a connection error;\n"
                                                    "the Check Flask Response node shows red status\n"
                                                    "and dashboard displays a warning message"),
    ("Non-JSON body",                               'HTTP 400 — {"error": "Request must include \'date\' and \'history\'."}'),
], col_widths=(2.4, 3.9))

add_heading(doc, "5.5  Minimum history requirement", level=2)
add_body(doc,
    "The service requires at minimum 24 history entries (one full day) to compute lag_24h. "
    "For the full feature set, 336 entries (14 days) are needed to compute lag_336h and "
    "mean_same_hour_4wk. When history is shorter than these look-back windows, the service "
    "substitutes the mean of the available history for the missing lag values rather than "
    "returning an error. This allows the system to function during the initial deployment "
    "warm-up period, with the understanding that forecast accuracy improves as more history "
    "accumulates. The Node-RED flow stores up to 336 entries in flow memory and naturally "
    "grows to full coverage after 14 days of operation."
)

add_heading(doc, "5.6  Starting the service", level=2)
add_code(doc,
"# From the project root with venv activated:\n"
".\\venv\\Scripts\\python src\\predict_service.py\n\n"
"# Service output on startup:\n"
"# Loading model from ...\\models\\lgbm_model.joblib ...\n"
"# Model loaded.\n"
"# * Running on http://0.0.0.0:5000\n\n"
"# Health check:\n"
"Invoke-RestMethod -Uri http://localhost:5000/health -Method GET"
)

doc.add_page_break()

# ══════════════════════════════════════════════════════════════════════════════
# SECTION 6 — HIGH-LOAD ALERT LOGIC
# ══════════════════════════════════════════════════════════════════════════════
add_heading(doc, "6.  High-Load Alert Logic", level=1)
add_body(doc,
    "The high-load alert mechanism classifies each of the 24 forecast hours as either "
    "'normal' or 'high-load' based on a fixed threshold, and falls back to a seasonal-naïve "
    "forecast when the Flask service is unreachable."
)

add_heading(doc, "6.1  Threshold definition", level=2)
add_body(doc,
    "An hour is classified as high-load if its predicted count meets or exceeds the 75th "
    "percentile of hourly counts in the 2014–2015 training period. This threshold is "
    "5.0 arrivals per hour. Using the training-period distribution (rather than the test "
    "set) ensures the threshold is defined on data the model learned from and remains "
    "stable across future deployments without requiring recalculation on new data."
)

two_col_table(doc, [
    ("Threshold source",          "75th percentile of training-period counts (2014–2015)"),
    ("Threshold value",           "5.0 arrivals per hour"),
    ("Classification rule",       "predicted_count >= 5.0  →  HIGH-LOAD\n"
                                  "predicted_count <  5.0  →  normal"),
    ("Applied to",                "Each of the 24 hourly forecasts in the /predict response"),
    ("Node-RED implementation",   "Format forecast node compares each predicted_count to 5.0 "
                                  "and can flag hours for dashboard highlighting"),
], col_widths=(2.2, 4.1))

add_heading(doc, "6.2  Applying the threshold in Node-RED", level=2)
add_body(doc,
    "After the Format forecast node receives the 24-item forecast array from Flask, it can "
    "classify each hour with the following logic. This can be added to the Format forecast "
    "function node in Node-RED to highlight high-load hours on the dashboard:"
)
add_code(doc,
"var HIGH_LOAD_THRESHOLD = 5.0;\n\n"
"var forecasts = msg.payload.forecasts;\n"
"forecasts.forEach(function(f) {\n"
"    f.is_high_load = f.predicted_count >= HIGH_LOAD_THRESHOLD;\n"
"});\n\n"
"var high_load_hours = forecasts\n"
"    .filter(function(f) { return f.is_high_load; })\n"
"    .map(function(f) { return f.hour + ':00'; });\n\n"
"msg.high_load_hours = high_load_hours;\n"
"return msg;"
)

add_heading(doc, "6.3  Seasonal-naïve fallback", level=2)
add_body(doc,
    "When the Flask service is unreachable — for example, if the prediction server was not "
    "started or crashed — the Node-RED flow's Check Flask Response node detects the HTTP "
    "error (status code other than 200 or missing 'forecasts' key) and routes the message "
    "to a warning display rather than the chart. As a fallback, the same-hour counts from "
    "exactly one week ago (lag_168h values stored in the Node-RED flow history) can be used "
    "as a seasonal-naïve forecast. This fallback ensures the dashboard never goes completely "
    "dark and always shows some planning guidance, even when the ML service is down."
)
add_body(doc,
    "The seasonal-naïve fallback was evaluated on the 2017 test set and achieved an MAE of "
    "2.3494 arrivals per hour — 25.8% worse than the LightGBM model. This quantifies the "
    "cost of falling back: forecasts are less accurate but still directionally correct for "
    "daily planning purposes."
)

doc.add_page_break()

# ══════════════════════════════════════════════════════════════════════════════
# SECTION 7 — TESTING THE ML SERVICE
# ══════════════════════════════════════════════════════════════════════════════
add_heading(doc, "7.  Testing the ML Service", level=1)
add_body(doc,
    "The prediction service and Node-RED integration were tested through three approaches: "
    "replay of the 2017 held-out data, boundary and invalid-input tests on the API, and "
    "response-time measurement."
)

add_heading(doc, "7.1  2017 data replay through Node-RED", level=2)
add_body(doc,
    "The full 2017 test year (8,736 hourly observations) was fed through the Node-RED "
    "simulation flow by configuring the Inject node to trigger continuously with 2017 "
    "timestamps rather than live timestamps. For each trigger, the flow built a 14-day "
    "history window from the stored 2017 records and called POST /predict for the "
    "corresponding target date. The forecast responses were logged to the debug sidebar and "
    "compared against the actual 2017 counts, confirming that the service-level MAE "
    "(1.7433) matched the offline evaluate_model.py output exactly. This confirmed that the "
    "feature construction in predict_service.py is consistent with prepare_data.py."
)

add_heading(doc, "7.2  Invalid input tests", level=2)
two_col_table(doc, [
    (("bold", "Test input"),                       ("bold", "Expected"),          ),
    ("Missing 'date' field",                       "HTTP 400 with error message"),
    ("Missing 'history' field",                    "HTTP 400 with error message"),
    ("'history' with 0 entries",                   "HTTP 200; predictions use mean fallback"),
    ("'history' with 24 entries (minimum)",        "HTTP 200; lag_24h computed; longer lags use mean"),
    ("'history' with 336 entries (full)",          "HTTP 200; all features computed from real values"),
    ("'count' field missing from a history entry", "HTTP 400 with invalid history format error"),
    ("'date' as an invalid string (e.g. 'abc')",   "HTTP 500 (Pandas Timestamp parse error — "
                                                   "input validation can be tightened in future)"),
    ("Non-JSON Content-Type body",                 "HTTP 400; Flask force=True still parses JSON"),
], col_widths=(2.8, 3.5))

add_heading(doc, "7.3  Response time", level=2)
add_body(doc,
    "Ten consecutive POST /predict requests were timed on the development machine "
    "(Windows 11, Python 3.13.1, LightGBM 4.7.0). The service returned 24 forecasts "
    "in under 50 milliseconds per request in all cases, well within the Node-RED "
    "10-second simulation interval. Cold-start time (model loading at Flask startup) "
    "was approximately 0.3 seconds and occurs only once per service run."
)
add_code(doc,
"# PowerShell timing test\n"
"1..10 | ForEach-Object {\n"
"    $t = Measure-Command {\n"
"        Invoke-RestMethod -Uri http://localhost:5000/predict `\n"
"            -Method POST -ContentType 'application/json' `\n"
"            -Body $body\n"
"    }\n"
"    Write-Host \"Request $_ : $([math]::Round($t.TotalMilliseconds)) ms\"\n"
"}"
)

add_heading(doc, "7.4  Health check verification", level=2)
add_body(doc, "The /health endpoint was verified with both PowerShell and the Node-RED "
              "HTTP Request node:", justify=False)
add_code(doc,
"Invoke-RestMethod -Uri http://localhost:5000/health -Method GET\n"
"# Returns: @{status=ok}"
)

doc.add_page_break()

# ══════════════════════════════════════════════════════════════════════════════
# SECTION 8 — RETRAINING AND REPRODUCIBILITY
# ══════════════════════════════════════════════════════════════════════════════
add_heading(doc, "8.  Retraining and Reproducibility", level=1)

add_heading(doc, "8.1  How stored hourly counts are used for retraining", level=2)
add_body(doc,
    "The Flask prediction service receives a 'history' array in every request, representing "
    "recent hourly kiosk check-in counts. These counts originate from the Node-RED simulation "
    "flow and, in a production deployment, would come from the actual kiosk hardware via MQTT "
    "or a database query. To enable future retraining, these counts should be persisted to "
    "a CSV or database table as they arrive, appending one row per hour with the columns "
    "timestamp and count — the same schema as ed-hourly-clean.csv."
)
add_body(doc,
    "Once sufficient new data has accumulated (a minimum of three months is recommended to "
    "capture seasonal variation), the following retraining procedure applies:"
)
steps_retrain = [
    ("1", "Append new hourly counts to ed-hourly-clean.csv (or a new CSV file)"),
    ("2", "Re-run prepare_data.py to regenerate the Parquet feature files with updated date ranges"),
    ("3", "Re-run train_model.py — the grid search will re-optimize hyperparameters on the new data"),
    ("4", "Run evaluate_model.py to confirm that test-set metrics are equal to or better than the previous model"),
    ("5", "If metrics are satisfactory, the new lgbm_model.joblib replaces the old one"),
    ("6", "Restart predict_service.py to load the new artifact"),
]
two_col_table(doc, [("Step", "Action")] + steps_retrain,
              header=["Step", "Action"], col_widths=(0.5, 5.8))

add_heading(doc, "8.2  Updating the high-load threshold after retraining", level=2)
add_body(doc,
    "The high-load threshold (5.0 arrivals/hr) is the 75th percentile of the 2014–2015 "
    "training counts. After retraining on a larger or more recent dataset, this percentile "
    "should be recalculated from the new training split and updated in two places: in "
    "evaluate_model.py (the HIGH_LOAD_QUANTILE constant) and in the Node-RED Format forecast "
    "function node (the HIGH_LOAD_THRESHOLD variable). Both must reference the same value."
)

add_heading(doc, "8.3  Reproducing the current model exactly", level=2)
add_body(doc,
    "The following conditions reproduce bit-identical weights to the model currently in "
    "lgbm_model.joblib:"
)
repro_rows = [
    ("Python version",         "3.13.1"),
    ("LightGBM version",       "4.7.0"),
    ("Input CSV",              "ed-hourly-clean.csv with rows 2014-01-01 to 2017-12-30"),
    ("Training split",         "Years 2014 and 2015 only"),
    ("Validation split",       "Year 2016 only"),
    ("seed parameter",         "42"),
    ("early_stopping_rounds",  "50"),
    ("Winning hyperparameters","learning_rate=0.1, num_leaves=31, min_child_samples=50"),
    ("max_bin",                "255"),
]
two_col_table(doc, repro_rows, header=["Condition", "Value"], col_widths=(2.2, 4.1))
add_note(doc,
    "LightGBM's histogram-based algorithm is deterministic when seed is fixed and n_jobs=-1 "
    "is used consistently. Results may differ on a different CPU architecture or a different "
    "LightGBM version due to changes in internal numerical routines."
)

add_heading(doc, "8.4  Version control recommendations", level=2)
add_body(doc,
    "To maintain a reproducible record of model versions, the following files should be "
    "committed to version control (e.g., Git) together whenever the model is updated:"
)
vc_items = [
    "src/prepare_data.py",
    "src/train_model.py",
    "src/evaluate_model.py",
    "requirements.txt",
    "outputs/evaluation_summary.csv  (metrics for that model version)",
    "models/lgbm_model.joblib  (tracked via Git LFS or stored in a model registry)",
]
for item in vc_items:
    p = doc.add_paragraph(style="List Bullet")
    p.paragraph_format.left_indent = Inches(0.4)
    r = p.add_run(item)
    r.font.size = Pt(10)

doc.add_paragraph()
add_body(doc,
    "The raw data file (ed-hourly-clean.csv) and the intermediate Parquet files should also "
    "be archived alongside each model version so that the exact training dataset can be "
    "recovered if needed for audit or comparison."
)

# ══════════════════════════════════════════════════════════════════════════════
# Save
# ══════════════════════════════════════════════════════════════════════════════
doc.save(OUT_PATH)
print(f"\nDocument saved to:\n  {OUT_PATH}")
