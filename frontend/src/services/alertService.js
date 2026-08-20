import api from "../utils/api";

export const getAlerts = async () => {
    return api.get("/outbreaks");
};
