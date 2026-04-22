// Check environment
const env = document.URL.includes("localhost") ? "development":"production"
// Set base Api based on environment
const baseAPI = env == "development" ? "http://localhost:8000/api" : "" // add your production API URL here

export { env, baseAPI }