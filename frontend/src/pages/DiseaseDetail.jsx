import { useEffect, useState } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';

import api from '../utils/api';
import Loader from '../components/Loader';

const getSeverityStyle = (severity) => {
  switch (severity?.toLowerCase()) {
    case 'high':
      return 'bg-red-100 text-red-800 border-red-200';
    case 'medium':
      return 'bg-orange-100 text-orange-800 border-orange-200';
    case 'low':
      return 'bg-green-100 text-green-800 border-green-200';
    default:
      return 'bg-gray-100 text-gray-800 border-gray-200';
  }
};

const formatDate = (value) => {
  if (!value) return 'Unknown';

  return new Intl.DateTimeFormat('en-GB', {
    day: '2-digit',
    month: 'short',
    year: 'numeric',
  }).format(new Date(value));
};

const DiseaseDetail = () => {
  const location = useLocation();
  const name = location.pathname.replace('/disease/', '');
  const navigate = useNavigate();
  const [disease, setDisease] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    const fetchDisease = async () => {
      try {
        setLoading(true);
        setError(null);

        const response = await api.get(`/diseases/${name}`);
        if (response.data.success) {
          setDisease(response.data.data);
        } else {
          setError('Disease not found');
        }
      } catch (err) {
        setError('Disease not found');
      } finally {
        setLoading(false);
      }
    };

    fetchDisease();
  }, [name]);

  if (loading) return <Loader />;

  if (error) {
    return (
      <div className="mx-auto max-w-3xl px-4 py-10">
        <div className="rounded-2xl border border-red-200 bg-red-50 p-8 text-center text-red-700 shadow-sm">
          <h1 className="mb-3 text-2xl font-bold">Disease not found</h1>
          <p className="mb-6 text-sm sm:text-base">{error}</p>
          <button
            type="button"
            onClick={() => navigate('/')}
            className="inline-flex items-center rounded-lg bg-gray-900 px-4 py-2 text-sm font-medium text-white transition hover:bg-gray-800"
          >
            Back to Home
          </button>
        </div>
      </div>
    );
  }

  if (!disease) {
    return (
      <div className="mx-auto max-w-3xl px-4 py-10">
        <div className="rounded-2xl border border-gray-200 bg-white p-8 text-center text-gray-600 shadow-sm">
          <h1 className="mb-3 text-2xl font-bold text-gray-900">Disease not found</h1>
          <button
            type="button"
            onClick={() => navigate('/')}
            className="mt-2 inline-flex items-center rounded-lg bg-gray-900 px-4 py-2 text-sm font-medium text-white transition hover:bg-gray-800"
          >
            Back to Home
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="mx-auto max-w-4xl px-4 py-8">
      <div className="mb-6">
        <button
          type="button"
          onClick={() => navigate('/')}
          className="inline-flex items-center rounded-lg border border-gray-200 bg-white px-4 py-2 text-sm font-medium text-gray-700 transition hover:border-gray-300 hover:bg-gray-50"
        >
          Back to Home
        </button>
      </div>

      <div className="rounded-2xl border border-gray-100 bg-white p-8 shadow-sm">
        <div className="mb-8 flex flex-col gap-4 border-b border-gray-100 pb-6 sm:flex-row sm:items-start sm:justify-between">
          <div>
            <h1 className="text-3xl font-bold text-gray-900 capitalize">{disease.name}</h1>
            <p className="mt-2 text-sm text-gray-500">Last updated: {formatDate(disease.last_updated || disease.date)}</p>
          </div>
          <span className={`inline-flex rounded-full border px-3 py-1 text-sm font-semibold uppercase ${getSeverityStyle(disease.severity)}`}>
            {disease.severity || 'unknown'}
          </span>
        </div>

        <div className="grid gap-6 md:grid-cols-2">
          <div className="rounded-xl bg-gray-50 p-5">
            <h2 className="mb-3 text-lg font-semibold text-gray-800">Symptoms</h2>
            <ul className="list-disc space-y-2 pl-5 text-gray-700">
              {(disease.symptoms || []).map((symptom) => (
                <li key={symptom}>{symptom}</li>
              ))}
            </ul>
          </div>

          <div className="space-y-6">
            <div className="rounded-xl bg-gray-50 p-5">
              <h2 className="mb-2 text-lg font-semibold text-gray-800">Transmission</h2>
              <p className="text-gray-700">{disease.transmission || 'Unknown'}</p>
            </div>

            <div className="rounded-xl bg-gray-50 p-5">
              <h2 className="mb-2 text-lg font-semibold text-gray-800">Prevention</h2>
              <p className="text-gray-700">{disease.prevention || 'Unknown'}</p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default DiseaseDetail;
