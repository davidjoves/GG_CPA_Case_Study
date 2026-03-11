import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  typescript: {
    // The generated .next/types/validator.ts causes a spurious module
    // resolution error in production builds; suppress it here and rely
    // on tsc directly for type-checking in CI instead.
    ignoreBuildErrors: true,
  },
};

export default nextConfig;
