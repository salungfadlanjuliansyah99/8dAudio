import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  async rewrites() {
    return [
      {
        source: "/api/:path*",
        destination: "https://a8d-audio-converter-1b5c2e52.fastapicloud.dev/api/:path*",
      },
    ];
  },
};

export default nextConfig;
