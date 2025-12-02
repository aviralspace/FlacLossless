import React, { useState, useEffect } from 'react';
import CookieUpload from '@/components/CookieUpload';
import DownloadError from '@/components/DownloadError';
import { backendService } from '@/services/backendService';

/**
 * Example: Integration guide for using cookie upload components
 */

export default function CookiesIntegrationExample() {
  const [showCookieUpload, setShowCookieUpload] = useState(false);
  const [downloadError, setDownloadError] = useState<{
    error: string;
    videoTitle?: string;
  } | null>(null);
  const [cookiesAvailable, setCookiesAvailable] = useState(false);

  // Check if cookies are available on mount
  useEffect(() => {
    checkCookies();
  }, []);

  const checkCookies = async () => {
    const status = await backendService.checkCookies();
    setCookiesAvailable(status.has_cookies);
  };

  const handleDownload = async (videoUrl: string) => {
    try {
      // Check if cookies are available first
      if (!cookiesAvailable) {
        setShowCookieUpload(true);
        return;
      }

      // Attempt download
      const result = await backendService.downloadAudio(videoUrl);
      console.log('Download successful:', result);
    } catch (error) {
      // Display error modal with cookie upload option
      const errorMsg = error instanceof Error ? error.message : 'Download failed';
      setDownloadError({
        error: errorMsg,
        videoTitle: 'Video'
      });
    }
  };

  const handleCookieSuccess = () => {
    setShowCookieUpload(false);
    setCookiesAvailable(true);
    // Retry the download if there was an error
    if (downloadError) {
      setDownloadError(null);
    }
  };

  return (
    <div className="space-y-4">
      <div>
        <h1 className="text-2xl font-bold">Download YouTube Music</h1>
        <p className="text-gray-400 mt-2">
          {cookiesAvailable ? '✓ Cookies available' : '⚠ Cookies not configured'}
        </p>
      </div>

      {/* Upload cookies manually */}
      {!cookiesAvailable && (
        <button
          onClick={() => setShowCookieUpload(true)}
          className="px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg"
        >
          Upload Cookies
        </button>
      )}

      {/* Cookie upload component */}
      {showCookieUpload && (
        <CookieUpload
          onSuccess={handleCookieSuccess}
          onError={(error) => console.error('Cookie upload error:', error)}
        />
      )}

      {/* Download error modal with retry and cookie upload */}
      {downloadError && (
        <DownloadError
          error={downloadError.error}
          videoTitle={downloadError.videoTitle}
          onRetry={() => {
            setDownloadError(null);
            handleDownload('https://www.youtube.com/watch?v=example');
          }}
          onDismiss={() => setDownloadError(null)}
        />
      )}

      {/* Your existing UI components go here */}
    </div>
  );
}
