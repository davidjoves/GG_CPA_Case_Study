const BASE_URL =
  process.env.NEXT_PUBLIC_BASE_URL ||
  (process.env.NODE_ENV === "development"
    ? "http://localhost:3000"
    : "");


const API_PATHS = {
    CALCULATE: `${BASE_URL}/api/calculate`,
};

const API_URLS = {
    CALCULATE: `${BASE_URL}${API_PATHS.CALCULATE}`,
};

export const API = API_URLS;