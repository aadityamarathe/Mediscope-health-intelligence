import { useNavigate, Link } from 'react-router-dom';

const OutbreakCard = ({ outbreak }) => {
  const navigate = useNavigate();

  // --- ADDED: detect unknown disease ---
  const isUnknown = outbreak.disease === 'Unknown Disease';

  const getSeverityColor = (severity) => {
    switch ((severity || '').toLowerCase()) {
      case 'high':
        return 'bg-red-100 text-red-800 border-red-200';
      case 'medium':
        return 'bg-orange-100 text-orange-800 border-orange-200';
      default:
        return 'bg-green-100 text-green-800 border-green-200';
    }
  };

  const severity = (outbreak.severity || 'low').toLowerCase();
  const severityClass = getSeverityColor(severity);
  const formattedCases = outbreak.case_count != null
    ? new Intl.NumberFormat().format(outbreak.case_count)
    : 'Unknown';
  const formattedDate = outbreak.date
    ? new Intl.DateTimeFormat('en-GB', {
        day: '2-digit',
        month: 'short',
        year: 'numeric',
      }).format(new Date(outbreak.date))
    : 'Unknown';

  // --- ADDED: display label — shows "Unidentified Disease" in UI only ---
  const displayDisease = isUnknown ? 'Unidentified Disease' : outbreak.disease;

  // --- ADDED: conditional click handler ---
  const handleClick = () => {
    if (!isUnknown) {
      navigate(`/disease/${outbreak.disease}`);
    }
  };

  return (
    <div
      onClick={handleClick}
      // --- CHANGED: conditional styles for unknown vs known cards ---
      className={`group rounded-xl border p-5 shadow-sm transition-all ${
        isUnknown
          ? 'cursor-not-allowed border-gray-200 bg-gray-50 opacity-70'
          : 'cursor-pointer border-gray-100 bg-white hover:-translate-y-0.5 hover:shadow-lg'
      }`}
      // --- ADDED: tooltip for unknown disease cards ---
      title={isUnknown ? 'Detailed information not available' : undefined}
    >
      <div className="mb-4 flex items-start justify-between gap-4">
        <div className="min-w-0">
            {!isUnknown ? (
              <Link
                to={`/disease/${outbreak.disease}`}
                onClick={(e) => e.stopPropagation()}
                className="text-gray-900 hover:text-blue-600 group-hover:text-blue-600 transition-colors"
              >
                {displayDisease}
              </Link>
            ) : (
              <span className="text-gray-500 italic">
                {displayDisease}
              </span>
            )}
          <p className="mt-1 text-sm font-medium text-gray-600">
            {outbreak.country || 'Unknown country'}
          </p>
        </div>
        <span className={`rounded-full border px-2.5 py-1 text-xs font-semibold uppercase ${severityClass}`}>
          {severity}
        </span>
      </div>

      <div className="space-y-3 text-sm text-gray-700">
        <div className="flex items-center justify-between gap-3">
          <span className="font-medium text-gray-500">Cases</span>
          <span className="font-semibold text-gray-900">{formattedCases}</span>
        </div>
        <div className="flex items-center justify-between gap-3">
          <span className="font-medium text-gray-500">Date</span>
          <span className="font-semibold text-gray-900">{formattedDate}</span>
        </div>
      </div>
    </div>
  );
};

export default OutbreakCard;
