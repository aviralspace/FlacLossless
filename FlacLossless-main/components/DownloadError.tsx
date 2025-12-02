import React, { useState } from 'react';
import CookieUpload from './CookieUpload';

interface DownloadErrorProps {
  error: string;
  onRetry?: () => void;
  onDismiss?: () => void;
  videoTitle?: string;
}

export const DownloadError: React.FC<DownloadErrorProps> = ({
  error,
  onRetry,
  onDismiss,
  videoTitle = 'This video'
}) => {
  const [showCookieUpload, setShowCookieUpload] = useState(false);

  const isAuthError = error.toLowerCase().includes('authentication') ||
    error.toLowerCase().includes('sign in') ||
    error.toLowerCase().includes('cookies') ||
    error.toLowerCase().includes('bot');

  const handleCookieSuccess = () => {
    setShowCookieUpload(false);
    onRetry?.();
  };

  return (
    <div className="fixed inset-0 bg-black bg-opacity-75 flex items-center justify-center z-50 p-4">
      <div className="bg-gray-900 rounded-lg max-w-lg w-full p-6 border border-gray-700">
        <div className="flex items-start mb-4">
          <svg
            className="w-6 h-6 text-red-500 mr-3 flex-shrink-0 mt-0.5"
            fill="currentColor"
            viewBox="0 0 20 20"
          >
            <path
              fillRule="evenodd"
              d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z"
              clipRule="evenodd"
            />
          </svg>
          <div>
            <h2 className="text-xl font-bold text-white">Download Failed</h2>
            <p className="text-sm text-gray-400 mt-1">{videoTitle}</p>
          </div>
        </div>

        <div className="bg-red-900 bg-opacity-20 border border-red-700 rounded-lg p-4 mb-4">
          <p className="text-sm text-red-200">{error}</p>
        </div>

        {isAuthError && !showCookieUpload && (
          <div className="mb-4 p-3 bg-blue-900 bg-opacity-20 border border-blue-700 rounded-lg">
            <p className="text-sm text-blue-200 mb-2">
              YouTube requires authentication to download. You can provide your cookies to continue.
            </p>
            <button
              onClick={() => setShowCookieUpload(true)}
              className="text-sm text-blue-400 hover:text-blue-300 underline font-medium"
            >
              Upload YouTube Cookies
            </button>
          </div>
        )}

        {showCookieUpload && (
          <div className="mb-4">
            <CookieUpload
              onSuccess={handleCookieSuccess}
              onError={(err) => console.error('Cookie upload error:', err)}
              showTitle={true}
            />
          </div>
        )}

        <div className="flex gap-3 justify-end">
          <button
            onClick={onDismiss}
            className="px-4 py-2 text-gray-300 hover:text-white transition-colors text-sm font-medium"
          >
            Dismiss
          </button>
          {onRetry && (
            <button
              onClick={onRetry}
              className="px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg transition-colors text-sm font-medium"
            >
              Retry Download
            </button>
          )}
        </div>
      </div>
    </div>
  );
};

export default DownloadError;
