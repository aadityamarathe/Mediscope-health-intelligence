# Frontend Implementation

The frontend of MediScope is a Single Page Application (SPA) built using React 19 and Vite. It serves as the visual presentation layer, allowing users to interact with the backend data through maps, charts, and data tables.

## Technology Choices
- **React 19 & Vite**: Chosen for extremely fast Hot Module Replacement (HMR) during development and highly optimized production builds.
- **TailwindCSS**: Utility-first CSS framework used for rapid UI development without writing custom CSS files. Provides responsive design out-of-the-box.
- **Leaflet**: Lightweight, open-source JavaScript library for mobile-friendly interactive maps.
- **Chart.js**: Used for rendering responsive, customizable bar and line charts.

## Core Pages (`frontend/src/pages/`)

### 1. `Map.jsx` (Global Outbreak Map)
- **Purpose**: The primary visual interface of the application, rendering a global map dotted with outbreak markers.
- **UI Components**: Leaflet Map Container, Custom Map Markers, Interactive Tooltips, Sidebar Filter Panel.
- **State Variables**: 
  - `outbreaks` (array): Holds the current list of outbreaks.
  - `filters` (object): Holds current selections for disease type, region, and date range.
  - `loading` (boolean): Controls the loading spinner overlay.
- **Hooks**: `useEffect` (to fetch data on mount and filter changes), `useState` (to manage filters and outbreak data).
- **API Calls**: `GET /api/outbreaks` (filtered by query parameters).
- **User Flow**: User lands on the page -> Map renders default outbreaks -> User changes a filter in the sidebar -> State updates -> `useEffect` triggers a new API call -> Map re-renders with new markers.

### 2. `Analytics.jsx` (Trend Analysis)
- **Purpose**: Displays statistical trends and historical occurrences of diseases.
- **UI Components**: Chart.js Bar Charts, Line Charts, Statistical summary cards.
- **State Management**: `summaryData`, `timeSeriesData`.
- **API Calls**: `GET /api/outbreaks/summary`.
- **Styling**: Tailwind grids to align charts symmetrically.

### 3. `Compare.jsx` (Side-by-Side Comparison)
- **Purpose**: Allows users to select two distinct diseases or regions and compare their statistics side-by-side.
- **UI Components**: Dual Dropdown Selectors, Split-screen data tables, Radar charts.
- **Hooks**: Requires complex state management for two independent data sources (`selectionA`, `selectionB`, `dataA`, `dataB`).
- **User Flow**: User selects Disease A and Disease B -> Application fetches data for both -> Renders comparative metrics (e.g., total cases, severity differences).

### 4. `Alerts.jsx` (Subscription Management)
- **Purpose**: Interface for users to subscribe to email notifications for specific regions or pathogens.
- **UI Components**: Subscription Form (Email input, Region dropdown, Disease multi-select), Success/Error Toasts.
- **API Calls**: `POST /api/alerts/subscribe`.
- **User Interaction**: Form validation prevents submission of invalid emails. On success, a toast notification confirms the subscription.

### 5. `DiseaseDetail.jsx` & `Search.jsx`
- **Purpose**: Provides deep-dive information into a specific disease (symptoms, historical severity, global distribution). `Search.jsx` provides a global search bar to quickly jump to these detail pages.
- **API Calls**: `GET /api/diseases/<name>`.
- **Navigation**: Uses React Router's `useNavigate` and `useParams` to route dynamically based on the searched disease.

## Services Layer (`frontend/src/services/`)
To keep React components clean and focused purely on UI rendering, all `fetch` or `axios` calls are abstracted into service modules.
- **`api.js`**: Contains the configured Axios instance, defining the `baseURL` (e.g., `http://localhost:5000/api`) and default headers.
- **Error Handling**: The service layer catches network errors and returns standardized error objects to the components, which then trigger UI toast notifications.
