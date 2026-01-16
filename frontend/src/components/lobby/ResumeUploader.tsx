import { useCallback, useState } from 'react';
import { Upload, FileText, X } from 'lucide-react';
import { motion } from 'framer-motion';
import { useSessionStore } from '../../stores/sessionStore';
import { validatePDF, getFileExtension } from '../../lib/utils';
import { API_ENDPOINTS } from '../../lib/constants';
import { Toast } from '../ui/Toast';

export const ResumeUploader = () => {
  const [isDragging, setIsDragging] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const { resumeFile, setResumeFile, setResumeText } = useSessionStore();

  const handleFile = useCallback(async (file: File) => {
    if (!validatePDF(file)) {
      const ext = getFileExtension(file.name);
      setError(`I can only read PDF files right now. Please upload the PDF version so I can read your text. (You uploaded a .${ext} file)`);
      return;
    }

    setResumeFile(file);
    
    const formData = new FormData();
    formData.append('file', file);
    
    try {
      const response = await fetch(API_ENDPOINTS.UPLOAD_RESUME, {
        method: 'POST',
        body: formData,
      });
      
      if (!response.ok) throw new Error('Upload failed');
      
      const data = await response.json();
      setResumeText(data.text);
    } catch (err) {
      setError('Failed to process your resume. Please try again.');
      setResumeFile(null);
    }
  }, [setResumeFile, setResumeText]);

  const handleDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
    
    const file = e.dataTransfer.files[0];
    if (file) handleFile(file);
  }, [handleFile]);

  const handleDragOver = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(true);
  }, []);

  const handleDragLeave = useCallback(() => {
    setIsDragging(false);
  }, []);

  const handleFileInput = useCallback((e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) handleFile(file);
  }, [handleFile]);

  const removeFile = useCallback(() => {
    setResumeFile(null);
    setResumeText(null);
  }, [setResumeFile, setResumeText]);

  return (
    <>
      {error && <Toast message={error} type="error" onClose={() => setError(null)} />}
      
      {!resumeFile ? (
        <motion.div
          onDrop={handleDrop}
          onDragOver={handleDragOver}
          onDragLeave={handleDragLeave}
          className={`relative border-2 border-dashed rounded-xl p-12 text-center transition-all cursor-pointer ${
            isDragging ? 'border-primary-blue bg-blue-50' : 'border-gray-300 hover:border-gray-400'
          }`}
          whileHover={{ scale: 1.01 }}
          whileTap={{ scale: 0.99 }}
        >
          <input
            type="file"
            accept=".pdf"
            onChange={handleFileInput}
            className="absolute inset-0 w-full h-full opacity-0 cursor-pointer"
          />
          <Upload className="mx-auto mb-4 text-gray-400" size={48} />
          <h3 className="text-lg font-semibold text-slate-dark mb-2">
            Drop your resume here
          </h3>
          <p className="text-gray-500">or click to browse (PDF only)</p>
        </motion.div>
      ) : (
        <motion.div
          initial={{ opacity: 0, scale: 0.9 }}
          animate={{ opacity: 1, scale: 1 }}
          className="bg-white rounded-xl p-6 shadow-soft flex items-center justify-between"
        >
          <div className="flex items-center gap-3">
            <FileText className="text-primary-blue" size={32} />
            <div>
              <p className="font-medium text-slate-dark">{resumeFile.name}</p>
              <p className="text-sm text-gray-500">
                {(resumeFile.size / 1024).toFixed(1)} KB
              </p>
            </div>
          </div>
          <button
            onClick={removeFile}
            className="p-2 hover:bg-gray-100 rounded-lg transition-colors"
          >
            <X size={20} />
          </button>
        </motion.div>
      )}
    </>
  );
};
