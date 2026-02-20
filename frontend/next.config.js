/** @type {import('next').NextConfig} */
const nextConfig = {
  output: 'standalone',

  // ── Compression ──────────────────────────────────────────────────────────
  compress: true,

  // ── Production source maps ────────────────────────────────────────────────
  productionBrowserSourceMaps: false,

  // ── HTTP Headers ─────────────────────────────────────────────────────────
  async headers() {
    return [
      {
        source: '/_next/static/:path*',
        headers: [
          {
            key: 'Cache-Control',
            value: 'public, max-age=31536000, immutable',
          },
        ],
      },
      {
        source: '/api/:path*',
        headers: [
          {
            key: 'Cache-Control',
            value: 'no-store',
          },
        ],
      },
    ]
  },

  images: {
    remotePatterns: [
      {
        protocol: 'https',
        hostname: 'www.ctth.ma',
        pathname: '/wp-content/**',
      },
    ],
  },

}

module.exports = nextConfig
