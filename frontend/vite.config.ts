import { defineConfig, loadEnv } from 'vite';
import react from '@vitejs/plugin-react';
import path from 'path';

export default defineConfig(({ command, mode }) => {
  const env = loadEnv(mode, process.cwd(), '');
  
  return {
    plugins: [
      react({
        // Optimize React refresh for better development experience
        fastRefresh: true,
        // Enable automatic JSX runtime
        jsxRuntime: 'automatic'
      })
    ],
    
    // ========================================================================
    // PATH RESOLUTION
    // ========================================================================
    resolve: {
      alias: {
        '@': path.resolve(__dirname, './src'),
        '@components': path.resolve(__dirname, './src/components'),
        '@pages': path.resolve(__dirname, './src/pages'),
        '@services': path.resolve(__dirname, './src/services'),
        '@stores': path.resolve(__dirname, './src/stores'),
        '@utils': path.resolve(__dirname, './src/utils'),
        '@types': path.resolve(__dirname, './src/types'),
        '@assets': path.resolve(__dirname, './src/assets')
      }
    },

    // ========================================================================
    // DEVELOPMENT SERVER
    // ========================================================================
    server: {
      port: 3000,
      host: true, // Listen on all addresses
      strictPort: false, // Allow fallback ports
      open: false, // Don't auto-open browser (better for containers)
      
      // Proxy API requests to backend
      proxy: {
        '/api': {
          target: env.VITE_API_URL?.replace('/api', '') || 'http://localhost:8000',
          changeOrigin: true,
          secure: false,
          timeout: 30000,
          configure: (proxy, options) => {
            proxy.on('error', (err, req, res) => {
              console.error('🔴 Proxy error:', err);
            });
            proxy.on('proxyReq', (proxyReq, req, res) => {
              console.log('🔄 Proxying request:', req.method, req.url);
            });
          }
        }
      },

      // CORS configuration for development
      cors: {
        origin: ['http://localhost:3000', 'http://127.0.0.1:3000'],
        credentials: true
      },

      // Hot Module Replacement
      hmr: {
        overlay: true // Show errors in browser overlay
      }
    },

    // ========================================================================
    // BUILD CONFIGURATION
    // ========================================================================
    build: {
      target: 'es2020', // Modern browsers support
      outDir: 'dist',
      assetsDir: 'assets',
      sourcemap: mode === 'development', // Source maps only in dev
      minify: mode === 'production' ? 'esbuild' : false,
      
      // Chunk optimization
      rollupOptions: {
        output: {
          manualChunks: {
            // Vendor libraries
            vendor: ['react', 'react-dom'],
            router: ['react-router-dom'],
            ui: ['framer-motion', '@headlessui/react', 'lucide-react'],
            forms: ['react-hook-form'],
            http: ['axios', 'react-query'],
            state: ['zustand'],
            charts: ['recharts'],
            utils: ['date-fns', 'clsx', 'tailwind-merge']
          },
          // Asset file naming
          chunkFileNames: 'js/[name]-[hash].js',
          entryFileNames: 'js/[name]-[hash].js',
          assetFileNames: (assetInfo) => {
            const info = assetInfo.name!.split('.');
            const extType = info[info.length - 1];
            if (/\.(mp4|webm|ogg|mp3|wav|flac|aac)(\?.*)?$/i.test(assetInfo.name!)) {
              return 'media/[name]-[hash].[ext]';
            }
            if (/\.(png|jpe?g|gif|svg|ico|webp)(\?.*)?$/i.test(assetInfo.name!)) {
              return 'images/[name]-[hash].[ext]';
            }
            if (['css', 'scss', 'sass', 'less'].includes(extType)) {
              return 'css/[name]-[hash].[ext]';
            }
            return 'assets/[name]-[hash].[ext]';
          }
        }
      },

      // Performance warnings
      chunkSizeWarningLimit: 1000, // Warn for chunks > 1MB
      
      // Asset optimization
      assetsInlineLimit: 4096 // Inline assets < 4KB
    },

    // ========================================================================
    // OPTIMIZATIONS
    // ========================================================================
    optimizeDeps: {
      include: [
        'react',
        'react-dom',
        'react-router-dom',
        'axios',
        'zustand',
        'react-query',
        'framer-motion',
        'lucide-react',
        'recharts',
        'date-fns'
      ],
      exclude: ['@vite/client', '@vite/env']
    },

    // ========================================================================
    // ENVIRONMENT VARIABLES
    // ========================================================================
    define: {
      // Expose build information
      __BUILD_DATE__: JSON.stringify(new Date().toISOString()),
      __BUILD_VERSION__: JSON.stringify(process.env.npm_package_version || '1.0.0'),
      __DEV_MODE__: JSON.stringify(mode === 'development')
    },

    // ========================================================================
    // CSS CONFIGURATION
    // ========================================================================
    css: {
      devSourcemap: mode === 'development'
    },

    // ========================================================================
    // PREVIEW SERVER (for production builds)
    // ========================================================================
    preview: {
      port: 4173,
      host: true,
      strictPort: false,
      open: false
    },

    // ========================================================================
    // LOGGING
    // ========================================================================
    logLevel: mode === 'development' ? 'info' : 'warn',

    // ========================================================================
    // CLEANUP CONFIGURATION
    // ========================================================================
    clearScreen: false, // Don't clear terminal on rebuild (better for containers)
    
    // Remove legacy browser support to reduce bundle size
    esbuild: {
      drop: mode === 'production' ? ['console', 'debugger'] : [],
      target: 'es2020'
    }
  };
});