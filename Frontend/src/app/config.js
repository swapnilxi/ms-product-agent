// lib/config.js
export const PRIMARY_COLOR = process.env.NEXT_PUBLIC_PRIMARY_COLOR || "#6366F1";

 // Backend API Configuration
 export const API = {
    baseUrl: process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000",

//   baseUrl: process.env.NODE_ENV === "production"
//   ? process.env.NEXT_PUBLIC_API_URL: "http://localhost:8000",
  };



// Theme Configuration
export const THEME = {
    primaryColor: process.env.NEXT_PUBLIC_PRIMARY_COLOR || "#6366F1", // Default fallback color
    secondaryColor: process.env.NEXT_PUBLIC_SECONDARY_COLOR || "#F9FAFB",
  };
  
 
  
  // Agent Endpoints
  export const AGENT_ENDPOINTS = {
    researchAgent: "/research-agent",
    productAgent: "/product-agent",
    marketingAgent: "/marketing-agent",
    runPipeline: "/run-pipeline",
    chooseAgents: "/choose-agent",
    getReports: "/get-reports",
    downloadReport: "/download-report",
  };
  
  // Default Instructions (optional)
  export const DEFAULT_INSTRUCTIONS = {
    research: "Conduct market and technical research for the given companies.",
    product: "Brainstorm innovative product ideas for the given companies.",
    marketing: "Create a marketing strategy for the product.",
  };
  
  // System Labels (Optional)
  export const LABELS = {
    generateProductIdea: "Generate Product Idea",
    getResearchReport: "Get Research Report",
    generateMarketingPlan: "Generate Marketing Plan",
    runFullPipeline: "Run Full Pipeline",
  };
  