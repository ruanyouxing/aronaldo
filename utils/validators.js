/**
 * Validates and normalizes a URL
 * @param {string} url - The URL to validate
 * @returns {Object} - { valid: boolean, url: string, error: string }
 */
function validateUrl(url) {
  if (!url) {
    return { valid: false, url: null, error: "URL cannot be empty" };
  }

  let normalizedUrl = url.trim();

  // Add https:// if no protocol is specified
  if (!normalizedUrl.match(/^https?:\/\//i)) {
    normalizedUrl = "https://" + normalizedUrl;
  }

  // Validate URL
  try {
    new URL(normalizedUrl);
    return { valid: true, url: normalizedUrl, error: null };
  } catch (error) {
    return { valid: false, url: null, error: "Invalid URL format" };
  }
}

/**
 * Validates multiple URLs
 * @param {Array<string>} urls - Array of URLs to validate
 * @returns {Object} - { valid: boolean, urls: Array<string>, error: string }
 */
function validateMultipleUrls(urls) {
  const validatedUrls = [];
  
  for (const url of urls) {
    if (!url) continue; // Skip empty URLs
    
    const result = validateUrl(url);
    if (!result.valid) {
      return { valid: false, urls: null, error: `${result.error}: ${url}` };
    }
    validatedUrls.push(result.url);
  }

  return { valid: true, urls: validatedUrls, error: null };
}

module.exports = {
  validateUrl,
  validateMultipleUrls,
};
