export default [
    {
        files: ['main.js'],
        languageOptions: {
            ecmaVersion: 2022,
            sourceType: 'script',
            globals: {
                window: 'readonly',
                document: 'readonly',
                console: 'readonly',
                requestAnimationFrame: 'readonly',
                setTimeout: 'readonly',
                getComputedStyle: 'readonly',
                IntersectionObserver: 'readonly',
                Math: 'readonly',
                Date: 'readonly',
                HTMLElement: 'readonly',
            },
        },
        rules: {
            'no-unused-vars': ['warn', { argsIgnorePattern: '^_' }],
            'no-undef': 'error',
            'no-redeclare': 'error',
            'eqeqeq': ['error', 'always'],
            'no-var': 'error',
            'prefer-const': 'warn',
            'no-duplicate-case': 'error',
            'no-unreachable': 'error',
            'no-constant-condition': 'warn',
        },
    },
    {
        ignores: ['node_modules/', 'test-results/', 'playwright-report/'],
    },
];
