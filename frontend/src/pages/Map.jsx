import { useState, useEffect, useMemo } from 'react';
import { Link } from 'react-router-dom';

import {
  MapContainer,
  TileLayer,
  CircleMarker,
  Popup,
  useMapEvents,
} from 'react-leaflet';
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Title,
  Tooltip as ChartTooltip,
  Legend as ChartLegend,
  Filler,
} from 'chart.js';
import { Line } from 'react-chartjs-2';
import api, { fetchOutbreakDiseases } from '../services/api';
import Loader from '../components/Loader';
import 'leaflet/dist/leaflet.css';

// ── Register Chart.js modules ──────────────────────────────────────
ChartJS.register(
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Title,
  ChartTooltip,
  ChartLegend,
  Filler,
);

// ── Helpers ────────────────────────────────────────────────────────
const severityColor = {
  high: 'red',
  medium: 'orange',
  low: 'green',
};

const DEFAULT_SOURCE_FILTERS = ['WHO', 'CDC'];

const markerRadius = (caseCount) =>
  Math.min(Math.max((caseCount || 0) / 10000, 5), 20);

const clusterRadius = (count) =>
  Math.min(Math.max(10 + count * 1.2, 12), 28);

const formatDate = (raw) => {
  if (!raw) return 'Unknown';
  return new Intl.DateTimeFormat('en-GB', {
    day: '2-digit',
    month: 'short',
    year: 'numeric',
  }).format(new Date(raw));
};

const formatNumber = (n) =>
  n != null ? new Intl.NumberFormat().format(n) : 'Unknown';

const normalizeSource = (value) => String(value || '').trim();

const getClusterCellSize = (zoom) => {
  if (zoom >= 8) return 0;
  if (zoom >= 6) return 1.2;
  if (zoom >= 4) return 3.5;
  if (zoom >= 3) return 7;
  return 14;
};

const severityRank = {
  high: 3,
  medium: 2,
  low: 1,
};

const resolveClusterSeverity = (items) => {
  let strongest = 'low';
  let strongestRank = 0;

  for (const item of items) {
    const severity = String(item.severity || '').toLowerCase();
    const rank = severityRank[severity] || 0;
    if (rank > strongestRank) {
      strongest = severity;
      strongestRank = rank;
    }
  }

  return strongestRank ? strongest : 'low';
};

const summarizeValues = (items, key, limit = 3) => {
  const counts = new Map();
  for (const item of items) {
    const value = String(item[key] || '').trim();
    if (!value) continue;
    counts.set(value, (counts.get(value) || 0) + 1);
  }

  return [...counts.entries()]
    .sort((a, b) => b[1] - a[1] || a[0].localeCompare(b[0]))
    .slice(0, limit)
    .map(([value]) => value);
};

const buildMarkerGroups = (items, zoom) => {
  const cellSize = getClusterCellSize(zoom);
  if (cellSize === 0) {
    return items.map((item, index) => ({
      type: 'marker',
      key: `${item.disease}-${item.country}-${item.source}-${index}`,
      item,
    }));
  }

  const buckets = new Map();
  for (const item of items) {
    const lat = parseFloat(item.lat);
    const lng = parseFloat(item.lng);
    if (Number.isNaN(lat) || Number.isNaN(lng)) {
      continue;
    }

    const latBucket = Math.round(lat / cellSize);
    const lngBucket = Math.round(lng / cellSize);
    const bucketKey = `${latBucket}:${lngBucket}`;
    if (!buckets.has(bucketKey)) {
      buckets.set(bucketKey, []);
    }
    buckets.get(bucketKey).push(item);
  }

  return [...buckets.entries()].map(([bucketKey, bucketItems]) => {
    if (bucketItems.length === 1) {
      return {
        type: 'marker',
        key: `${bucketKey}:single`,
        item: bucketItems[0],
      };
    }

    const lat =
      bucketItems.reduce((sum, item) => sum + parseFloat(item.lat || 0), 0) /
      bucketItems.length;
    const lng =
      bucketItems.reduce((sum, item) => sum + parseFloat(item.lng || 0), 0) /
      bucketItems.length;
    const totalCases = bucketItems.reduce(
      (sum, item) => sum + Number(item.case_count || 0),
      0,
    );

    return {
      type: 'cluster',
      key: `${bucketKey}:cluster`,
      cluster: {
        lat,
        lng,
        count: bucketItems.length,
        severity: resolveClusterSeverity(bucketItems),
        totalCases,
        diseases: summarizeValues(bucketItems, 'disease'),
        countries: summarizeValues(bucketItems, 'country'),
        sources: summarizeValues(bucketItems, 'source'),
      },
    };
  });
};

// ── Zoom tracker (placed inside MapContainer) ──────────────────────
const MapViewportTracker = ({ onZoomChange }) => {
  useMapEvents({
    zoomend: (event) => {
      onZoomChange(event.target.getZoom());
    },
  });

  return null;
};

// ── Component ──────────────────────────────────────────────────────
const MapPage = () => {
  // Map data
  const [outbreaks, setOutbreaks] = useState([]);
  const [mapLoading, setMapLoading] = useState(true);
  const [mapError, setMapError] = useState(null);
  const [mapZoom, setMapZoom] = useState(2);
  const [selectedMapDisease, setSelectedMapDisease] = useState('');
  const [selectedMapSeverity, setSelectedMapSeverity] = useState('');
  const [selectedSources, setSelectedSources] = useState(DEFAULT_SOURCE_FILTERS);

  // Trend data
  const [diseases, setDiseases] = useState([]);
  const [selectedDisease, setSelectedDisease] = useState('');
  const [trendData, setTrendData] = useState([]);
  const [trendLoading, setTrendLoading] = useState(false);
  const [trendError, setTrendError] = useState(null);

  // ── Fetch map outbreaks on mount ─────────────────────────────────
  useEffect(() => {
    const fetchMapData = async () => {
      try {
        setMapLoading(true);
        const res = await api.get('/outbreaks/map');
        const data = res.data?.data ?? res.data ?? [];
        setOutbreaks(Array.isArray(data) ? data : []);
      } catch (err) {
        setMapError(
          err.response?.data?.message || 'Failed to load map data.',
        );
      } finally {
        setMapLoading(false);
      }
    };
    fetchMapData();
  }, []);

  // ── Fetch disease list on mount ──────────────────────────────────
  useEffect(() => {
    const fetchDiseases = async () => {
      try {
        const outbreakDiseases = await fetchOutbreakDiseases();
        setDiseases(outbreakDiseases);
        setSelectedDisease((current) =>
          current && outbreakDiseases.includes(current)
            ? current
            : outbreakDiseases[0] || '',
        );
      } catch {
        setDiseases([]);
        setSelectedDisease('');
        // silently ignore — dropdown will just be empty
      }
    };
    fetchDiseases();
  }, []);

  useEffect(() => {
    console.log('Diseases:', diseases);
  }, [diseases]);

  // ── Fetch trend data when disease changes ────────────────────────
  useEffect(() => {
    if (!selectedDisease) {
      setTrendData([]);
      return;
    }

    const fetchTrend = async () => {
      try {
        setTrendLoading(true);
        setTrendError(null);
        const res = await api.get('/outbreaks/trends', {
          params: { disease: selectedDisease },
        });
        const data = res.data?.data ?? res.data ?? [];
        setTrendData(Array.isArray(data) ? data : []);
      } catch (err) {
        setTrendError(
          err.response?.data?.message || 'Failed to load trend data.',
        );
      } finally {
        setTrendLoading(false);
      }
    };
    fetchTrend();
  }, [selectedDisease]);

  useEffect(() => {
    console.log('Trends:', trendData);
  }, [trendData]);

  // ── Map filter derived data ──────────────────────────────────────
  const mapDiseases = useMemo(
    () =>
      [...new Set(outbreaks.map((item) => item?.disease).filter(Boolean))].sort(
        (a, b) => a.localeCompare(b),
      ),
    [outbreaks],
  );

  const mapSeverities = useMemo(
    () =>
      [
        ...new Set(
          outbreaks
            .map((item) => String(item?.severity || '').toLowerCase())
            .filter(Boolean),
        ),
      ].sort(),
    [outbreaks],
  );

  const mapSources = useMemo(
    () =>
      [...new Set(outbreaks.map((item) => normalizeSource(item?.source)).filter(Boolean))].sort(
        (a, b) => a.localeCompare(b),
      ),
    [outbreaks],
  );

  const filteredOutbreaks = useMemo(
    () =>
      outbreaks.filter((item) => {
        const source = normalizeSource(item?.source);
        const severity = String(item?.severity || '').toLowerCase();

        if (selectedMapDisease && item?.disease !== selectedMapDisease) {
          return false;
        }
        if (selectedMapSeverity && severity !== selectedMapSeverity) {
          return false;
        }
        if (selectedSources.length && !selectedSources.includes(source)) {
          return false;
        }
        return true;
      }),
    [outbreaks, selectedMapDisease, selectedMapSeverity, selectedSources],
  );

  const markerGroups = useMemo(
    () => buildMarkerGroups(filteredOutbreaks, mapZoom),
    [filteredOutbreaks, mapZoom],
  );

  // ── Chart config ─────────────────────────────────────────────────
  const chartData = {
    labels: trendData.map((d) => formatDate(d.date)),
    datasets: [
      {
        label: 'Case Count',
        data: trendData.map((d) => d.case_count),
        borderColor: '#3b82f6',
        backgroundColor: 'rgba(59, 130, 246, 0.1)',
        tension: 0.35,
        fill: true,
        pointRadius: 4,
        pointHoverRadius: 6,
      },
    ],
  };

  const chartOptions = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: { display: false },
      title: {
        display: true,
        text: `${selectedDisease} — Case Trend Over Time`,
        font: { size: 16, weight: '600' },
        color: '#1f2937',
        padding: { bottom: 16 },
      },
    },
    scales: {
      x: {
        grid: { display: false },
        ticks: { color: '#6b7280', maxRotation: 45 },
      },
      y: {
        beginAtZero: true,
        ticks: { color: '#6b7280' },
        grid: { color: '#f3f4f6' },
      },
    },
  };

  const toggleSource = (source) => {
    setSelectedSources((current) =>
      current.includes(source)
        ? current.filter((item) => item !== source)
        : [...current, source],
    );
  };

  // ── Render ───────────────────────────────────────────────────────
  return (
    <div className="mx-auto max-w-7xl space-y-10">
      {/* ─── MAP SECTION ─────────────────────────────────────────── */}
      <section>
        <h1 className="mb-6 text-3xl font-bold text-gray-900">
          Global Outbreak Map
        </h1>

        {mapLoading && <Loader />}

        {mapError && (
          <div className="rounded-lg border border-red-200 bg-red-50 p-6 text-red-600 shadow-sm">
            <h2 className="mb-1 text-lg font-bold">Error Loading Map</h2>
            <p>{mapError}</p>
          </div>
        )}

        {!mapLoading && !mapError && (
          <div className="space-y-4">
            {/* ── Filter bar ──────────────────────────────────────── */}
            <div className="rounded-xl border border-gray-200 bg-white p-4 shadow-sm">
              <div className="grid gap-4 md:grid-cols-3">
                <div>
                  <label
                    htmlFor="map-disease-filter"
                    className="mb-2 block text-sm font-medium text-gray-700"
                  >
                    Disease Filter
                  </label>
                  <select
                    id="map-disease-filter"
                    value={selectedMapDisease}
                    onChange={(e) => setSelectedMapDisease(e.target.value)}
                    className="w-full rounded-lg border border-gray-300 bg-white px-4 py-2.5 text-sm text-gray-800 shadow-sm transition focus:border-blue-500 focus:outline-none focus:ring-2 focus:ring-blue-500/20"
                  >
                    <option value="">All diseases</option>
                    {mapDiseases.map((name) => (
                      <option key={name} value={name}>
                        {name}
                      </option>
                    ))}
                  </select>
                </div>

                <div>
                  <label
                    htmlFor="map-severity-filter"
                    className="mb-2 block text-sm font-medium text-gray-700"
                  >
                    Severity Filter
                  </label>
                  <select
                    id="map-severity-filter"
                    value={selectedMapSeverity}
                    onChange={(e) => setSelectedMapSeverity(e.target.value)}
                    className="w-full rounded-lg border border-gray-300 bg-white px-4 py-2.5 text-sm text-gray-800 shadow-sm transition focus:border-blue-500 focus:outline-none focus:ring-2 focus:ring-blue-500/20"
                  >
                    <option value="">All severities</option>
                    {mapSeverities.map((severity) => (
                      <option key={severity} value={severity}>
                        {severity}
                      </option>
                    ))}
                  </select>
                </div>

                <div>
                  <p className="mb-2 text-sm font-medium text-gray-700">Source Filter</p>
                  <div className="flex flex-wrap gap-2">
                    {mapSources.map((source) => {
                      const isActive = selectedSources.includes(source);
                      return (
                        <button
                          key={source}
                          type="button"
                          onClick={() => toggleSource(source)}
                          className={`rounded-full border px-3 py-1.5 text-sm font-medium transition ${
                            isActive
                              ? 'border-blue-200 bg-blue-50 text-blue-700'
                              : 'border-gray-200 bg-white text-gray-600 hover:border-gray-300 hover:bg-gray-50'
                          }`}
                        >
                          {source}
                        </button>
                      );
                    })}
                  </div>
                </div>
              </div>

              <div className="mt-4 flex flex-wrap items-center gap-3 text-sm text-gray-600">
                <span className="rounded-full bg-gray-100 px-3 py-1 font-medium">
                  Showing {filteredOutbreaks.length} outbreak records
                </span>
                <span className="rounded-full bg-gray-100 px-3 py-1 font-medium">
                  Rendered as {markerGroups.length} map markers
                </span>
                {!selectedSources.includes('disease.sh') && (
                  <span className="rounded-full bg-amber-50 px-3 py-1 font-medium text-amber-700">
                    disease.sh hidden by default
                  </span>
                )}
              </div>
            </div>

            {/* ── Map ─────────────────────────────────────────────── */}
            <div className="relative overflow-hidden rounded-xl border border-gray-200 shadow-md">
              <MapContainer
                center={[20, 0]}
                zoom={2}
                scrollWheelZoom={true}
                className="h-[500px] w-full"
              >
                <MapViewportTracker onZoomChange={setMapZoom} />
                <TileLayer
                  attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>'
                  url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
                />

                {markerGroups.map((entry) => {
                  if (entry.type === 'cluster') {
                    const cluster = entry.cluster;
                    return (
                      <CircleMarker
                        key={entry.key}
                        center={[cluster.lat, cluster.lng]}
                        radius={clusterRadius(cluster.count)}
                        pathOptions={{
                          color: severityColor[cluster.severity] || 'gray',
                          fillColor: severityColor[cluster.severity] || 'gray',
                          fillOpacity: 0.4,
                          weight: 2,
                        }}
                      >
                        <Popup>
                          <div className="min-w-[220px] text-sm leading-relaxed">
                            <div className="text-base font-bold text-gray-900">
                              Cluster of {cluster.count} outbreaks
                            </div>
                            <hr className="my-2 border-gray-200" />
                            <div>
                              <span className="font-medium text-gray-700">Cases:</span>{' '}
                              {formatNumber(cluster.totalCases)}
                            </div>
                            <div>
                              <span className="font-medium text-gray-700">Severity:</span>{' '}
                              {cluster.severity}
                            </div>
                            <div>
                              <span className="font-medium text-gray-700">Diseases:</span>{' '}
                              {cluster.diseases.join(', ') || 'N/A'}
                            </div>
                            <div>
                              <span className="font-medium text-gray-700">Countries:</span>{' '}
                              {cluster.countries.join(', ') || 'N/A'}
                            </div>
                            <div>
                              <span className="font-medium text-gray-700">Sources:</span>{' '}
                              {cluster.sources.join(', ') || 'N/A'}
                            </div>
                          </div>
                        </Popup>
                      </CircleMarker>
                    );
                  }

                  const ob = entry.item;
                  const lat = parseFloat(ob.lat);
                  const lng = parseFloat(ob.lng);
                  if (Number.isNaN(lat) || Number.isNaN(lng)) return null;

                  return (
                    <CircleMarker
                      key={entry.key}
                      center={[lat, lng]}
                      radius={markerRadius(ob.case_count)}
                      pathOptions={{
                        color: severityColor[String(ob.severity || '').toLowerCase()] || 'gray',
                        fillColor: severityColor[String(ob.severity || '').toLowerCase()] || 'gray',
                        fillOpacity: 0.55,
                        weight: 2,
                      }}
                    >
                      <Popup>
                        <div className="min-w-[180px] text-sm leading-relaxed">
                          <Link
                            to={`/disease/${encodeURIComponent(String(ob.disease || '').toLowerCase())}`}
                            className="text-base font-bold text-blue-600 hover:text-blue-700 hover:underline"
                          >
                            {ob.disease}
                          </Link>
                          <br />
                          <span className="text-gray-600">{ob.country}</span>
                          <hr className="my-1.5 border-gray-200" />
                          <span className="font-medium text-gray-700">
                            Cases:
                          </span>{' '}
                          {formatNumber(ob.case_count)}
                          <br />
                          <span className="font-medium text-gray-700">
                            Date:
                          </span>{' '}
                          {formatDate(ob.date)}
                          <br />
                          <span className="font-medium text-gray-700">
                            Source:
                          </span>{' '}
                          {ob.source || 'N/A'}
                        </div>
                      </Popup>
                    </CircleMarker>
                  );
                })}
              </MapContainer>

              {/* ── Legend overlay ──────────────────────────────────── */}
              <div className="absolute bottom-4 right-4 z-[1000] rounded-lg border border-gray-200 bg-white/95 px-4 py-3 shadow-lg backdrop-blur">
                <p className="mb-2 text-xs font-bold uppercase tracking-wider text-gray-500">
                  Severity
                </p>
                {[
                  { label: 'High', color: severityColor.high },
                  { label: 'Medium', color: severityColor.medium },
                  { label: 'Low', color: severityColor.low },
                ].map(({ label, color }) => (
                  <div key={label} className="flex items-center gap-2 text-sm text-gray-700">
                    <span
                      className="inline-block h-3 w-3 rounded-full"
                      style={{ backgroundColor: color }}
                    />
                    {label}
                  </div>
                ))}
              </div>
            </div>
          </div>
        )}

        {!mapLoading && !mapError && filteredOutbreaks.length === 0 && (
          <div className="mt-4 rounded-lg border border-gray-100 bg-white p-8 text-center text-gray-500 shadow-sm">
            No outbreak map data matches the current filters.
          </div>
        )}
      </section>

      {/* ─── TREND CHART SECTION ─────────────────────────────────── */}
      {false && (
      <section>
        <h2 className="mb-6 text-2xl font-bold text-gray-900">
          Disease Trends
        </h2>

        {/* Disease selector */}
        <div className="mb-6">
          <label
            htmlFor="disease-select"
            className="mb-2 block text-sm font-medium text-gray-700"
          >
            Select a disease to view trends
          </label>
          <select
            id="disease-select"
            value={selectedDisease}
            onChange={(e) => setSelectedDisease(e.target.value)}
            className="w-full max-w-sm rounded-lg border border-gray-300 bg-white px-4 py-2.5 text-sm text-gray-800 shadow-sm transition focus:border-blue-500 focus:outline-none focus:ring-2 focus:ring-blue-500/20"
          >
            <option value="">— Choose disease —</option>
            {diseases.map((name) => (
              <option key={name} value={name}>
                {name}
              </option>
            ))}
          </select>
        </div>

        {/* Chart / states */}
        {!selectedDisease && (
          <div className="rounded-lg border border-gray-100 bg-white p-10 text-center text-gray-400 shadow-sm">
            Pick a disease from the dropdown above to view its case trend.
          </div>
        )}

        {selectedDisease && trendLoading && <Loader />}

        {selectedDisease && trendError && (
          <div className="rounded-lg border border-red-200 bg-red-50 p-6 text-red-600 shadow-sm">
            <h2 className="mb-1 text-lg font-bold">Error Loading Trends</h2>
            <p>{trendError}</p>
          </div>
        )}

        {selectedDisease &&
          !trendLoading &&
          !trendError &&
          trendData.length === 0 && (
            <div className="rounded-lg border border-gray-100 bg-white p-10 text-center text-gray-500 shadow-sm">
              No trend data available for {selectedDisease}.
            </div>
          )}

        {selectedDisease &&
          !trendLoading &&
          !trendError &&
          trendData.length > 0 && (
            <div className="rounded-xl border border-gray-200 bg-white p-6 shadow-sm">
              <div className="h-[380px]">
                <Line data={chartData} options={chartOptions} />
              </div>
            </div>
          )}
      </section>
      )}
    </div>
  );
};

export default MapPage;
