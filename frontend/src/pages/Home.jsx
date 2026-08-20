import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import api from '../utils/api';
import Loader from '../components/Loader';

import StatCard from '../components/StatCard';

const severityBadge = {
  high: 'bg-red-100 text-red-800 border-red-200',
  medium: 'bg-orange-100 text-orange-800 border-orange-200',
  low: 'bg-green-100 text-green-800 border-green-200',
};

const formatNumber = (value) => new Intl.NumberFormat().format(value ?? 0);

const Home = () => {
  const navigate = useNavigate();
  const [outbreaks, setOutbreaks] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    const fetchOutbreaks = async () => {
      try {
        setLoading(true);
        console.log("API CALL TRIGGERED");
        const response = await api.get('/outbreaks/summary');
        if (response.data.success) {
          setOutbreaks(response.data.data);
        } else {
          setError(response.data.message || 'Failed to fetch outbreaks.');
        }
      } catch (err) {
        setError(err.response?.data?.message || 'A network error occurred connecting to the API.');
      } finally {
        setLoading(false);
      }
    };

    fetchOutbreaks();
  }, []);

  if (loading) return <Loader />;

  if (error) {
    return (
      <div className="p-6 bg-red-50 text-red-600 border border-red-200 rounded-lg shadow-sm">
        <h2 className="font-bold text-lg mb-1">Error Loading Data</h2>
        <p>{error}</p>
      </div>
    );
  }

  if (outbreaks.length === 0) {
    return (
      <div className="p-10 text-center text-gray-500 bg-white rounded-xl shadow-sm border border-gray-100">
        <h2 className="text-2xl font-semibold mb-2">No outbreaks found</h2>
        <p>There are currently no active outbreaks being monitored.</p>
      </div>
    );
  }

  // Calculate stats
  const totalDiseases = outbreaks.length;
  const totalOccurrences = outbreaks.reduce((sum, outbreak) => sum + (outbreak.occurrences || 0), 0);
  const highSeverityCount = outbreaks.filter((o) => (o.severity || '').toLowerCase() === 'high').length;
  const critical = outbreaks
    .filter((o) => (o.severity || '').toLowerCase() === 'high')
    .slice(0, 3);

  return (
    <div className="max-w-7xl mx-auto space-y-8">
      {/* SUMMARY CARDS */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <StatCard title="Diseases Summarized" value={totalDiseases} />
        <StatCard title="Occurrences Logged" value={totalOccurrences} />
        <StatCard title="High Severity" value={highSeverityCount} />
      </div>

      {/* CRITICAL OUTBREAKS */}
      {critical.length > 0 && (
        <div>
          <h2 className="text-2xl font-bold text-gray-800 mb-6">Critical Outbreaks</h2>
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
            {critical.map((outbreak, index) => (
              <div
                key={`${outbreak.disease}-${index}`}
                className="rounded-2xl border-2 border-red-300 bg-red-50/60 p-2 shadow-sm cursor-pointer hover:shadow-lg transition"
                onClick={() => navigate(`/disease/${encodeURIComponent(outbreak.disease.toLowerCase())}`)}
              >
                <div className="mb-3 flex items-center justify-between px-2 pt-2">
                  <span className="inline-flex rounded-full bg-red-600 px-3 py-1 text-xs font-bold uppercase tracking-wide text-white">
                    High Risk
                  </span>
                </div>
                <div className="rounded-xl border border-red-100 bg-white p-5 shadow-sm">
                  <div className="mb-4 flex items-start justify-between gap-4">
                    <div>
                      <h3 className="text-xl font-bold text-gray-900 capitalize">{outbreak.disease}</h3>
                      <p className="mt-1 text-sm text-gray-600">
                        {formatNumber(outbreak.total_cases)} total cases
                      </p>
                    </div>
                    <span className={`rounded-full border px-2.5 py-1 text-xs font-semibold uppercase ${severityBadge[(outbreak.severity || 'low').toLowerCase()] || severityBadge.low}`}>
                      {outbreak.severity || 'low'}
                    </span>
                  </div>
                  <p className="text-sm text-gray-600">
                    {outbreak.occurrences || 0} recorded outbreaks
                  </p>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* OUTBREAK LIST */}
      <div>
        <h2 className="text-2xl font-bold text-gray-800 mb-6">Recent Outbreaks</h2>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {outbreaks.map((outbreak, index) => (
            <div 
              key={`${outbreak.disease}-${index}`} 
              className="rounded-xl border border-gray-100 bg-white p-5 shadow-sm transition hover:shadow-lg cursor-pointer"
              onClick={() => navigate(`/disease/${encodeURIComponent(outbreak.disease)}`)}
            >
              <div className="mb-4 flex items-start justify-between gap-4">
                <div>
                  <h3 className="text-xl font-bold text-gray-900 capitalize">{outbreak.disease}</h3>
                  <p className="mt-1 text-sm text-gray-600">
                    {outbreak.occurrences || 0} recorded outbreaks
                  </p>
                </div>
                <span className={`rounded-full border px-2.5 py-1 text-xs font-semibold uppercase ${severityBadge[(outbreak.severity || 'low').toLowerCase()] || severityBadge.low}`}>
                  {outbreak.severity || 'low'}
                </span>
              </div>

              <div className="space-y-3 text-sm text-gray-700">
                <div className="flex items-center justify-between gap-3">
                  <span className="font-medium text-gray-500">Total Cases</span>
                  <span className="font-semibold text-gray-900">{formatNumber(outbreak.total_cases)}</span>
                </div>
                <div className="flex items-center justify-between gap-3">
                  <span className="font-medium text-gray-500">Occurrences</span>
                  <span className="font-semibold text-gray-900">{outbreak.occurrences || 0}</span>
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};

export default Home;
