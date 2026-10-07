"""
Lunar Survey Backend API
"""

import os
import math
import base64
import json
from pathlib import Path

import cv2
import numpy as np
import pandas as pd
import xmltodict

from flask import Flask, request, jsonify, Response
from flask_cors import CORS
from ultralytics import YOLO


# ============================================================
# PATHS
# ============================================================

BASE_DIR = Path(__file__).resolve().parent

MODEL_DIR = BASE_DIR / "models"
METADATA_DIR = BASE_DIR / "metadata"
UPLOAD_FOLDER = BASE_DIR / "uploads"

UPLOAD_FOLDER.mkdir(
    parents=True,
    exist_ok=True
)


# ============================================================
# MODEL PATH
# ============================================================

def resolve_model_path(*candidates):

    for candidate in candidates:

        path = MODEL_DIR / candidate

        if path.exists():
            return path

    normalized_candidates = {
        candidate.lower().replace(" ", "")
        for candidate in candidates
    }

    if MODEL_DIR.exists():

        for path in MODEL_DIR.iterdir():

            if path.is_file():

                normalized_name = (
                    path.name.lower().replace(" ", "")
                )

                if normalized_name in normalized_candidates:
                    return path

    return MODEL_DIR / candidates[0]


CRATER_MODEL_PATH = resolve_model_path(
    "crater_best.pt"
)

BOULDER_MODEL_PATH = resolve_model_path(
    "boulder_best.pt",
    "boulder_best .pt"
)

XML_PATH = (
    METADATA_DIR /
    "lunar_metadata.xml"
)


# ============================================================
# SAFE JSON VALUE CONVERTER
# ============================================================

def clean_json_values(value):

    # Dictionary
    if isinstance(value, dict):

        return {
            str(key): clean_json_values(val)
            for key, val in value.items()
        }

    # List / tuple
    if isinstance(value, (list, tuple)):

        return [
            clean_json_values(item)
            for item in value
        ]

    # None
    if value is None:
        return None

    # NumPy integer
    if isinstance(value, np.integer):
        return int(value)

    # NumPy floating point
    if isinstance(value, np.floating):

        value = float(value)

        if not math.isfinite(value):
            return None

        return value

    # Python float
    if isinstance(value, float):

        if not math.isfinite(value):
            return None

        return value

    # Pandas missing value
    if value is pd.NA:
        return None

    try:

        result = pd.isna(value)

        if isinstance(
            result,
            (bool, np.bool_)
        ):

            if result:
                return None

    except (TypeError, ValueError):

        pass

    return value


# ============================================================
# METADATA
# ============================================================

def find_key_recursively(
    element,
    target_key
):

    if isinstance(element, dict):

        if target_key in element:
            return element[target_key]

        for value in element.values():

            result = find_key_recursively(
                value,
                target_key
            )

            if result is not None:
                return result

    elif isinstance(element, list):

        for item in element:

            result = find_key_recursively(
                item,
                target_key
            )

            if result is not None:
                return result

    return None


def extract_pixel_resolution(xml_path):

    try:

        with open(
            xml_path,
            "r",
            encoding="utf-8"
        ) as f:

            data_dict = xmltodict.parse(
                f.read()
            )

        obj = find_key_recursively(
            data_dict,
            "isda:pixel_resolution"
        )

        if (
            isinstance(obj, dict)
            and "#text" in obj
        ):

            value = float(
                obj["#text"]
            )

            if math.isfinite(value):
                return value

        print(
            "Warning: pixel resolution not found."
        )

        return None

    except Exception as e:

        print(
            "Pixel resolution error:",
            repr(e)
        )

        return None


def extract_sun_elevation(xml_path):

    try:

        with open(
            xml_path,
            "r",
            encoding="utf-8"
        ) as f:

            data_dict = xmltodict.parse(
                f.read()
            )

        elevation_obj = find_key_recursively(
            data_dict,
            "isda:sun_elevation"
        )

        if (
            isinstance(elevation_obj, dict)
            and "#text" in elevation_obj
        ):

            value = float(
                elevation_obj["#text"]
            )

            if math.isfinite(value):
                return value

        incidence_obj = find_key_recursively(
            data_dict,
            "isda:solar_incidence"
        )

        if (
            isinstance(incidence_obj, dict)
            and "#text" in incidence_obj
        ):

            incidence = float(
                incidence_obj["#text"]
            )

            value = 90.0 - incidence

            if math.isfinite(value):
                return value

        print(
            "Warning: sun elevation not found."
        )

        return None

    except Exception as e:

        print(
            "Sun elevation error:",
            repr(e)
        )

        return None


# ============================================================
# SHADOW MEASUREMENT
# ============================================================

def measure_shadow_length(crop_image):

    if crop_image.size == 0:
        return 0.0

    gray = cv2.cvtColor(
        crop_image,
        cv2.COLOR_BGR2GRAY
    )

    blurred = cv2.GaussianBlur(
        gray,
        (5, 5),
        0
    )

    shadow_mask = cv2.adaptiveThreshold(
        blurred,
        255,
        cv2.ADAPTIVE_THRESH_MEAN_C,
        cv2.THRESH_BINARY_INV,
        21,
        5
    )

    contours, _ = cv2.findContours(
        shadow_mask,
        cv2.RETR_EXTERNAL,
        cv2.CHAIN_APPROX_SIMPLE
    )

    if not contours:
        return 0.0

    largest_contour = max(
        contours,
        key=cv2.contourArea
    )

    rect = cv2.minAreaRect(
        largest_contour
    )

    width, height = rect[1]

    value = max(
        float(width),
        float(height)
    )

    if not math.isfinite(value):
        return 0.0

    return value


# ============================================================
# ANALYSIS
# ============================================================

def analyze_and_display_results(
    crater_model,
    boulder_model,
    image_path,
    metadata_path
):

    image = cv2.imread(
        str(image_path)
    )

    if image is None:

        print(
            "Could not read image."
        )

        return None, None, []

    sun_elevation = extract_sun_elevation(
        metadata_path
    )

    image_scale = extract_pixel_resolution(
        metadata_path
    )

    if (
        sun_elevation is None
        or image_scale is None
    ):

        return None, None, []

    print(
        f"Scale: {image_scale} m/pixel"
    )

    print(
        f"Sun Elevation: "
        f"{sun_elevation:.2f}°"
    )

    # ========================================================
    # YOLO
    # ========================================================

    crater_results = crater_model.predict(
        str(image_path),
        verbose=False
    )[0]

    boulder_results = boulder_model.predict(
        str(image_path),
        verbose=False
    )[0]

    results_list = []

    # ========================================================
    # CRATERS
    # ========================================================

    for box in crater_results.boxes:

        x1, y1, x2, y2 = map(
            int,
            box.xyxy[0].tolist()
        )

        crop = image[
            y1:y2,
            x1:x2
        ]

        shadow_pixels = measure_shadow_length(
            crop
        )

        diameter_meters = (
            (x2 - x1) *
            image_scale
        )

        if shadow_pixels > 5:

            method = "Shadow Measurement"

            depth = (
                shadow_pixels *
                image_scale *
                math.tan(
                    math.radians(
                        sun_elevation
                    )
                )
            )

        else:

            method = "Estimated (D-d Ratio)"

            depth = (
                diameter_meters *
                0.2
            )

        # Safe depth
        try:

            depth = float(depth)

            if not math.isfinite(depth):
                depth = None

        except (
            TypeError,
            ValueError
        ):

            depth = None

        # Safe confidence
        try:

            confidence = float(
                box.conf[0].item()
            )

            if not math.isfinite(
                confidence
            ):

                confidence = None

        except (
            TypeError,
            ValueError,
            IndexError
        ):

            confidence = None

        results_list.append(
            {
                "class": "Crater",
                "confidence": confidence,
                "depth(KM)": depth,
                "height(KM)": None,
                "method": method
            }
        )

    # ========================================================
    # BOULDERS
    # ========================================================

    for box in boulder_results.boxes:

        x1, y1, x2, y2 = map(
            int,
            box.xyxy[0].tolist()
        )

        crop = image[
            y1:y2,
            x1:x2
        ]

        shadow_pixels = measure_shadow_length(
            crop
        )

        width_meters = (
            (x2 - x1) *
            image_scale
        )

        if shadow_pixels > 3:

            method = "Shadow Measurement"

            height = (
                shadow_pixels *
                image_scale *
                math.tan(
                    math.radians(
                        sun_elevation
                    )
                )
            )

        else:

            method = "Estimated (H-W Ratio)"

            height = (
                width_meters *
                0.5
            )

        # Safe height
        try:

            height = float(height)

            if not math.isfinite(height):
                height = None

        except (
            TypeError,
            ValueError
        ):

            height = None

        # Safe confidence
        try:

            confidence = float(
                box.conf[0].item()
            )

            if not math.isfinite(
                confidence
            ):

                confidence = None

        except (
            TypeError,
            ValueError,
            IndexError
        ):

            confidence = None

        results_list.append(
            {
                "class": "Boulder",
                "confidence": confidence,
                "depth(KM)": None,
                "height(KM)": height,
                "method": method
            }
        )

    # ========================================================
    # DATAFRAME
    # ========================================================

    results_df = pd.DataFrame(
        results_list
    )

    # ========================================================
    # ANNOTATED IMAGE
    # ========================================================

    display_image = image.copy()

    all_boxes = (
        crater_results.boxes.xyxy.tolist()
        +
        boulder_results.boxes.xyxy.tolist()
    )

    for i, row in results_df.iterrows():

        x1, y1, x2, y2 = map(
            int,
            all_boxes[i]
        )

        if row["class"] == "Crater":

            color = (0, 255, 0)

            value = row["depth(KM)"]

            if (
                value is not None
                and not pd.isna(value)
                and math.isfinite(
                    float(value)
                )
            ):

                text = (
                    f"Crater #{i+1} | "
                    f"Depth: "
                    f"{float(value):.2f}m "
                    f"({row['method']})"
                )

            else:

                text = (
                    f"Crater #{i+1} | "
                    f"Depth: N/A "
                    f"({row['method']})"
                )

        else:

            color = (255, 200, 0)

            value = row["height(KM)"]

            if (
                value is not None
                and not pd.isna(value)
                and math.isfinite(
                    float(value)
                )
            ):

                text = (
                    f"Boulder #{i+1} | "
                    f"Height: "
                    f"{float(value):.2f}m "
                    f"({row['method']})"
                )

            else:

                text = (
                    f"Boulder #{i+1} | "
                    f"Height: N/A "
                    f"({row['method']})"
                )

        cv2.rectangle(
            display_image,
            (x1, y1),
            (x2, y2),
            color,
            2
        )

        cv2.putText(
            display_image,
            text,
            (
                x1,
                max(y1 - 10, 20)
            ),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.8,
            color,
            2
        )

    return (
        results_df,
        display_image,
        results_list
    )


# ============================================================
# FLASK
# ============================================================

app = Flask(__name__)

CORS(app)


# ============================================================
# LOAD MODELS
# ============================================================

print(
    "Loading AI models..."
)

if not CRATER_MODEL_PATH.exists():

    raise FileNotFoundError(
        f"Crater model not found: "
        f"{CRATER_MODEL_PATH}"
    )

if not BOULDER_MODEL_PATH.exists():

    raise FileNotFoundError(
        f"Boulder model not found: "
        f"{BOULDER_MODEL_PATH}"
    )

if not XML_PATH.exists():

    raise FileNotFoundError(
        f"Metadata XML not found: "
        f"{XML_PATH}"
    )

crater_model = YOLO(
    str(CRATER_MODEL_PATH)
)

boulder_model = YOLO(
    str(BOULDER_MODEL_PATH)
)

print(
    "AI models loaded successfully."
)


# ============================================================
# ANALYZE API
# ============================================================

@app.route(
    "/analyze",
    methods=["POST"]
)
def analyze_image_endpoint():

    image_path = None

    try:

        # ----------------------------------------------------
        # CHECK IMAGE
        # ----------------------------------------------------

        if "image" not in request.files:

            return jsonify(
                {
                    "error":
                    "Image file is required"
                }
            ), 400

        image_file = request.files["image"]

        if not image_file.filename:

            return jsonify(
                {
                    "error":
                    "No image selected"
                }
            ), 400

        # ----------------------------------------------------
        # SAVE IMAGE
        # ----------------------------------------------------

        filename = Path(
            image_file.filename
        ).name

        image_path = (
            UPLOAD_FOLDER /
            filename
        )

        image_file.save(
            str(image_path)
        )

        print(
            "Image received:",
            filename
        )

        # ----------------------------------------------------
        # ANALYZE
        # ----------------------------------------------------

        (
            results_df,
            annotated_image,
            results_list
        ) = analyze_and_display_results(
            crater_model,
            boulder_model,
            image_path,
            XML_PATH
        )

        if (
            results_df is None
            or annotated_image is None
        ):

            return jsonify(
                {
                    "error":
                    "Analysis failed."
                }
            ), 500

        # ----------------------------------------------------
        # ENCODE IMAGE
        # ----------------------------------------------------

        success, buffer = cv2.imencode(
            ".jpg",
            annotated_image
        )

        if not success:

            return jsonify(
                {
                    "error":
                    "Failed to encode image."
                }
            ), 500

        image_base64 = (
            base64.b64encode(
                buffer
            ).decode("utf-8")
        )

        # ====================================================
        # IMPORTANT:
        # USE results_list DIRECTLY
        # DO NOT USE results_df.to_dict()
        # ====================================================

        results_json = clean_json_values(
            results_list
        )

        # ====================================================
        # FINAL SAFETY CHECK
        # ====================================================

        response_data = {
            "results_table": results_json,
            "annotated_image":
                "data:image/jpeg;base64,"
                + image_base64
        }

        response_data = clean_json_values(
            response_data
        )

        # ====================================================
        # STRICT JSON
        # ====================================================

        json_text = json.dumps(
            response_data,
            allow_nan=False,
            ensure_ascii=False
        )

        print(
            "JSON response created successfully."
        )

        print(
            "NaN-safe response confirmed."
        )

        return Response(
            json_text,
            status=200,
            mimetype="application/json"
        )

    except Exception as e:

        print(
            "Analysis error:",
            repr(e)
        )

        return jsonify(
            {
                "error":
                str(e)
            }
        ), 500

    finally:

        # ----------------------------------------------------
        # DELETE TEMP IMAGE
        # ----------------------------------------------------

        if (
            image_path is not None
            and image_path.exists()
        ):

            try:

                image_path.unlink()

            except Exception as cleanup_error:

                print(
                    "Cleanup error:",
                    cleanup_error
                )


# ============================================================
# HEALTH CHECK
# ============================================================

@app.route(
    "/",
    methods=["GET"]
)
def health_check():

    return jsonify(
        {
            "status":
            "running",

            "service":
            "Lunar Terrain AI Backend",

            "version":
            "NAN_FIX_2026"
        }
    )


# ============================================================
# START SERVER
# ============================================================

if __name__ == "__main__":

    print(
        "Starting Lunar Terrain AI backend..."
    )

    print(
        "NAN FIX VERSION: 2026"
    )

    app.run(
        host="0.0.0.0",
        port=int(
            os.environ.get(
                "PORT",
                5001
            )
        ),
        debug=False
    )