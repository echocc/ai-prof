import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  async rewrites() {
    // Use server-side env var for rewrites (runtime, not build-time)
    // Try API_URL first (server-side), then NEXT_PUBLIC_API_URL (build-time), then localhost
    const apiUrl = process.env.API_URL || process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

    console.log('[Next.js Rewrites] API URL:', apiUrl);

    return [
      {
        source: '/api/:path*',
        destination: `${apiUrl}/api/:path*`,
      },
    ];
  },
};

export default nextConfig;
