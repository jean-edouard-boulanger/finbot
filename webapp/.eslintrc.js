const errorOnProd = process.env.NODE_ENV === "prod" ? "error" : "warn";

module.exports = exports = {
  env: {
    browser: true,
    node: true,
  },
  plugins: ["react"],
  extends: ["eslint:recommended", "plugin:react/recommended"],
  parserOptions: {
    ecmaVersion: 2020,
    sourceType: "module",
  },
  rules: {
    "react/prop-types": "off",
    "react/display-name": "off",
    "no-unused-vars": errorOnProd,
  },
};
