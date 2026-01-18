import { useState, useRef } from "react";
import type { UploadData } from "../App";
import { uploadLog } from "../services/api";

interface LogUploadProps {
  onUploadSuccess: (data: UploadData) => void;
}

export default function LogUpload({ onUploadSuccess }: LogUploadProps) {
  const [isDragging, setIsDragging] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [progress, setProgress] = useState(0);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const handleDragEnter = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(true);
  };

  const handleDragLeave = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);

    const files = e.dataTransfer.files;
    if (files.length > 0) {
      handleFile(files[0]);
    }
  };

  const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files.length > 0) {
      handleFile(e.target.files[0]);
    }
  };

  const handleFile = async (file: File) => {
    setError(null);
    setProgress(0);

    // Validate file
    if (!file.name.match(/\.(txt|log|csv)$/i)) {
      setError("Please upload a text, log, or CSV file");
      return;
    }

    if (file.size > 10 * 1024 * 1024) {
      setError("File size must be less than 10MB");
      return;
    }

    setIsLoading(true);

    // Simulate progress
    const progressInterval = setInterval(() => {
      setProgress((prev) => {
        if (prev >= 90) {
          clearInterval(progressInterval);
          return prev;
        }
        return prev + Math.random() * 30;
      });
    }, 200);

    try {
      const result = await uploadLog(file);
      clearInterval(progressInterval);
      setProgress(100);

      setTimeout(() => {
        onUploadSuccess({
          filename: result.filename,
          collectionName: result.collection_name,
        });
      }, 500);
    } catch (err) {
      clearInterval(progressInterval);
      setError(err instanceof Error ? err.message : "Upload failed");
      setProgress(0);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center p-4">
      <div className="w-full max-w-xl">
        {/* Header */}
        <div className="text-center mb-8 mt-4">
          <div className="inline-flex items-center justify-center w-16 h-16 bg-linear-to-br from-purple-500 to-pink-500 rounded-full mb-4 shadow-lg">
            <svg
              className="w-8 h-8 text-white"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M13 10V3L4 14h7v7l9-11h-7z"
              />
            </svg>
          </div>
          <h1 className="text-4xl font-bold text-white mb-2">CrashGPT</h1>
          <p className="text-gray-300 text-lg">Log Analysis with RAG</p>
        </div>

        {/* Upload Card */}
        <div className="bg-slate-800/50 backdrop-blur-xl rounded-2xl shadow-2xl border border-slate-700/50 overflow-hidden p-8">
          {/* Drop Zone */}
          <div
            onDragEnter={handleDragEnter}
            onDragLeave={handleDragLeave}
            onDrop={handleDrop}
            onClick={() => fileInputRef.current?.click()}
            className={`p-16 transition-all cursor-pointer ${
              isDragging
                ? "bg-purple-500/20 border-2 border-purple-500"
                : "bg-slate-700/30 border-2 border-dashed border-slate-600 hover:border-purple-500"
            }`}
          >
            <input
              ref={fileInputRef}
              type="file"
              onChange={handleFileSelect}
              accept=".txt,.log,.csv"
              className="hidden"
              disabled={isLoading}
            />

            <div className="text-center">
              <div className="inline-flex items-center justify-center w-16 h-16 bg-linear-to-br from-purple-500/20 to-pink-500/20 rounded-full mb-6">
                <svg
                  className="w-8 h-8 text-purple-400"
                  fill="none"
                  stroke="currentColor"
                  viewBox="0 0 24 24"
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M12 4v16m8-8H4"
                  />
                </svg>
              </div>

              <h3 className="text-xl font-semibold text-white mb-2">
                {isDragging ? "Drop your file here" : "Upload your log file"}
              </h3>
              <p className="text-gray-400 mb-4">
                Drag and drop or click to select
              </p>
              <p className="text-sm text-gray-500">
                .txt, .log, or .csv files up to 10MB
              </p>
            </div>
          </div>

          {/* Progress Bar */}
          {isLoading && progress > 0 && (
            <div className="px-8 py-6 bg-slate-700/20 border-t border-slate-700/50 mt-6">
              <div className="flex items-center justify-between mb-2">
                <span className="text-sm font-medium text-gray-300">
                  Uploading...
                </span>
                <span className="text-sm text-gray-400">
                  {Math.round(progress)}%
                </span>
              </div>
              <div className="w-full bg-slate-700/50 rounded-full h-2 overflow-hidden">
                <div
                  className="h-full bg-linear-to-r from-purple-500 to-pink-500 transition-all duration-300"
                  style={{ width: `${progress}%` }}
                />
              </div>
            </div>
          )}

          {/* Error Message */}
          {error && (
            <div className="px-8 py-6 bg-red-500/10 border-t border-red-500/20 mt-6">
              <div className="flex items-start">
                <svg
                  className="w-5 h-5 text-red-400 mt-0.5 mr-3 shrink-0"
                  fill="currentColor"
                  viewBox="0 0 20 20"
                >
                  <path
                    fillRule="evenodd"
                    d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z"
                    clipRule="evenodd"
                  />
                </svg>
                <p className="text-red-300 text-sm">{error}</p>
              </div>
            </div>
          )}
        </div>

        {/* Info Section */}
        <div className="mt-12 grid grid-cols-1 md:grid-cols-3 gap-6">
          <div className="bg-slate-800/30 rounded-lg p-6 border border-slate-700/30">
            <div className="text-purple-400 text-2xl font-bold mb-1">1</div>
            <p className="text-sm text-gray-400">Upload logs</p>
          </div>
          <div className="bg-slate-800/30 rounded-lg p-6 border border-slate-700/30">
            <div className="text-pink-400 text-2xl font-bold mb-1">2</div>
            <p className="text-sm text-gray-400">Ask questions</p>
          </div>
          <div className="bg-slate-800/30 rounded-lg p-6 border border-slate-700/30">
            <div className="text-blue-400 text-2xl font-bold mb-1">3</div>
            <p className="text-sm text-gray-400">Get insights</p>
          </div>
        </div>
      </div>
    </div>
  );
}
