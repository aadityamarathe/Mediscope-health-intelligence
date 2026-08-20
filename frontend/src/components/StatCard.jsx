const StatCard = ({ title, value }) => {
  return (
    <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-6 flex flex-col items-center justify-center transition hover:shadow-md">
      <h3 className="text-gray-500 text-sm font-medium uppercase tracking-wider mb-2">{title}</h3>
      <div className="text-3xl font-bold text-gray-800">{value}</div>
    </div>
  );
};

export default StatCard;
