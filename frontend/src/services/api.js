import api from "../utils/api";

export const fetchOutbreakDiseases = async () => {
  const res = await api.get("/outbreaks");
  const data = res.data?.data ?? res.data ?? [];

  // Remove: null, undefined, "unknown"
  const diseases = (Array.isArray(data) ? data : [])
    .map((item) => item?.disease)
    .filter((disease) => 
      disease != null && 
      disease.toString().trim().toLowerCase() !== "unknown" &&
      disease.toString().trim() !== ""
    )
    .map((disease) => disease.toString().trim());

  return [...new Set(diseases)].sort();
};


export default api;
