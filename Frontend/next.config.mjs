/** @type {import('next').NextConfig} */
const nextConfig = {
  output: 'export',
  
  // Configure images for static handling
  images: {
    unoptimized: true, // Required for static export
    domains: [],        // Add any domains needed for external images
    remotePatterns: []  // Configure any remote image patterns if needed
  },
  
  // Trailing slash is often recommended for static sites
  trailingSlash: true,
  
  // Environment variable configuration
  env: {
    // You can add public environment variables here
    // NEXT_PUBLIC_API_URL: process.env.NEXT_PUBLIC_API_URL,
  },
  
  // Disable certain features not supported in static exports if needed
  experimental: {
    // Any experimental features you want to enable
  }
};

export default nextConfig;
