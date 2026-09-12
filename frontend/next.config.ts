import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  /* Standalone output for optimized Docker production image */
  output: "standalone",
};

export default nextConfig;
