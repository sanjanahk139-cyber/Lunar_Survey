import { useState, useMemo } from 'react';

function App() {
  const [page, setPage] = useState('landing');
  const [selectedImageFile, setSelectedImageFile] = useState(null);
  const [preview, setPreview] = useState('');
  const [results, setResults] = useState(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState('');

  const handleImageChange = (event) => {
    const file = event.target.files[0];

    if (file) {
      setSelectedImageFile(file);
      setPreview(URL.createObjectURL(file));
      setResults(null);
      setError('');
    }
  };

  const handleSubmit = async () => {
    if (!selectedImageFile) {
      setError('Please select an image file.');
      return;
    }

    setIsLoading(true);
    setError('');
    setResults(null);

    const formData = new FormData();

    // Flask backend expects the field name "image"
    formData.append('image', selectedImageFile);

    try {
      // Backend URL comes from frontend .env with a local fallback
      const backendBaseUrl = (
        import.meta.env.VITE_BACKEND_URL || 'http://localhost:5001'
      ).replace(/\/$/, '');
      const backendUrl = `${backendBaseUrl}/analyze`;

      console.log('Backend URL:', backendUrl);

      const response = await fetch(backendUrl, {
        method: 'POST',
        body: formData,
      });

      if (!response.ok) {
        let errorMessage = `Server responded with ${response.status}`;

        try {
          const errorData = await response.json();
          errorMessage = errorData.error || errorMessage;
        } catch {
          // Keep default error message
        }

        throw new Error(errorMessage);
      }

      const data = await response.json();

      console.log('Backend response:', data);

      // Backend returns results_table as an array
      setResults(data);

    } catch (err) {
      console.error('Analysis error:', err);

      setError(
        `Analysis failed: ${err.message}. Make sure the backend server and Cloudflare tunnel are running.`
      );
    } finally {
      setIsLoading(false);
    }
  };

  // Compute summary statistics
  const summary = useMemo(() => {
    if (!results?.results_table?.length) {
      return {
        total: 0,
        byClass: {},
        maxCount: 0,
      };
    }

    const byClass = {};

    results.results_table.forEach((row) => {
      const cls = row.class || 'Unknown';
      byClass[cls] = (byClass[cls] || 0) + 1;
    });

    const counts = Object.values(byClass);
    const maxCount = counts.length ? Math.max(...counts) : 0;

    return {
      total: results.results_table.length,
      byClass,
      maxCount,
    };
  }, [results]);

  // Color map for class bars
  const classColors = {
    crater: 'bg-cyan-500',
    Crater: 'bg-cyan-500',
    boulder: 'bg-amber-500',
    Boulder: 'bg-amber-500',
    rock: 'bg-orange-500',
    Rock: 'bg-orange-500',
  };

  const getBarColor = (cls) => {
    return classColors[cls] || 'bg-emerald-500';
  };

  // =========================
  // LANDING PAGE
  // =========================

  if (page === 'landing') {
    return (
      <div
        className="min-h-screen w-full flex items-center justify-center px-6 py-10 text-white"
        style={{
          backgroundImage:
            "linear-gradient(rgba(2, 6, 23, 0.25), rgba(2, 6, 23, 0.35)), url('/moon-astronaut-space-background.jpg')",
          backgroundSize: 'cover',
          backgroundPosition: 'center',
          backgroundRepeat: 'no-repeat',
          backgroundColor: '#020b1a',
        }}
      >
        <div className="w-full max-w-3xl text-center">

          <p
            className="mb-3 text-sm uppercase tracking-[0.35em] text-cyan-300"
            style={{
              textShadow: '0 2px 8px rgba(0,0,0,0.8)',
            }}
          >
            Lunar Survey
          </p>

          <h1
            className="text-3xl sm:text-5xl font-black text-white leading-tight"
            style={{
              textShadow: '0 2px 12px rgba(0,0,0,0.9)',
            }}
          >
            AI based Lunar Terrain Detection and Mapping System
          </h1>

          <p
            className="mt-6 text-lg text-slate-100 max-w-2xl mx-auto"
            style={{
              textShadow: '0 2px 8px rgba(0,0,0,0.8)',
            }}
          >
            Explore lunar terrain, analyze crater formations, and inspect
            surface data through a streamlined scientific workflow.
          </p>

          <button
            onClick={() => setPage('analyzer')}
            className="mt-10 inline-flex items-center justify-center rounded-full px-10 py-3.5 text-lg font-bold text-slate-950 transition-all duration-300 hover:scale-105 hover:brightness-110"
            style={{
              background:
                'linear-gradient(135deg, #22d3ee 0%, #67e8f9 40%, #a5f3fc 100%)',
              boxShadow:
                '0 0 20px rgba(34, 211, 238, 0.7), 0 0 40px rgba(34, 211, 238, 0.4), 0 4px 14px rgba(0,0,0,0.3)',
            }}
          >
            Explore
          </button>

        </div>
      </div>
    );
  }

  // =========================
  // ANALYZER PAGE
  // =========================

  return (
    <div
      className="min-h-screen w-full text-white p-0 m-0 font-sans"
      style={{
        backgroundImage:
          "linear-gradient(rgba(2, 6, 23, 0.55), rgba(2, 6, 23, 0.65)), url('/analyzer-background.jpg')",
        backgroundSize: 'cover',
        backgroundPosition: 'center',
        backgroundRepeat: 'no-repeat',
        backgroundAttachment: 'fixed',
        backgroundColor: '#020b1a',
      }}
    >

      <div className="mx-auto flex max-w-5xl flex-col items-center justify-center px-4 py-8">

        {/* HEADER */}

        <header className="mb-6 w-full text-center">

          <button
            onClick={() => setPage('landing')}
            className="mb-4 rounded-full border border-cyan-400/60 bg-slate-900/80 px-4 py-2 text-sm text-cyan-300 hover:bg-slate-800"
          >
            Back to Home
          </button>

          <h1
            className="text-3xl sm:text-4xl font-bold text-cyan-400"
            style={{
              textShadow: '0 2px 8px rgba(0,0,0,0.8)',
            }}
          >
            Lunar Crater & Boulder Analyzer
          </h1>

          <p
            className="mt-2 text-base text-slate-200"
            style={{
              textShadow: '0 1px 6px rgba(0,0,0,0.8)',
            }}
          >
            Upload an image to detect features and calculate their properties.
          </p>

        </header>

        {/* UPLOAD SECTION */}

        <div className="w-full max-w-2xl rounded-2xl border border-slate-700 bg-slate-800/90 p-5 shadow-xl">

          <div className="grid grid-cols-1 gap-4">

            <div>

              <label className="mb-2 block text-sm font-medium text-slate-200">
                Select Image File (.jpg, .png)
              </label>

              <input
                type="file"
                onChange={handleImageChange}
                accept="image/png, image/jpeg"
                className="w-full text-sm text-slate-300 file:mr-4 file:rounded-full file:border-0 file:bg-cyan-600 file:px-4 file:py-2 file:font-semibold file:text-white hover:file:bg-cyan-500"
              />

            </div>

          </div>

          <div className="pt-4 text-center">

            <button
              onClick={handleSubmit}
              disabled={isLoading || !selectedImageFile}
              className="w-full rounded-full bg-green-600 px-6 py-2.5 text-base font-bold text-white transition hover:bg-green-500 disabled:cursor-not-allowed disabled:bg-slate-500 sm:w-auto"
            >
              {isLoading ? 'Analyzing...' : 'Analyze Image'}
            </button>

          </div>

          {error && (
            <p className="mt-4 text-center text-red-400">
              {error}
            </p>
          )}

        </div>

        {/* PREVIEW AND RESULTS */}

        <div className="mt-6 grid w-full max-w-2xl grid-cols-1 gap-6">

          {/* IMAGE PREVIEW */}

          <div className="flex w-full flex-col items-center">

            <h2 className="mb-3 text-xl font-semibold text-cyan-400">
              Image Preview
            </h2>

            <div className="flex min-h-[220px] w-full max-w-md items-center justify-center rounded-xl border border-slate-700 bg-slate-800 p-3">

              {preview ? (
                <img
                  src={preview}
                  alt="Selected"
                  className="max-h-[40vh] max-w-full rounded-md"
                />
              ) : (
                <p className="text-slate-400">
                  Select an image to see a preview
                </p>
              )}

            </div>

          </div>

          {/* LOADING */}

          <div className="flex w-full flex-col items-center">

            {isLoading && (
              <div className="flex min-h-[220px] w-full max-w-md items-center justify-center rounded-xl border border-slate-700 bg-slate-800 p-4 animate-pulse">

                <p className="text-base text-slate-300">
                  Processing... This may take a moment.
                </p>

              </div>
            )}

            {/* RESULTS */}

            {results && (
              <>

                <h2 className="mb-3 text-xl font-semibold text-cyan-400">
                  Analysis Results
                </h2>

                <div className="flex w-full flex-col items-center space-y-4">

                  {/* ANNOTATED IMAGE */}

                  <div className="flex w-full max-w-md items-center justify-center rounded-xl border-2 border-cyan-500 bg-slate-900 p-2">

                    <img
                      src={results.annotated_image}
                      alt="Analysis Result"
                      className="max-h-[40vh] max-w-full rounded-md shadow-lg"
                    />

                  </div>

                  {/* SUMMARY */}

                  <div className="w-full rounded-xl border border-slate-700 bg-slate-800 p-4">

                    <h3 className="mb-3 text-lg font-semibold text-cyan-300">
                      Summary
                    </h3>

                    {/* TOTAL COUNT */}

                    <div className="mb-4 flex items-center justify-center gap-3 rounded-lg bg-slate-900/80 border border-cyan-500/40 px-4 py-3">

                      <span className="text-sm uppercase tracking-wider text-slate-400">
                        Total Detections
                      </span>

                      <span className="text-3xl font-bold text-cyan-400 tabular-nums">
                        {summary.total}
                      </span>

                    </div>

                    {/* BAR CHART */}

                    {summary.total > 0 && (
                      <div className="mt-2">

                        <p className="mb-3 text-sm font-medium text-slate-300">
                          Detections by Class
                        </p>

                        <div className="flex items-end justify-center gap-4 sm:gap-6 min-h-[160px] px-2 pt-2 pb-1">

                          {Object.entries(summary.byClass).map(
                            ([cls, count]) => {

                              const pct =
                                summary.maxCount > 0
                                  ? (count / summary.maxCount) * 100
                                  : 0;

                              const barH = Math.max(pct, 12);

                              return (
                                <div
                                  key={cls}
                                  className="flex flex-col items-center gap-2 flex-1 max-w-[80px]"
                                >

                                  <span className="text-sm font-bold text-cyan-300 tabular-nums">
                                    {count}
                                  </span>

                                  <div className="w-full flex items-end justify-center h-[120px]">

                                    <div
                                      className={`w-10 sm:w-12 rounded-t-md transition-all duration-500 ${getBarColor(
                                        cls
                                      )}`}
                                      style={{
                                        height: `${barH}%`,
                                        boxShadow:
                                          '0 0 12px rgba(34, 211, 238, 0.35)',
                                      }}
                                      title={`${cls}: ${count}`}
                                    />

                                  </div>

                                  <span className="text-xs capitalize font-medium text-slate-300 text-center leading-tight truncate w-full">
                                    {cls}
                                  </span>

                                </div>
                              );
                            }
                          )}

                        </div>

                        <div className="mt-1 border-t border-slate-600 mx-2" />

                      </div>
                    )}

                    {summary.total === 0 && (
                      <p className="text-center text-slate-400 text-sm">
                        No objects detected.
                      </p>
                    )}

                  </div>

                  {/* DETECTION TABLE */}

                  <div className="w-full rounded-xl border border-slate-700 bg-slate-800 p-3">

                    <h3 className="mb-2 text-lg font-semibold">
                      Detection Data
                    </h3>

                    <div className="overflow-x-auto">

                      <table className="w-full text-left text-xs">

                        <thead className="bg-slate-700">

                          <tr>
                            <th className="p-2">Class</th>
                            <th className="p-2">Confidence</th>
                            <th className="p-2">Height (KM)</th>
                            <th className="p-2">Depth (KM)</th>
                            <th className="p-2">Method</th>
                          </tr>

                        </thead>

                        <tbody>

                          {results.results_table.length > 0 ? (

                            results.results_table.map((row, index) => (

                              <tr
                                key={index}
                                className="border-b border-slate-700 hover:bg-slate-700/50"
                              >

                                <td className="p-2">
                                  {row.class}
                                </td>

                                <td className="p-2">
                                  {Number(row.confidence).toFixed(2)}
                                </td>

                                <td className="p-2">
                                  {row['height(KM)'] != null
                                    ? Number(row['height(KM)']).toFixed(2)
                                    : 'N/A'}
                                </td>

                                <td className="p-2">
                                  {row['depth(KM)'] != null
                                    ? Number(row['depth(KM)']).toFixed(2)
                                    : 'N/A'}
                                </td>

                                <td className="p-2">
                                  {row.method}
                                </td>

                              </tr>

                            ))

                          ) : (

                            <tr>

                              <td
                                colSpan="5"
                                className="p-2 text-center text-slate-400"
                              >
                                No objects detected.
                              </td>

                            </tr>

                          )}

                        </tbody>

                      </table>

                    </div>

                  </div>

                </div>

              </>
            )}

          </div>

        </div>

      </div>

    </div>
  );
}

export default App;