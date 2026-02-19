/** @type {import('next').NextConfig} */
const nextConfig = {
  output: 'standalone',

  // ── Compression ──────────────────────────────────────────────────────────
  // Enables gzip/brotli compression for all responses (HTML, JS, CSS, JSON)
  compress: true,

  // ── Bundle Optimisation ──────────────────────────────────────────────────
  // Removes unused exports from packages that support it (tree-shaking)
  // Particularly effective for lucide-react and recharts
  experimental: {
    optimizePackageImports: ['lucide-react', 'recharts'],
  },

  // ── Production source maps ────────────────────────────────────────────────
  // Disable browser source maps in production to reduce bundle size ~30%
  productionBrowserSourceMaps: false,

  // ── HTTP Headers ─────────────────────────────────────────────────────────
  async headers() {
    return [
      {
        // Aggressive caching for static assets (JS/CSS chunks)
        source: '/_next/static/:path*',
        headers: [
          {
            key: 'Cache-Control',
            value: 'public, max-age=31536000, immutable',
          },
        ],
      },
      {
        // Short cache for API responses served through Next.js
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

  // ── Webpack ───────────────────────────────────────────────────────────────
  webpack(config, { isServer }) {
    if (!isServer) {
      // Split recharts into its own chunk so it only loads when needed
      config.optimization.splitChunks = {
        ...config.optimization.splitChunks,
        cacheGroups: {
          ...(config.optimization.splitChunks?.cacheGroups ?? {}),
          recharts: {
            name: 'recharts',
            test: /[\\/]node_modules[\\/]recharts[\\/]/,
            chunks: 'all',
            priority: 30,
          },
          lucide: {
            name: 'lucide',
            test: /[\\/]node_modules[\\/]lucide-react[\\/]/,
            chunks: 'all',
            priority: 20,
          },
        },
      }
    }
    return config
  },
}

module.exports = nextConfig
