import React, { useRef, useState } from "react";
import { Button } from "../../../../app/components/ui/Button";

interface DocumentUploadProps {
  onUpload: (file: File) => Promise<void>;
  isLoading: boolean;
}

export const DocumentUpload: React.FC<DocumentUploadProps> = ({
  onUpload,
  isLoading,
}) => {
  const fileInputRef = useRef<HTMLInputElement>(null);
  const [selectedFile, setSelectedFile] = useState<File | null>(null);

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>): void => {
    const file = e.target.files?.[0];
    if (file) setSelectedFile(file);
  };

  const handleUpload = async (): Promise<void> => {
    if (!selectedFile) return;
    await onUpload(selectedFile);
    setSelectedFile(null);
    if (fileInputRef.current) fileInputRef.current.value = "";
  };

  return (
    <div>
      <h3 className="text-sm font-medium text-gray-900 mb-3 hidden">
        Upload Document
      </h3>

      <div className="space-y-2">
        <input
          ref={fileInputRef}
          type="file"
          onChange={handleFileChange}
          accept=".pdf,.doc,.docx,.txt"
          className="hidden"
          id="file-upload"
        />
        <label
          htmlFor="file-upload"
          className="block w-full px-3 py-2 border-2 border-dashed border-gray-300 rounded-lg text-sm text-center cursor-pointer hover:border-blue-500 hover:bg-blue-50 transition"
        >
          {selectedFile ? selectedFile.name : "Choose file"}
        </label>
        {selectedFile && (
          <Button
            onClick={handleUpload}
            disabled={isLoading}
            className="w-full bg-blue-600 hover:bg-blue-700 text-white text-sm"
          >
            {isLoading ? "Uploading..." : "Upload"}
          </Button>
        )}
      </div>

      {selectedFile && (
        <p className="text-xs text-gray-600 mt-2">
          Selected: {selectedFile.name}
        </p>
      )}
    </div>
  );
};
