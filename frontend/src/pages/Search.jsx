import { useState } from 'react';
import { Link } from 'react-router-dom';

import api from '../utils/api';
import Loader from '../components/Loader';

const Search = () => {
  const [query, setQuery] = useState('');
  const [results, setResults] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const handleSearch = async (e) => {
    e.preventDefault();
    if (!query.trim()) return;

    try {
      setLoading(true);
      setError(null);
      
      const response = await api.get(`/search?symptoms=${encodeURIComponent(query)}`);
      
      if (response.data.success) {
        setResults(response.data.data);
      } else {
        setError(response.data.message || 'Failed to perform search.');
      }
    } catch (err) {
      setError(err.response?.data?.message || 'Error executing search.');
    } finally {
      setLoading(false);
    }
  };

  const getSeverityStyle = (severity) => {
    switch (severity?.toLowerCase()) {
      case 'high': return 'bg-red-100 text-red-800';
      case 'medium': return 'bg-orange-100 text-orange-800';
      case 'low': return 'bg-green-100 text-green-800';
      default: return 'bg-gray-100 text-gray-800';
    }
  };

  return (
    <div className="max-w-4xl mx-auto space-y-8">
      {/* TOP: Input field & Search button & Disclaimer */}
      <div className="bg-white p-8 rounded-xl shadow-sm border border-gray-100">
        <h1 className="text-3xl font-bold text-gray-800 mb-2">Symptom Search</h1>
        <p className="text-gray-600 mb-6">Enter symptoms separated by commas (e.g., fever, rash, headache) to find potential disease matches.</p>
        
        <form onSubmit={handleSearch} className="flex flex-col sm:flex-row gap-4">
          <input
            type="text"
            className="flex-grow p-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 outline-none transition"
            placeholder="fever, headache, joint pain..."
            value={query}
            onChange={(e) => setQuery(e.target.value)}
          />
          <button 
            type="submit" 
            className="bg-blue-600 text-white px-8 py-3 rounded-lg font-medium hover:bg-blue-700 transition shadow-sm whitespace-nowrap"
          >
            Search
          </button>
        </form>

        <div className="mt-6 p-4 bg-yellow-50 border border-yellow-200 rounded-lg text-yellow-800 text-sm flex items-start gap-3">
          <svg className="w-5 h-5 flex-shrink-0 mt-0.5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z"></path></svg>
          <p>
            <strong className="block mb-1">IMPORTANT DISCLAIMER</strong>
            This tool matches symptoms to diseases for informational purposes only. It is <strong>Not a medical diagnosis tool</strong>. Always consult a healthcare professional.
          </p>
        </div>
      </div>

      {/* RESULT SECTION */}
      {loading && <Loader />}

      {error && (
        <div className="p-4 bg-red-50 text-red-600 rounded-lg border border-red-200 shadow-sm">
          {error}
        </div>
      )}

      {results && !loading && (
        <div className="space-y-4">
          <h2 className="text-xl font-semibold text-gray-700">Search Results ({results.length})</h2>
          
          {results.length === 0 ? (
            <div className="p-8 text-center bg-white rounded-xl shadow-sm border border-gray-100 text-gray-500">
              No matching diseases found for those symptoms.
            </div>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              {results.map((disease) => (
                <div key={disease.name} className="bg-white rounded-xl shadow-sm border border-gray-100 p-6 flex flex-col gap-3 hover:shadow-md transition">
                  <div className="flex justify-between items-start">
                    <Link to={`/disease/${encodeURIComponent(disease.name.toLowerCase())}`}>
                      <h3 className="text-xl font-bold text-gray-800 capitalize hover:text-blue-600 transition">
                        {disease.name}
                      </h3>
                    </Link>
                    {disease.severity && (
                      <span className={`px-2.5 py-1 rounded-full text-xs font-semibold ${getSeverityStyle(disease.severity)}`}>
                        {disease.severity.toUpperCase()}
                      </span>
                    )}
                  </div>
                  
                  <div>
                    <h4 className="text-sm font-semibold text-gray-500 uppercase tracking-wider mb-2">Matched Symptoms</h4>
                    <ul className="list-disc list-inside text-gray-700">
                      {disease.symptoms?.slice(0, 3).map((sym, i) => (
                        <li key={i}>{sym}</li>
                      ))}
                      {disease.symptoms?.length > 3 && (
                        <li className="text-sm text-gray-500 italic mt-1 list-none">+ {disease.symptoms.length - 3} more</li>
                      )}
                    </ul>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      )}
    </div>
  );
};

export default Search;
