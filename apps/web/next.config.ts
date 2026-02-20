import path from 'node:path';
import type { NextConfig } from 'next';

const nextConfig: NextConfig = {
  transpilePackages: ['@wishlist/shared-types'],
  turbopack: {
    root: path.join(__dirname, '../..'),
  },
  allowedDevOrigins: ['http://localhost:3000', 'http://127.0.0.1:3000'],
};

export default nextConfig;
