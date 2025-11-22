<<<<<<< HEAD
<<<<<<< HEAD
import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  /* config options here */
=======
import type { NextConfig } from 'next';

const nextConfig: NextConfig = {
  reactStrictMode: true,
  experimental: {
    typedRoutes: true,
  },
>>>>>>> origin/claude/frontend-content-ui-01SUCiGQU6dN2Z9rPASZfehV
};

export default nextConfig;
=======
import type { NextConfig } from 'next'

const nextConfig: NextConfig = {
  experimental: {
    serverActions: {
      bodySizeLimit: '10mb',
    },
  },
}

export default nextConfig
>>>>>>> origin/claude/prospect-ui-frontend-01F9BktJJ2Zg4J6voVhwdpQH
