require("dotenv").config();

const HtmlWebpackPlugin = require("html-webpack-plugin");
const { WebpackAssetsManifest } = require("webpack-assets-manifest");
const mime = require("mime-types");
const MiniCssExtractPlugin = require("mini-css-extract-plugin");
const path = require("path");
const { execSync } = require("child_process");

const isProd = process.env.NODE_ENV === "production";

module.exports = {
  mode: isProd ? "production" : "development",
  entry: "./src/index.tsx",
  output: {
    publicPath: isProd ? "https://hel1.your-objectstorage.com/habra-adm/" : "/",
    filename: "[name].[contenthash].js",
    assetModuleFilename: "[name].[contenthash][ext][query]",
    clean: true,
    crossOriginLoading: "anonymous",
  },
  resolve: {
    extensions: [".js", ".jsx", ".ts", ".tsx"],
    alias: {
      "react": "preact/compat",
      "react-dom/test-utils": "preact/test-utils",
      "react-dom": "preact/compat", // Must be below test-utils
      "react/jsx-runtime": "preact/jsx-runtime",
    },
  },
  devtool: isProd ? false : "source-map",
  module: {
    rules: [
      {
        test: /\.tsx?$/,
        exclude: /node_modules/,
        use: {
          loader: "babel-loader",
          options: {
            generatorOpts: {
              jsescOption: {
                minimal: true,
              },
            },
            cacheDirectory: true,
            presets: [
              [
                "@babel/preset-env",
                {
                  targets: {
                    firefox: "91",
                  },
                },
              ],
              "@babel/preset-react",
              [
                "@babel/typescript", {
                  jsxPragma: "h",
                  optimizeConstEnums: true,
                },
              ],
            ],
            plugins: [
              [
                "@babel/plugin-transform-react-jsx", {
                  pragma: "h",
                  pragmaFrag: "Fragment",
                  useSpread: true,
                },
              ],
            ],
          },
        },
      },
      {
        test: /\.css$/,
        use: [
          // TODO: CSS-minification!
          MiniCssExtractPlugin.loader,
          {
            loader: "css-loader",
            options: {
              modules: {
                auto: true,
                localIdentName: "[name]__[local]--[hash:base64:5]",
              },
            },
          },
        ],
      },
      {
        test: /\.(jpg|png)$/,
        type: "asset/resource",
      },
    ],
  },
  devServer: {
    historyApiFallback: true,
    client: {
      progress: true,
    },
    port: 9000,
    proxy: [
      {
        context: ["/api", "/backend"],
        target: process.env.BACKEND_BASE_URL || "https://beta.habrasanta.org",
        changeOrigin: true,
        secure: false,
      },
    ],
  },
  plugins: [
    new MiniCssExtractPlugin({
      filename: "[name].[contenthash].css",
    }),
    new HtmlWebpackPlugin({
      template: path.join(__dirname, "src", "index.html"),
      templateParameters: {
        version: execSync("git describe --tags --always").toString().trim(),
      },
    }),
    new WebpackAssetsManifest({
      output: path.join(__dirname, "assets-manifest.json"),
      integrity: true,
      integrityHashes: ["sha256"],
      publicPath: true,
    }),
  ],
};
