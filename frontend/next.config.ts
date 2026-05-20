import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  output: "standalone",
  basePath: process.env.NEXT_PUBLIC_BASE_PATH || "",
  turbopack: {
    root: import.meta.dirname,
  },
};

export default nextConfig;
