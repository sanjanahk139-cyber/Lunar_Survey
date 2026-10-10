# Lunar Survey

Lunar Survey is a full-stack AI-powered lunar terrain analysis application that helps detect and measure craters and boulders in lunar images. The system combines a React frontend with a Flask backend and YOLO-based object detection models to identify surface features, estimate their dimensions, and present annotated results to the user.

The project is designed for scientific visualization and analysis workflows where users can upload a lunar image, run detection, and inspect both the annotated output and the underlying measurement data.

## Overview

This repository contains:

- A Vite + React frontend for the web interface
- A Flask backend for image processing and AI inference
- YOLO detection models for crater and boulder recognition
- Lunar metadata parsing for image scale and sun elevation
- Automatic shadow-based and ratio-based measurements
- A result dashboard that shows detection counts and measurement tables

## Key Features

- Landing page and analyzer dashboard
- Image upload and preview before analysis
- AI detection of lunar craters and boulders
- Annotated image output with bounding boxes and labels
- Summary statistics by class
- Table of detection results including:
  - object class
  - confidence score
  - height in KM
  - depth in KM
  - measurement method
- Flask API used for upload and analysis processing
- Local backend configuration for reliable development workflow

## Project Structure

```text
Lunar_Survey/
├── .env
├── .gitignore
├── README.md
├── eslint.config.js
├── index.html
├── package-lock.json
├── package.json
├── public/
│   ├── analyzer-background.jpg
│   ├── moon-astronaut-space-background.jpg
│   └── vite.svg
├── src/
│   ├── App.css
│   ├── App.jsx
│   ├── index.css
│   └── main.jsx
├── backend/
│   ├── main.py
│   ├── requirements.txt
│   ├── backend.ipynb
│   ├── metadata/
│   │   └── lunar_metadata.xml
│   ├── models/
│   │   ├── crater_best.pt
│   │   └── boulder_best.pt
│   └── uploads/
├── dist/
└── node_modules/
```

## Tech Stack

### Frontend

- React 19
- Vite
- Tailwind CSS
- JavaScript (JSX)

### Backend

- Python 3
- Flask
- Flask-CORS
- OpenCV
- NumPy
- Pandas
- xmltodict
- Ultralytics YOLO

### AI/Detection

- YOLO object detection models for lunar feature identification
- Metadata-based measurement calibration using:
  - pixel resolution
  - sun elevation
  - shadow geometry

## How the Application Works

### 1. Frontend workflow

The React app starts at the landing screen and allows the user to navigate to the analyzer page. From there:

- the user selects a lunar image
- the selected file is previewed in the UI
- the image is sent to the backend API via multipart form data
- the backend returns JSON results plus an annotated image
- the frontend displays the image, summaries, and results table

### 2. Backend workflow

The Flask server in `backend/main.py` performs the following steps:

- validates the uploaded file
- saves the temporary image locally
- loads the crater and boulder YOLO models
- reads metadata from `backend/metadata/lunar_metadata.xml`
- extracts:
  - image pixel resolution
  - sun elevation
- runs crater detection
- runs boulder detection
- estimates dimensions using either:
  - shadow measurement when enough shadow evidence is present
  - ratio-based estimation as fallback
- creates an annotated image with bounding boxes and labels
- returns a JSON payload containing:
  - `results_table`
  - `annotated_image` as a base64 data URL

### 3. Measurement logic

The backend uses two primary approaches for estimating physical dimensions:

#### Craters

- If shadow measurement is available, crater depth is estimated from shadow length and sun elevation.
- Otherwise, a fallback estimate is used using a diameter-to-depth ratio.

#### Boulders

- If shadow measurement is available, boulder height is estimated using shadow length and sun elevation.
- Otherwise, a fallback estimate is used using a height-width ratio.

This gives the system a scientific basis for approximate terrain measurements even when the image lacks strong shadow information.

## Backend API

The backend exposes the following endpoint:

### `POST /analyze`

Request:

- multipart form data
- field name: `image`

Example:

```bash
curl -X POST http://localhost:5001/analyze \
  -F "image=@path/to/lunar_image.jpg"
```

Response:

```json
{
  "results_table": [
    {
      "class": "Crater",
      "confidence": 0.42,
      "depth(KM)": 0.18,
      "height(KM)": null,
      "method": "Shadow Measurement"
    }
  ],
  "annotated_image": "data:image/jpeg;base64,..."
}
```

The backend also includes a health check endpoint:

### `GET /`

Returns service status and version information.

## Configuration

### Frontend environment

The frontend reads `VITE_BACKEND_URL` from the project-root environment at
build time.

Current value:

```env
VITE_BACKEND_URL=http://localhost:5001
```

For local development, use `http://localhost:5001`. For the deployed frontend,
set this to the Render service URL (without `/analyze` or a trailing slash)
and redeploy Vercel. Changing a Vercel environment variable does not change an
already-built deployment.

## Deploy the backend to Render

The repository includes a `render.yaml` Blueprint configuration. It creates a
Python web service from `backend/`, installs the backend requirements, serves
the Flask app with Gunicorn, and allows requests from the current Vercel
frontend. The model weights and metadata are inside `backend/` and are included
in the service.

1. Push the latest project changes to the GitHub repository connected to
   Vercel.
2. Sign in to Render and choose **New** > **Blueprint**.
3. Connect the GitHub repository and select the branch to deploy. Render reads
   `render.yaml` and creates the `lunar-survey-backend` web service.
4. Wait for the first build and deploy to finish. The initial build can take
   several minutes because PyTorch and the YOLO dependencies are large.
5. Open the Render service URL, for example
   `https://lunar-survey-backend.onrender.com`. Visit its root (`/`) and verify
   it returns JSON containing `"status": "running"`.
6. In Vercel, open the frontend project's **Settings** > **Environment
   Variables**. Set `VITE_BACKEND_URL` to the Render service URL, for example
   `https://lunar-survey-backend.onrender.com`. Do not add `/analyze` or a
   trailing slash. Apply it to Production, and Preview too if needed.
7. Redeploy the Vercel frontend so the new environment variable is included in
   its build.
8. Open the Vercel site, upload an image, and run an analysis. If the browser
   reports a CORS error, verify Render's `FRONTEND_ORIGIN` environment variable
   exactly matches `https://lunar-survey-a1ym.vercel.app`, then redeploy the
   backend.

For manual setup instead of using the Blueprint, create a **New Web Service**
from the same repository and configure:

- **Root Directory:** `backend`
- **Runtime:** Python
- **Build Command:** `pip install -r requirements.txt`
- **Start Command:** `gunicorn --workers 1 --threads 1 --timeout 300 --bind 0.0.0.0:$PORT main:app`
- **Environment Variables:** `PYTHON_VERSION` = `3.11.11`;
  `FRONTEND_ORIGIN` = `https://lunar-survey-a1ym.vercel.app`

Choose an instance with enough memory for PyTorch and both YOLO models. Small
free instances may run out of memory while loading models or analyzing images.
Render's service filesystem is ephemeral, but uploaded images are temporary
and deleted after each request.

## Dependencies

### Frontend dependencies

From `package.json`:

- React
- React DOM
- Tailwind CSS
- Vite
- ESLint and relevant React plugins

### Backend dependencies

From `backend/requirements.txt`:

```text
flask
flask-cors
ultralytics
opencv-python-headless
numpy
pandas
xmltodict
torch
torchvision
gunicorn
```

## Setup Instructions

### Prerequisites

- Node.js and npm
- Python 3.9+
- A working environment with internet access for dependency installation

### 1. Install frontend dependencies

```bash
npm install
```

### 2. Install backend dependencies

```bash
pip install -r backend/requirements.txt
```

### 3. Start the backend

From the project root:

```bash
python backend/main.py
```

The backend runs by default on:

```text
http://localhost:5001
```

### 4. Start the frontend

From the project root:

```bash
npm run dev -- --host 0.0.0.0
```

The Vite app usually runs at:

```text
http://localhost:4173
```

If port 4173 is already in use, Vite will automatically try the next available port, such as 4174.

## Running the Project

1. Launch the Python backend.
2. Launch the frontend dev server.
3. Open the frontend in your browser.
4. Navigate to the analyzer screen.
5. Upload a lunar image.
6. Click the analysis button.
7. View the results, annotations, and summary statistics.

## Important Files

### `src/App.jsx`

This is the main UI logic. It is responsible for:

- landing page rendering
- analyzer page rendering
- file selection
- image preview
- request submission to the backend
- result rendering and summary generation

### `backend/main.py`

This is the heart of the project. It contains:

- model loading
- metadata extraction
- image analysis
- crater and boulder detection
- dimension estimation
- annotated image creation
- Flask API routes

### `backend/metadata/lunar_metadata.xml`

This XML file provides metadata used by the analysis pipeline, including lunar spatial and illumination information.

### `backend/models/crater_best.pt`

The trained YOLO model for crater detection.

### `backend/models/boulder_best.pt`

The trained YOLO model for boulder detection.

## Notes on Data and Results

The project is designed for scientific exploration and rough estimation, not clinical-grade measurement. Results depend on:

- image quality
- lighting conditions
- object visibility
- model training quality
- metadata accuracy

The app emits summaries and measurement values in kilometers, using the metadata-driven pixel scale and shadow-based geometric estimation.

## Current Status

The application supports local development and production deployment using:

- frontend: Vite React app
- backend: Flask API on `localhost:5001`
- production backend: Gunicorn on Render

Local development still uses `localhost:5001`; production requests are sent to
the Render URL configured in Vercel.

## Troubleshooting

### Frontend says "Analysis failed: Failed to fetch"

This usually means:

- the backend is not running
- the backend port is wrong
- the `.env` file is set incorrectly

Check:

```bash
python backend/main.py
```

and confirm the project-root `.env` contains:

```env
VITE_BACKEND_URL=http://localhost:5001
```

For the deployed site, verify that Vercel has the Render URL set as
`VITE_BACKEND_URL` and that the frontend was redeployed after setting it.

### Model or metadata not found

Make sure the following files exist:

- `backend/models/crater_best.pt`
- `backend/models/boulder_best.pt`
- `backend/metadata/lunar_metadata.xml`

### Errors while installing dependencies

Use an updated Python version and reinstall packages from `backend/requirements.txt`.

## Future Improvements

Possible future enhancements include:

- user-friendly upload validation and format restrictions
- export of results to CSV or JSON
- image comparison and historical analysis
- more advanced crater/boulder segmentation
- improved measurement calibration

## License

This project is intended for academic and research-oriented lunar survey analysis. If you plan to reuse or extend it for publication or production deployment, ensure the project’s licensing and model usage constraints are reviewed before distribution.

## Conclusion

Lunar Survey is a compact but complete full-stack AI project for lunar terrain analysis. It brings together computer vision, scientific measurement, and a user-friendly interface into a single application that can detect and analyze lunar craters and boulders from uploaded imagery.
