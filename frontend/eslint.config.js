// Flat ESLint v9 config.  See
// https://eslint.org/docs/latest/use/configure/configuration-files
import js from "@eslint/js";
import tsParser from "@typescript-eslint/parser";
import tsPlugin from "@typescript-eslint/eslint-plugin";
import reactHooks from "eslint-plugin-react-hooks";
import reactRefresh from "eslint-plugin-react-refresh";
import globals from "globals";

export default [
  {
    ignores: [
      "dist/**",
      "node_modules/**",
      "vite.config.d.ts",
      "vite.config.js",
      "*.mjs",
    ],
  },
  js.configs.recommended,
  // Browser/TS source files
  {
    files: ["src/**/*.{ts,tsx}"],
    languageOptions: {
      parser: tsParser,
      parserOptions: {
        ecmaVersion: 2022,
        sourceType: "module",
        ecmaFeatures: { jsx: true },
      },
      globals: {
        ...globals.browser,
        ...globals.es2022,
        // vitest globals
        describe: "readonly",
        it: "readonly",
        test: "readonly",
        expect: "readonly",
        beforeEach: "readonly",
        afterEach: "readonly",
        beforeAll: "readonly",
        afterAll: "readonly",
        vi: "readonly",
        // react testing library
        screen: "readonly",
        render: "readonly",
        cleanup: "readonly",
        fireEvent: "readonly",
        waitFor: "readonly",
      },
    },
    plugins: {
      "@typescript-eslint": tsPlugin,
      "react-hooks": reactHooks,
      "react-refresh": reactRefresh,
    },
    rules: {
      ...tsPlugin.configs.recommended.rules,
      ...reactHooks.configs.recommended.rules,
      // shadcn/ui components re-export CVA variants alongside the
      // component itself; the "only export components" rule from
      // react-refresh is a false positive for that pattern and is
      // tracked separately by the UI team's typing rules.
      "react-refresh/only-export-components": "off",
      // The project intentionally uses `any` for partial mock casts
      // in test-utils.
      "@typescript-eslint/no-explicit-any": "off",
      // Allow `_`-prefixed unused vars (used in mock signatures).
      "@typescript-eslint/no-unused-vars": [
        "error",
        { argsIgnorePattern: "^_", varsIgnorePattern: "^_" },
      ],
    },
  },
  // Node-side config / build files
  {
    files: ["*.{js,ts,mjs,cjs}", "*.config.{js,ts,mjs,cjs}", "vite.config.ts", "vitest.config.ts"],
    languageOptions: {
      parser: tsParser,
      parserOptions: { ecmaVersion: 2022, sourceType: "module" },
      globals: {
        ...globals.node,
        ...globals.es2022,
      },
    },
    rules: {
      // In Node files, `__dirname` / `require` are valid.  Disable
      // rules that would flag them so existing configs lint clean.
      "no-undef": "off",
    },
  },
];
