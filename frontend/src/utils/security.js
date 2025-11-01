/**
 * Security utilities for XSS protection and input validation
 */

/**
 * Sanitize HTML content to prevent XSS attacks
 * Uses DOMPurify-like approach (simplified, should use DOMPurify library in production)
 */
export const sanitizeHTML = (html) => {
  if (!html || typeof html !== 'string') return '';
  
  // Basic XSS prevention - remove script tags and event handlers
  let sanitized = html
    .replace(/<script\b[^<]*(?:(?!<\/script>)<[^<]*)*<\/script>/gi, '')
    .replace(/<iframe\b[^<]*(?:(?!<\/iframe>)<[^<]*)*<\/iframe>/gi, '')
    .replace(/on\w+\s*=\s*["'][^"']*["']/gi, '') // Remove event handlers like onclick=
    .replace(/javascript:/gi, '') // Remove javascript: protocol
    .replace(/on\w+\s*=\s*[^\s>]*/gi, '') // Remove event handlers without quotes
    .replace(/<object\b[^<]*(?:(?!<\/object>)<[^<]*)*<\/object>/gi, '')
    .replace(/<embed\b[^<]*(?:(?!<\/embed>)<[^<]*)*<\/embed>/gi, '');
  
  return sanitized;
};

/**
 * Validate email address
 */
export const validateEmail = (email) => {
  if (!email || typeof email !== 'string') return false;
  const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
  return emailRegex.test(email.trim());
};

/**
 * Sanitize user input (remove potentially dangerous characters)
 */
export const sanitizeInput = (input) => {
  if (typeof input !== 'string') return input;
  
  return input
    .replace(/[<>]/g, '') // Remove < and >
    .replace(/javascript:/gi, '')
    .replace(/on\w+\s*=/gi, '')
    .trim();
};

/**
 * Validate password strength
 */
export const validatePassword = (password) => {
  if (!password || password.length < 8) {
    return { valid: false, error: 'Passwort muss mindestens 8 Zeichen lang sein' };
  }
  if (password.length > 128) {
    return { valid: false, error: 'Passwort darf maximal 128 Zeichen lang sein' };
  }
  return { valid: true };
};

/**
 * Validate filename to prevent path traversal
 */
export const validateFilename = (filename) => {
  if (!filename || typeof filename !== 'string') return false;
  
  // Check for path traversal attempts
  if (filename.includes('..') || filename.includes('/') || filename.includes('\\')) {
    return false;
  }
  
  // Check for dangerous characters
  if (/[<>:"|?*\x00-\x1f]/.test(filename)) {
    return false;
  }
  
  // Limit length
  if (filename.length > 255) {
    return false;
  }
  
  return true;
};

/**
 * Escape HTML entities for safe rendering
 */
export const escapeHTML = (str) => {
  if (typeof str !== 'string') return str;
  const map = {
    '&': '&amp;',
    '<': '&lt;',
    '>': '&gt;',
    '"': '&quot;',
    "'": '&#039;'
  };
  return str.replace(/[&<>"']/g, (m) => map[m]);
};

/**
 * Generate CSRF token (for frontend-initiated requests)
 */
export const generateCSRFToken = () => {
  const array = new Uint8Array(16);
  crypto.getRandomValues(array);
  return Array.from(array, byte => byte.toString(16).padStart(2, '0')).join('');
};

/**
 * Store token securely (with expiration)
 */
export const setSecureToken = (token, expiresInHours = 24) => {
  const expires = new Date();
  expires.setHours(expires.getHours() + expiresInHours);
  
  try {
    localStorage.setItem('token', token);
    localStorage.setItem('token_expires', expires.toISOString());
  } catch (e) {
    console.error('Failed to store token:', e);
  }
};

/**
 * Get token if not expired
 */
export const getSecureToken = () => {
  try {
    const token = localStorage.getItem('token');
    const expiresStr = localStorage.getItem('token_expires');
    
    if (!token) return null;
    
    if (expiresStr) {
      const expires = new Date(expiresStr);
      if (new Date() > expires) {
        // Token expired
        localStorage.removeItem('token');
        localStorage.removeItem('token_expires');
        return null;
      }
    }
    
    return token;
  } catch (e) {
    console.error('Failed to get token:', e);
    return null;
  }
};

/**
 * Clear token
 */
export const clearSecureToken = () => {
  try {
    localStorage.removeItem('token');
    localStorage.removeItem('token_expires');
    localStorage.removeItem('tempToken');
    localStorage.removeItem('setupToken');
  } catch (e) {
    console.error('Failed to clear token:', e);
  }
};

/**
 * Rate limiting helper (client-side basic check)
 */
let requestTimestamps = [];
export const checkRateLimit = (maxRequests = 10, timeWindowMs = 60000) => {
  const now = Date.now();
  requestTimestamps = requestTimestamps.filter(ts => now - ts < timeWindowMs);
  
  if (requestTimestamps.length >= maxRequests) {
    return false; // Rate limit exceeded
  }
  
  requestTimestamps.push(now);
  return true;
};

