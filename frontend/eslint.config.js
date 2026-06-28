import js from '@eslint/js';
import react from 'eslint-plugin-react';
import reactHooks from 'eslint-plugin-react-hooks';
import globals from 'globals';

export default [
  js.configs.recommended,
  {
    files: ['src/**/*.{js,jsx}'],
    languageOptions: {
      ecmaVersion: 2022,
      sourceType: 'module',
      globals: { ...globals.browser, process: 'readonly' },
      parserOptions: { ecmaFeatures: { jsx: true } },
    },
    plugins: { react, 'react-hooks': reactHooks },
    settings: { react: { version: 'detect' } },
    rules: {
      ...react.configs.recommended.rules,
      ...reactHooks.configs.recommended.rules,
      'react/react-in-jsx-scope': 'off',
      'react/prop-types': 'off',
      'no-unused-vars': ['warn', { argsIgnorePattern: '^_' }],
      // React Three Fiber uses non-standard DOM props (emissiveIntensity, transparent, etc.)
      'react/no-unknown-property': ['error', { ignore: [
        'object', 'args', 'position', 'rotation', 'scale', 'intensity', 'color',
        'attach', 'transparent', 'opacity', 'side', 'depthWrite', 'depthTest',
        'wireframe', 'vertexColors', 'flatShading', 'emissive', 'emissiveIntensity',
        'metalness', 'roughness', 'map', 'envMap', 'envMapIntensity', 'normalMap',
        'aoMap', 'aoMapIntensity', 'displacementMap', 'displacementScale',
        'alphaMap', 'alphaTest', 'blending', 'renderOrder', 'castShadow',
        'receiveShadow', 'visible', 'frustumCulled', 'matrixAutoUpdate',
        'geometry', 'material', 'morphTargetInfluences', 'userData',
        'fov', 'near', 'far', 'up', 'lookAt', 'target',
        'fog', 'background', 'environment', 'shadowMap',
        'count', 'itemSize', 'usage', 'needsUpdate',
        'parameters', 'dispose', 'clone', 'copy',
        'decay', 'distance', 'angle', 'penumbra',
        'groundColor', 'helper', 'shadowBias', 'shadowNormalBias',
        'shadowRadius', 'shadowMapSize',
        'linewidth', 'linecap', 'linejoin', 'dashed', 'dashScale', 'dashSize', 'gapSize',
        'pointsMaterial', 'size', 'sizeAttenuation',
        'skeleton', 'clearcoat', 'clearcoatRoughness',
      ] }],
    },
  },
];
