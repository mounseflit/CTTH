/** @type {import('next').NextConfig} */
const nextConfig = {
  output: 'standalone',
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
