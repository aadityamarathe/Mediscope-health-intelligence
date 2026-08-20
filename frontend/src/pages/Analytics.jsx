import React, { useEffect, useState } from 'react';
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  BarElement,
  ArcElement,
  Title,
  Tooltip,
  Legend,
  Filler,
} from 'chart.js';
import { Line, Bar, Doughnut } from 'react-chartjs-2';
import api from '../services/api';
import Loader from '../components/Loader';

ChartJS.register(
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  BarElement,
  ArcElement,
  Title,
  Tooltip,
  Legend,
  Filler
);

const Analytics = () => {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    const fetchAnalytics = async () => {
      try {
        setLoading(true);
        const response = await api.get('/analytics/activity');
        setData(response.data.data);
      } catch (err) {
        setError('Failed to load analytics data.');
      } finally {
        setLoading(false);
      }
    };
    fetchAnalytics();
  }, []);

  if (loading) {
    return (
      <div className="mx-auto max-w-7xl pt-10">
        <Loader />
      </div>
    );
  }

  if (error) {
    return (
      <div className="mx-auto max-w-7xl pt-10">
        <div className="rounded-lg border border-red-200 bg-red-50 p-6 text-red-600 shadow-sm">
          <h2 className="mb-1 text-lg font-bold">Error</h2>
          <p>{error}</p>
        </div>
      </div>
    );
  }

  // --- Articles Over Time (Line Chart) ---
  const lineChartData = {
    labels: data.articles_over_time.map((d) => d.date),
    datasets: [
      {
        label: 'Articles Collected',
        data: data.articles_over_time.map((d) => d.count),
        borderColor: '#3b82f6',
        backgroundColor: 'rgba(59, 130, 246, 0.1)',
        tension: 0.35,
        fill: true,
      },
    ],
  };

  // --- Top Diseases (Bar Chart) ---
  const diseaseChartData = {
    labels: data.top_diseases.map((d) => d.disease),
    datasets: [
      {
        label: 'Reports',
        data: data.top_diseases.map((d) => d.count),
        backgroundColor: '#f59e0b',
      },
    ],
  };

  // --- Reports by Source (Doughnut Chart) ---
  const sourceChartData = {
    labels: data.reports_by_source.map((d) => d.source),
    datasets: [
      {
        data: data.reports_by_source.map((d) => d.count),
        backgroundColor: ['#10b981', '#ef4444', '#6366f1', '#f59e0b', '#8b5cf6'],
      },
    ],
  };

  // --- Top Countries - Disease Diversity (Bar Chart) ---
  const countryChartData = {
    labels: data.top_countries.map((d) => d.country),
    datasets: [
      {
        label: 'Distinct Diseases Tracked',
        data: data.top_countries.map((d) => d.count),
        backgroundColor: '#8b5cf6',
      },
    ],
  };

  return (
    <div className="mx-auto max-w-7xl space-y-10">
      <section>
        <h1 className="mb-2 text-3xl font-bold text-gray-900">
          Outbreak Activity Analytics
        </h1>
        <div className="rounded-lg border border-yellow-200 bg-yellow-50 p-4 text-sm text-yellow-800 shadow-sm">
          <p>
            <strong>Disclaimer:</strong> Data reflects outbreak reports collected by
            MediScope sources and does not represent epidemiological disease
            progression.
          </p>
        </div>
      </section>

      <div className="grid grid-cols-1 gap-8 lg:grid-cols-2">
        {/* Articles Collected Over Time */}
        <div className="rounded-xl border border-gray-200 bg-white p-6 shadow-sm">
          <h2 className="mb-4 text-lg font-bold text-gray-900">
            Articles Collected Over Time
          </h2>
          <div className="h-[300px]">
            <Line
              data={lineChartData}
              options={{ maintainAspectRatio: false, plugins: { legend: { display: false } } }}
            />
          </div>
        </div>

        {/* Reports by Source */}
        <div className="rounded-xl border border-gray-200 bg-white p-6 shadow-sm">
          <h2 className="mb-4 text-lg font-bold text-gray-900">
            Reports by Source
          </h2>
          <div className="h-[300px] flex items-center justify-center">
            <Doughnut
              data={sourceChartData}
              options={{ maintainAspectRatio: false }}
            />
          </div>
        </div>

        {/* Top Diseases */}
        <div className="rounded-xl border border-gray-200 bg-white p-6 shadow-sm">
          <h2 className="mb-4 text-lg font-bold text-gray-900">
            Most Reported Diseases
          </h2>
          <div className="h-[300px]">
            <Bar
              data={diseaseChartData}
              options={{
                indexAxis: 'y',
                maintainAspectRatio: false,
                plugins: { legend: { display: false } },
              }}
            />
          </div>
        </div>

        {/* Countries with Highest Disease Diversity */}
        <div className="rounded-xl border border-gray-200 bg-white p-6 shadow-sm">
          <h2 className="mb-4 text-lg font-bold text-gray-900">
            Countries with Highest Disease Diversity
          </h2>
          <div className="h-[300px]">
            <Bar
              data={countryChartData}
              options={{
                indexAxis: 'y',
                maintainAspectRatio: false,
                plugins: { legend: { display: false } },
              }}
            />
          </div>
        </div>
      </div>
    </div>
  );
};

export default Analytics;
