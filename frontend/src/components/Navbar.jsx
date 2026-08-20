import { Link } from 'react-router-dom';

const Navbar = () => {
  return (
    <nav className="p-4 bg-blue-600 text-white flex justify-between items-center">
      <div className="font-bold text-xl">
        <Link to="/">MediScope</Link>
      </div>
      <div className="space-x-4">
        <Link to="/" className="hover:underline">Home</Link>
        <Link to="/map" className="hover:underline">Map</Link>
        <Link to="/compare" className="hover:underline">Compare</Link>
        <Link to="/search" className="hover:underline">Search</Link>
        <Link to="/alerts" className="hover:underline">Alerts</Link>
        <Link to="/analytics" className="hover:underline">Analytics</Link>
      </div>
    </nav>
  );
};

export default Navbar;
