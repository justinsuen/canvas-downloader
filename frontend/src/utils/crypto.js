import CryptoJS from 'crypto-js';

/**
 * getDeviceKey generates a device-specific encryption key
 */
const getDeviceKey = () => {
  return navigator.userAgent + window.screen.width + window.screen.height;
};

/**
 * encrypt encrypts text using device-specific key
 */
export const encrypt = (text) => {
  return CryptoJS.AES.encrypt(text, getDeviceKey()).toString();
};

/**
 * decrypt decrypts encrypted text using device-specific key
 */
export const decrypt = (encrypted) => {
  try {
    return CryptoJS.AES.decrypt(encrypted, getDeviceKey()).toString(CryptoJS.enc.Utf8);
  } catch {
    return '';
  }
};