import { useRef, useState } from "react";
import type { FC } from "react";
import Button from "./Button";

interface FileUploadProps {
  onFileSelect: (file: File) => void;
  label?: string;
  accept?: string;
  error?: string;
  maxSize?: number; // in MB
  id?: string;
}

const FileUpload: FC<FileUploadProps> = ({
  onFileSelect,
  label = "Upload file",
  accept = ".pdf,.txt,.doc,.docx",
  error,
  maxSize = 10, // Default max size 10MB
  id,
}) => {
  const [dragActive, setDragActive] = useState(false);
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [fileError, setFileError] = useState<string>("");
  const inputRef = useRef<HTMLInputElement>(null);

  // Generate a unique ID if one is not provided
  const inputId =
    id || `file-upload-${Math.random().toString(36).substr(2, 9)}`;

  const handleDrag = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();

    if (e.type === "dragenter" || e.type === "dragover") {
      setDragActive(true);
    } else if (e.type === "dragleave") {
      setDragActive(false);
    }
  };

  const validateFile = (file: File): boolean => {
    // Check file size
    if (file.size > maxSize * 1024 * 1024) {
      setFileError(`File is too large. Maximum size is ${maxSize}MB.`);
      return false;
    }

    // Check file type based on accept prop
    if (accept) {
      const acceptedTypes = accept.split(",");
      const fileExtension = `.${file.name.split(".").pop()?.toLowerCase()}`;
      const fileType = file.type;

      if (
        !acceptedTypes.some(
          (type) =>
            type === fileExtension ||
            type === fileType ||
            (type.includes("/*") && fileType.startsWith(type.replace("/*", "")))
        )
      ) {
        setFileError(`File type not supported. Accepted types: ${accept}`);
        return false;
      }
    }

    setFileError("");
    return true;
  };

  const handleFile = (file: File) => {
    if (validateFile(file)) {
      setSelectedFile(file);
      onFileSelect(file);
    }
  };

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    e.preventDefault();
    if (e.target.files && e.target.files[0]) {
      handleFile(e.target.files[0]);
    }
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(false);

    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      handleFile(e.dataTransfer.files[0]);
    }
  };

  const handleButtonClick = () => {
    inputRef.current?.click();
  };

  return (
    <div className="w-full">
      {label && (
        <label
          htmlFor={inputId}
          className="block text-sm font-medium text-gray-700 mb-1"
        >
          {label}
        </label>
      )}
      <div
        className={`
          border-2 border-dashed rounded-md p-6 flex flex-col items-center justify-center
          ${dragActive ? "border-blue-500 bg-blue-50" : "border-gray-300"}
          ${error || fileError ? "border-red-500 bg-red-50" : ""}
          ${selectedFile ? "border-green-500 bg-green-50" : ""}
        `}
        onDragEnter={handleDrag}
        onDragOver={handleDrag}
        onDragLeave={handleDrag}
        onDrop={handleDrop}
      >
        <input
          ref={inputRef}
          id={inputId}
          type="file"
          className="hidden"
          accept={accept}
          onChange={handleChange}
          aria-label={label}
        />

        {selectedFile ? (
          <div className="text-center">
            <svg
              className="mx-auto h-12 w-12 text-green-500"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
              xmlns="http://www.w3.org/2000/svg"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M5 13l4 4L19 7"
              />
            </svg>
            <p className="mt-2 text-sm text-gray-700">
              Selected: {selectedFile.name}
            </p>
            <Button
              variant="outline"
              className="mt-4"
              onClick={handleButtonClick}
              type="button"
            >
              Change file
            </Button>
          </div>
        ) : (
          <div className="text-center">
            <svg
              className="mx-auto h-12 w-12 text-gray-400"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
              xmlns="http://www.w3.org/2000/svg"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12"
              />
            </svg>
            <p className="mt-2 text-sm text-gray-600">
              Drag and drop a file here, or click to select a file
            </p>
            <p className="mt-1 text-xs text-gray-500">
              {`Max file size: ${maxSize}MB. Accepted formats: ${accept}`}
            </p>
            <Button
              variant="outline"
              className="mt-4"
              onClick={handleButtonClick}
              type="button"
            >
              Select file
            </Button>
          </div>
        )}
      </div>
      {(error || fileError) && (
        <p className="mt-1 text-sm text-red-600">{error || fileError}</p>
      )}
    </div>
  );
};

export default FileUpload;
