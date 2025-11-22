/** @type {import('next').NextConfig} */
const nextConfig = {
<<<<<<< HEAD
<<<<<<< HEAD
<<<<<<< HEAD
  output: 'standalone',
  reactStrictMode: true,

  // Image optimization
  images: {
    remotePatterns: [
      {
        protocol: 'https',
        hostname: '**.githubusercontent.com',
      },
      {
        protocol: 'https',
        hostname: '**.googleusercontent.com',
      },
    ],
  },

  // Environment variables exposed to browser
  env: {
    NEXT_PUBLIC_APP_NAME: 'Sales OS',
  },

  // Headers for security
  async headers() {
    return [
      {
        source: '/:path*',
        headers: [
          {
            key: 'X-DNS-Prefetch-Control',
            value: 'on',
          },
          {
            key: 'X-Frame-Options',
            value: 'SAMEORIGIN',
          },
          {
            key: 'X-Content-Type-Options',
            value: 'nosniff',
          },
        ],
      },
    ];
  },

  // Redirects
  async redirects() {
    return [
      {
        source: '/home',
        destination: '/dashboard',
        permanent: true,
=======
  reactStrictMode: true,
  async rewrites() {
    return [
      {
        source: '/api/:path*',
        destination: 'http://localhost:8000/api/:path*',
>>>>>>> origin/claude/pdf-deck-renderer-01QnNpwQFSMU7WYfb9J8gfKi
      },
    ];
=======
  reactStrictMode: true,
  experimental: {
    serverActions: true,
>>>>>>> origin/claude/transcript-ui-frontend-01827GXMtwFgZZZSpTQu33aT
  },
};

module.exports = nextConfig;
=======
  reactStrictMode: true,
  experimental: {
    serverActions: true,
  },
}

module.exports = nextConfig
>>>>>>> origin/claude/analytics-dashboard-01M24DLkEb1rR8wBY9c26gKw
