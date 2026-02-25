import { defineConfig, globalIgnores } from "eslint/config";

const eslintConfig = defineConfig([
  ...require("eslint-config-next/core-web-vitals"),
  ...require("eslint-config-next/typescript"),
  // Override default ignores of eslint-config-next.
  globalIgnores([
    // Default ignores of eslint-config-next:
    ".next/**",
    "out/**",
    "build/**",
    "next-env.d.ts",
  ]),
]);

export default eslintConfig;
