import React, { useState, useRef } from 'react';
import { backendService } from '../services/backendService';

interface CookieUploadProps {
  onSuccess?: () => void;
  onError?: (error: string) => void;
  showTitle?: boolean;
  className?: string;
}

export const CookieUpload: React.FC<CookieUploadProps> = ({
  onSuccess,
  onError,
  showTitle = true,
  className = ''
}) => {
  const [isLoading, setIsLoading] = useState(false);
  const [status, setStatus] = useState<'idle' | 'uploading' | 'success' | 'error'>('idle');
  const [message, setMessage] = useState('');
  const fileInputRef = useRef<HTMLInputElement>(null);

  const handleFileChange = async (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (!file) return;

    if (!file.name.endsWith('.txt')) {
      const error = 'Please select a .txt file';
      setStatus('error');
      setMessage(error);
      onError?.(error);
      return;
    }

    setIsLoading(true);
    setStatus('uploading');
    setMessage('Uploading cookies...');

    try {
      const result = await backendService.uploadCookies(file);
      setStatus('success');
      setMessage(result.message || 'Cookies uploaded successfully!');
      onSuccess?.();
      
      // Reset after 3 seconds
      setTimeout(() => {
        setStatus('idle');
        setMessage('');
        if (fileInputRef.current) {
          fileInputRef.current.value = '';
        }
      }, 3000);
    } catch (error) {
      const errorMsg = error instanceof Error ? error.message : 'Failed to upload cookies';
      setStatus('error');
      setMessage(errorMsg);
      onError?.(errorMsg);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className={`cookie-upload-container ${className}`}>
      {showTitle && (
        <h3 className="text-lg font-semibold mb-3 text-white">YouTube Authentication</h3>
      )}
      
      <div className="space-y-3">
        <p className="text-sm text-gray-300">
          To download videos, you need to provide your YouTube cookies for authentication.
        </p>

        <div className="bg-gray-800 border-2 border-dashed border-gray-600 rounded-lg p-4">
          <label className="flex flex-col items-center justify-center cursor-pointer hover:border-blue-500 transition-colors">
            <svg
              className="w-8 h-8 text-gray-400 mb-2"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12"
              />
            </svg>
            <span className="text-sm font-medium text-gray-300">
              {isLoading ? 'Uploading...' : 'Click to upload cookies file'}
            </span>
            <span className="text-xs text-gray-500 mt-1">(.txt format only)</span>
            <input
              ref={fileInputRef}
              type="file"
              accept=".txt"
              onChange={handleFileChange}
              disabled={isLoading}
              className="hidden"
            />
          </label>
        </div>

        {message && (
          <div
            className={`p-3 rounded-lg text-sm ${
              status === 'success'
                ? 'bg-green-900 bg-opacity-30 text-green-300 border border-green-700'
                : status === 'error'
                ? 'bg-red-900 bg-opacity-30 text-red-300 border border-red-700'
                : 'bg-blue-900 bg-opacity-30 text-blue-300 border border-blue-700'
            }`}
          >
            {message}
          </div>
        )}

        <div className="bg-gray-900 bg-opacity-50 rounded-lg p-3 text-xs text-gray-400 space-y-2">
          <p className="font-semibold text-gray-300">How to export cookies:</p>
          <ol className="list-decimal list-inside space-y-1">
            <li>Install a browser extension like "EditThisCookie" or "Get cookies.txt"</li>
            <li>Visit youtube.com and make sure you're logged in</li>
            <li>Use the extension to export cookies as .txt file</li>
            <li>Upload the file here</li>
          </ol>
        </div>
      </div>
    </div>
  );
};

export default CookieUpload;
