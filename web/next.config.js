/** @type {import('next').NextConfig} */
const nextConfig = {
  output: "standalone",
  experimental: {
    proxyTimeout: 120_000,   // 2 min — Ollama can be slow
  },
  async rewrites() {
    return [
      {
        source: "/api/:path*",
        destination: `${process.env.NEXT_PUBLIC_API_URL || "http://api:8000"}/api/:path*`,
      },
    ];
  },
};

module.exports = nextConfig;
