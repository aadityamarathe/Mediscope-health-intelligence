import { useEffect, useMemo, useState } from 'react';
import { Link, useSearchParams } from 'react-router-dom';

import api from '../utils/api';
import Loader from '../components/Loader';

const severityStyle = (severity) => {
  switch ((severity || '').toLowerCase()) {
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

const normalizeText = (value) => {
  if (Array.isArray(value)) {
    return value.map((item) => String(item).trim().toLowerCase()).join(', ');
  }

  return String(value || '').trim().toLowerCase();
};

const formatValue = (field, value) => {
  if (field === 'severity') {
    return value || 'Unknown';
  }

  if (field === 'total_cases' || field === 'recorded_outbreaks') {
    if (value == null) {
      return '0';
    }
    return new Intl.NumberFormat().format(value);
  }

  if (Array.isArray(value)) {
    return value.length ? value.join(', ') : 'Unknown';
  }

  return value || 'Unknown';
};

const renderSymptoms = (value) => {
  const symptoms = Array.isArray(value)
    ? value
    : String(value || '')
        .split(',')
        .map((item) => item.trim())
        .filter(Boolean);

  if (!symptoms.length) {
    return <span className="text-gray-500">Unknown</span>;
  }

  return (
    <div className="flex flex-wrap gap-2">
      {symptoms.map((symptom) => (
        <span
          key={symptom}
          className="rounded bg-gray-100 px-2 py-1 text-sm text-gray-700"
        >
          {symptom}
        </span>
      ))}
    </div>
  );
};

const Compare = () => {
  const [searchParams] = useSearchParams();
  const [diseases, setDiseases] = useState([]);
  const [diseaseOne, setDiseaseOne] = useState('');
  const [diseaseTwo, setDiseaseTwo] = useState('');
  const [comparison, setComparison] = useState(null);
  const [loadingDiseases, setLoadingDiseases] = useState(true);
  const [loadingComparison, setLoadingComparison] = useState(false);
  const [error, setError] = useState(null);

  useEffect(() => {
    const fetchDiseases = async () => {
      try {
        setLoadingDiseases(true);
        setError(null);

        const response = await api.get('/diseases');
        const items = response.data?.success ? response.data.data : [];
        const names = (Array.isArray(items) ? items : [])
          .map((item) => item?.name)
          .filter((name) => typeof name === 'string' && name.trim())
          .sort((a, b) => a.localeCompare(b));

        setDiseases(names);

        const prefilled = searchParams.get('d1');
        if (prefilled) {
          const matched = names.find(
            (name) => name.toLowerCase() === prefilled.trim().toLowerCase(),
          );
          if (matched) {
            setDiseaseOne(matched);
          }
        }
      } catch (err) {
        setError(err.response?.data?.message || 'Failed to load diseases.');
      } finally {
        setLoadingDiseases(false);
      }
    };

    fetchDiseases();
  }, [searchParams]);

  const rows = useMemo(() => {
    if (!comparison?.d1 || !comparison?.d2) {
      return [];
    }

    return [
      { label: 'Total Cases', field: 'total_cases' },
      { label: 'Recorded Outbreaks', field: 'recorded_outbreaks' },
      { label: 'Severity', field: 'severity' },
      { label: 'Symptoms', field: 'symptoms' },
      { label: 'Transmission', field: 'transmission' },
      { label: 'Prevention', field: 'prevention' },
    ];
  }, [comparison]);

  useEffect(() => {
    if (!diseaseOne || !diseaseTwo) {
      setComparison(null);
      setLoadingComparison(false);
      return;
    }

    if (diseaseOne === diseaseTwo) {
      setComparison(null);
      setLoadingComparison(false);
      setError('Select two different diseases');
      return;
    }

    const fetchComparison = async () => {
      try {
        setLoadingComparison(true);
        setError(null);

        const response = await api.get('/compare', {
          params: {
            d1: diseaseOne,
            d2: diseaseTwo,
          },
        });

        if (response.data?.success) {
          setComparison(response.data.data);
        } else {
          setComparison(null);
          setError('Failed to load comparison');
        }
      } catch (err) {
        setComparison(null);
        setError('Failed to load comparison');
      } finally {
        setLoadingComparison(false);
      }
    };

    fetchComparison();
  }, [diseaseOne, diseaseTwo]);

  return (
    <div className="mx-auto max-w-6xl space-y-8">
      <div className="rounded-xl border border-gray-100 bg-white p-8 shadow-sm">
        <h1 className="mb-2 text-3xl font-bold text-gray-800">Compare Diseases</h1>
        <p className="text-gray-600">
          Choose two diseases to compare their severity, symptoms, transmission,
          and prevention guidance.
        </p>

        <div className="mt-6 grid grid-cols-1 gap-4 md:grid-cols-2">
          <div>
            <label
              htmlFor="disease-one"
              className="mb-2 block text-sm font-medium text-gray-700"
            >
              Disease 1
            </label>
            <select
              id="disease-one"
              value={diseaseOne}
              onChange={(e) => setDiseaseOne(e.target.value)}
              disabled={loadingDiseases}
              className="w-full rounded-lg border border-gray-300 bg-white px-4 py-3 text-sm text-gray-800 shadow-sm transition-all duration-200 focus:border-blue-500 focus:outline-none focus:ring-2 focus:ring-blue-500/20 disabled:cursor-not-allowed disabled:bg-gray-50"
            >
              <option value="">Select disease</option>
              {diseases.map((disease) => (
                <option key={disease} value={disease}>
                  {disease}
                </option>
              ))}
            </select>
          </div>

          <div>
            <label
              htmlFor="disease-two"
              className="mb-2 block text-sm font-medium text-gray-700"
            >
              Disease 2
            </label>
            <select
              id="disease-two"
              value={diseaseTwo}
              onChange={(e) => setDiseaseTwo(e.target.value)}
              disabled={loadingDiseases}
              className="w-full rounded-lg border border-gray-300 bg-white px-4 py-3 text-sm text-gray-800 shadow-sm transition-all duration-200 focus:border-blue-500 focus:outline-none focus:ring-2 focus:ring-blue-500/20 disabled:cursor-not-allowed disabled:bg-gray-50"
            >
              <option value="">Select disease</option>
              {diseases.map((disease) => (
                <option key={disease} value={disease}>
                  {disease}
                </option>
              ))}
            </select>
          </div>
        </div>
      </div>

      {loadingDiseases && <Loader />}

      {loadingComparison && !loadingDiseases && (
        <div className="rounded-xl border border-gray-100 bg-white p-10 text-center text-gray-500 shadow-sm">
          <div className="flex flex-col items-center gap-3">
            <div className="h-8 w-8 animate-spin rounded-full border-4 border-gray-200 border-t-blue-600" />
            <p>Comparing...</p>
          </div>
        </div>
      )}

      {error && !loadingDiseases && !loadingComparison && (
        <div className="rounded-lg border border-red-200 bg-red-50 p-4 text-red-600 shadow-sm">
          {error}
        </div>
      )}

      {!loadingDiseases && !loadingComparison && !comparison && !error && (
        <div className="rounded-xl border border-gray-100 bg-white p-10 text-center text-gray-500 shadow-sm">
          Select two diseases to compare
        </div>
      )}

      {comparison?.d1 &&
        comparison?.d2 &&
        !loadingComparison &&
        diseaseOne !== diseaseTwo && (
        <div className="space-y-6">
          <div className="overflow-hidden rounded-xl border border-gray-100 bg-white shadow-md transition-shadow duration-200 hover:shadow-lg">
            <div className="overflow-x-auto">
              <table className="min-w-full border-separate border-spacing-y-3">
                <thead className="bg-gray-50">
                  <tr>
                    <th className="px-4 py-4 text-left text-sm font-bold text-gray-800">
                      Field
                    </th>
                    <th className="px-4 py-4 text-left text-sm font-semibold text-gray-700 capitalize">
                      <Link
                        to={`/disease/${encodeURIComponent(comparison.d1.name)}`}
                        className="text-blue-600 transition duration-200 hover:text-blue-700 hover:underline"
                      >
                        {comparison.d1.name}
                      </Link>
                    </th>
                    <th className="px-4 py-4 text-left text-sm font-semibold text-gray-700 capitalize">
                      <Link
                        to={`/disease/${encodeURIComponent(comparison.d2.name)}`}
                        className="text-blue-600 transition duration-200 hover:text-blue-700 hover:underline"
                      >
                        {comparison.d2.name}
                      </Link>
                    </th>
                  </tr>
                </thead>
                <tbody>
                  {rows.map((row) => {
                    const firstValue = comparison.d1[row.field];
                    const secondValue = comparison.d2[row.field];
                    const isDifferent =
                      normalizeText(firstValue) !== normalizeText(secondValue);

                    return (
                      <tr key={row.field} className="align-top">
                        <td className="rounded-l-xl border-y border-gray-100 bg-gray-50 px-4 py-4 text-sm font-bold text-gray-800">
                          {row.label}
                        </td>
                        <td className="border-y border-gray-100 bg-white px-4 py-4 text-sm text-gray-700">
                          {row.field === 'severity' ? (
                            <span className={`inline-flex rounded-full border px-3 py-1 text-sm font-bold uppercase ${severityStyle(firstValue)}`}>
                              {formatValue(row.field, firstValue)}
                            </span>
                          ) : row.field === 'symptoms' ? (
                            renderSymptoms(firstValue)
                          ) : (
                            <div className="whitespace-pre-line leading-7 font-medium">
                              {formatValue(row.field, firstValue)}
                            </div>
                          )}
                        </td>
                        <td className={`rounded-r-xl border-y border-r border-gray-100 bg-white px-4 py-4 text-sm text-gray-700 ${isDifferent ? 'bg-red-50' : ''}`}>
                          {row.field === 'severity' ? (
                            <span className={`inline-flex rounded-full border px-3 py-1 text-sm font-bold uppercase ${severityStyle(secondValue)}`}>
                              {formatValue(row.field, secondValue)}
                            </span>
                          ) : row.field === 'symptoms' ? (
                            renderSymptoms(secondValue)
                          ) : (
                            <div className="whitespace-pre-line leading-7 font-medium">
                              {formatValue(row.field, secondValue)}
                            </div>
                          )}
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
          </div>

          <div className="rounded-xl border border-gray-100 bg-white p-6 shadow-sm">
            <h2 className="mb-4 text-xl font-bold text-gray-800">Key Differences</h2>
            {comparison.key_differences?.length ? (
              <ul className="space-y-3 text-sm leading-7 text-gray-700">
                {comparison.key_differences.map((insight) => (
                  <li key={insight} className="flex items-start gap-3">
                    <span className="mt-2 h-2 w-2 flex-shrink-0 rounded-full bg-blue-500" />
                    <span>{insight}</span>
                  </li>
                ))}
              </ul>
            ) : (
              <p className="text-sm text-gray-500">
                No major differences were detected from the available disease records.
              </p>
            )}
          </div>
        </div>
      )}
    </div>
  );
};

export default Compare;
