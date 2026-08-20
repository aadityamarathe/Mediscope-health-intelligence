import api from "../utils/api";

export const getDiseases = async () => {
    return api.get("/diseases");
};
