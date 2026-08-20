import { useMemo, useState } from 'react';
import api from '../utils/api';

const STORAGE_KEY = 'alerts_subscriptions';
const REGIONS = [
  'India',
  'USA',
  'Pakistan',
  'Nigeria',
  'South Africa',
  'United Kingdom',
  'Brazil',
  'Yemen',
];

const isValidEmail = (email) =>
  /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email);

const readSubscriptions = () => {
  try {
    const raw = localStorage.getItem(STORAGE_KEY);
    const parsed = raw ? JSON.parse(raw) : [];
    return Array.isArray(parsed) ? parsed : [];
  } catch {
    return [];
  }
};

const Alerts = () => {
  const [email, setEmail] = useState('');
  const [region, setRegion] = useState('');
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');
  const [subscriptionsVersion, setSubscriptionsVersion] = useState(0);

  const subscriptions = useMemo(
    () => readSubscriptions(),
    [subscriptionsVersion],
  );
  const trimmedEmail = email.trim().toLowerCase();
  const isEmailValid = isValidEmail(trimmedEmail);
  const canSubscribe = Boolean(trimmedEmail && isEmailValid && region.trim());

  const handleSubscribe = async () => {
    const trimmedRegion = region.trim();

    setError('');
    setSuccess('');

    if (!trimmedEmail || !isEmailValid) {
      setError('Enter a valid email address');
      return;
    }

    if (!trimmedRegion) {
      setError('Select a region');
      return;
    }

    const existingSubscriptions = readSubscriptions();
    const alreadySubscribed = existingSubscriptions.some(
      (item) =>
        item.email === trimmedEmail &&
        item.region.toLowerCase() === trimmedRegion.toLowerCase(),
    );

    if (alreadySubscribed) {
      setError(`This email is already subscribed for ${trimmedRegion}`);
      return;
    }

    const nextSubscriptions = [
      ...existingSubscriptions,
      {
        email: trimmedEmail,
        region: trimmedRegion,
        subscribedAt: new Date().toISOString(),
      },
    ];

    try {
      await api.post('/alerts/subscribe', {
        email: trimmedEmail,
        region: trimmedRegion,
      });
      
      // Save locally only on backend success
      localStorage.setItem(STORAGE_KEY, JSON.stringify(nextSubscriptions));
      setSubscriptionsVersion((value) => value + 1);
      setEmail('');
      setRegion('');
      setSuccess('Subscribed successfully');
    } catch (error) {
      if (error.response) {
        // Backend rejected the request (400, 409, 500, etc.)
        const message = error.response.data?.message || 'Server error occurred.';
        setError(message);
      } else {
        // Network failure — save locally
        localStorage.setItem(STORAGE_KEY, JSON.stringify(nextSubscriptions));
        setSubscriptionsVersion((value) => value + 1);
        setEmail('');
        setRegion('');
        setSuccess('Subscription saved locally only');
      }
    }
  };

  const handleRemove = (emailToRemove, regionToRemove) => {
    const nextSubscriptions = readSubscriptions().filter(
      (item) =>
        !(
          item.email === emailToRemove &&
          item.region.toLowerCase() === regionToRemove.toLowerCase()
        ),
    );

    localStorage.setItem(STORAGE_KEY, JSON.stringify(nextSubscriptions));
    setSubscriptionsVersion((value) => value + 1);
    setError('');
    setSuccess('');
  };

  return (
    <div className="mx-auto max-w-3xl space-y-8">
      <div className="rounded-xl border border-gray-100 bg-white p-8 shadow-sm">
        <h1 className="mb-2 text-3xl font-bold text-gray-800">Alerts Dashboard</h1>
        <p className="text-gray-600">
          Subscribe for region-based outbreak alerts with a safe frontend-only demo flow.
        </p>

        <div className="mt-6 space-y-5">
          <div>
            <label
              htmlFor="alerts-email"
              className="mb-2 block text-sm font-medium text-gray-700"
            >
              Email Address
            </label>
            <input
              id="alerts-email"
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              placeholder="you@example.com"
              className="w-full rounded-lg border border-gray-300 px-4 py-3 text-sm text-gray-800 shadow-sm transition-all duration-200 focus:border-blue-500 focus:outline-none focus:ring-2 focus:ring-blue-500/20"
            />
          </div>

          <div>
            <label
              htmlFor="alerts-region"
              className="mb-2 block text-sm font-medium text-gray-700"
            >
              Region
            </label>
            <select
              id="alerts-region"
              value={region}
              onChange={(e) => setRegion(e.target.value)}
              className="w-full rounded-lg border border-gray-300 bg-white px-4 py-3 text-sm text-gray-800 shadow-sm transition-all duration-200 focus:border-blue-500 focus:outline-none focus:ring-2 focus:ring-blue-500/20"
            >
              <option value="">Select a region</option>
              {REGIONS.map((regionName) => (
                <option key={regionName} value={regionName}>
                  {regionName}
                </option>
              ))}
            </select>
          </div>

          <button
            type="button"
            onClick={handleSubscribe}
            disabled={!canSubscribe}
            className="inline-flex rounded-lg bg-blue-600 px-6 py-3 text-sm font-medium text-white transition-all duration-200 hover:bg-blue-700 hover:shadow-sm disabled:cursor-not-allowed disabled:bg-gray-300 disabled:hover:shadow-none"
          >
            Subscribe
          </button>

          <p className="text-sm text-gray-500">
            Max 100 alerts per day on free tier
          </p>

          {error ? (
            <div className="rounded-lg border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-600">
              {error}
            </div>
          ) : success ? (
            <div
              className={`rounded-lg border px-4 py-3 text-sm ${
                success === 'Subscribed successfully'
                  ? 'border-green-200 bg-green-50 text-green-700'
                  : 'border-yellow-200 bg-yellow-50 text-yellow-700'
              }`}
            >
              {success}
            </div>
          ) : null}
        </div>
      </div>

      <div className="rounded-xl border border-gray-100 bg-white p-6 shadow-sm">
        <h2 className="mb-4 text-lg font-semibold text-gray-800">Saved Subscriptions</h2>
        {subscriptions.length === 0 ? (
          <p className="text-sm text-gray-500">No local subscriptions saved yet.</p>
        ) : (
          <div className="space-y-4">
            {subscriptions.map((item) => (
              <div
                key={`${item.email}-${item.region}`}
                className="flex flex-col gap-3 rounded-lg border border-gray-100 bg-gray-50 px-4 py-3 text-sm text-gray-700 sm:flex-row sm:items-center sm:justify-between"
              >
                <div className="space-y-1">
                  <span className="block font-medium text-gray-800">{item.email}</span>
                  <span>{item.region}</span>
                </div>
                <button
                  type="button"
                  onClick={() => handleRemove(item.email, item.region)}
                  className="inline-flex rounded-lg border border-red-200 bg-white px-3 py-2 text-sm font-medium text-red-600 transition-all duration-200 hover:border-red-300 hover:bg-red-50"
                >
                  Remove
                </button>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
};

export default Alerts;
