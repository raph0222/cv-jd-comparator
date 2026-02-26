module.exports = {
  root: true,
  env: {
    browser: true,
    es2022: true,
    node: true
  },
  parser: "vue-eslint-parser",
  parserOptions: {
    ecmaVersion: "latest",
    sourceType: "module"
  },
  extends: ["eslint:recommended", "plugin:vue/vue3-essential"],
  rules: {
    "vue/multi-word-component-names": "off",
    semi: ["error", "never"]
  }
};
