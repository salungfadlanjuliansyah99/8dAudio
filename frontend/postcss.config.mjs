import postcssNesting from 'postcss-nesting';

export default {
  plugins: {
    '@tailwindcss/postcss': {},
    'postcss-nesting': postcssNesting,
  },
};
