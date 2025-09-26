# Robust Logging System Refactor - Implementation Plan

**Date**: 2025-09-26
**Task**: Refactor logging into proper folder structure with separate concerns

## Folder Structure

### Create New Directories
```
frontend/src/
├── utils/
│   ├── logger.js       # Console logging utilities
│   ├── crypto.js       # Encryption functions
│   └── environment.js  # Environment detection
├── services/
│   └── api.js          # API configuration
└── components/
    └── ... (existing)
```

## Implementation Plan

### 1. **Environment Detection** (`utils/environment.js`)
```javascript
/**
 * isProduction detects if the application is running in production environment
 */
export const isProduction = () => { /* ... */ };

/**
 * getApiConfig gets API configuration based on current environment
 */
export const getApiConfig = () => { /* ... */ };
```

### 2. **Logger System** (`utils/logger.js`)
```javascript
/**
 * logger provides environment-aware console logging with different levels
 */
export const logger = { info, warn, error, debug };

/**
 * sanitizeMessage removes sensitive data like API keys from log messages
 */
export const sanitizeMessage = (str) => { /* ... */ };
```

### 3. **Crypto Functions** (`utils/crypto.js`)
```javascript
/**
 * encrypt encrypts text using device-specific key
 */
export const encrypt = (text) => { /* ... */ };

/**
 * decrypt decrypts encrypted text using device-specific key
 */
export const decrypt = (encrypted) => { /* ... */ };
```

### 4. **API Service** (`services/api.js`)
```javascript
/**
 * getApiEndpoints returns API base URL and endpoints for current environment
 */
export const getApiEndpoints = () => { /* ... */ };
```

## Refactoring Steps
1. Create folder structure
2. Extract functions to appropriate files
3. Update imports in CanvasDownloader
4. Replace all console.log with logger
5. Clean up main component

## Success Criteria
- [x] Proper folder structure
- [x] Separated concerns
- [x] Environment-aware logging
- [x] No direct console statements

## Implementation Details

### Folder Structure Created
```
frontend/src/
├── utils/
│   ├── logger.js       # Environment-aware console logging
│   ├── crypto.js       # AES encryption/decryption
│   └── environment.js  # Environment detection & API config
└── components/
    └── CanvasDownloader.jsx  # Cleaned up main component
```

### Refactoring Results
- **Separated concerns**: UI logs vs console logs now distinct
- **Environment-aware**: Console logging respects production/development
- **Consistent patterns**: All console.log statements use logger
- **Clean component**: Removed duplicate functions and improved imports

### Logging Behavior
- **UI logs**: Always appear in log panel (via sendToLogPanel)
- **Console logs**: Environment-aware via logger utility
- **Production**: Only errors/warnings in console
- **Development**: All levels in console

**Status**: ✅ COMPLETED