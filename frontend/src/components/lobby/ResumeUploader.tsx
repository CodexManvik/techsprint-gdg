import { useCallback, useState } from 'react';
import { FileText, X, Check } from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';
import { useSessionStore } from '../../stores/sessionStore';
import { API_ENDPOINTS } from '../../lib/constants';
import { Toast } from '../ui/Toast';
import { FileUpload } from '../ui/file-upload';
import { cn } from '../../lib/utils';

export const ResumeUploader = () => {
  const [error, setError] = useState<string | null>(null);
  const [isProcessing, setIsProcessing] = useState(false);
  const [isSuccess, setIsSuccess] = useState(false);
  const { resumeFile, setResumeFile, setResumeText } = useSessionStore();

  const validatePDF = (file: File) => {
    return file.type === 'application/pdf' || file.name.toLowerCase().endsWith('.pdf');
  };

  const handleFile = useCallback(async (file: File | null) => {
    if (!file) {
      setResumeFile(null);
      setResumeText(null);
      return;
    }

    if (!validatePDF(file)) {
      const ext = file.name.split('.').pop() || 'unknown';
      setError(`I can only read PDF files. Please upload a PDF. (You uploaded a .${ext} file)`);
      return;
    }

    setResumeFile(file);
    setIsProcessing(true);

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
      setIsSuccess(true);
      setTimeout(() => setIsSuccess(false), 2000);
    } catch (err) {
      setError('Failed to process your resume. Please try again.');
      setResumeFile(null);
    } finally {
      setIsProcessing(false);
    }
  }, [setResumeFile, setResumeText]);

  const removeFile = useCallback(() => {
    setResumeFile(null);
    setResumeText(null);
  }, [setResumeFile, setResumeText]);

  return (
    <>
      {error && <Toast message={error} type="error" onClose={() => setError(null)} />}

      <AnimatePresence mode="wait">
        {!resumeFile ? (
          <motion.div
            key="upload"
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -10 }}
          >
            <FileUpload
              onChange={handleFile}
              accept=".pdf"
              label="Drop your resume here"
              description="or click to browse (PDF only)"
            />
          </motion.div>
        ) : (
          <motion.div
            key="file"
            initial={{ opacity: 0, scale: 0.95 }}
            animate={{ opacity: 1, scale: 1 }}
            exit={{ opacity: 0, scale: 0.95 }}
            className={cn(
              'glass rounded-xl p-6 flex items-center justify-between',
              isSuccess && 'border-success/50'
            )}
          >
            <div className="flex items-center gap-4">
              <div className={cn(
                'w-14 h-14 rounded-xl flex items-center justify-center transition-colors',
                isProcessing ? 'bg-primary/20' : isSuccess ? 'bg-success/20' : 'bg-primary/10'
              )}>
                {isProcessing ? (
                  <motion.div
                    animate={{ rotate: 360 }}
                    transition={{ duration: 1, repeat: Infinity, ease: "linear" }}
                    className="w-6 h-6 border-2 border-primary border-t-transparent rounded-full"
                  />
                ) : isSuccess ? (
                  <Check className="w-7 h-7 text-success" />
                ) : (
                  <FileText className="w-7 h-7 text-primary" />
                )}
              </div>
              <div>
                <p className="font-semibold text-foreground">{resumeFile.name}</p>
                <p className="text-sm text-foreground-muted">
                  {(resumeFile.size / 1024).toFixed(1)} KB
                  {isSuccess && <span className="ml-2 text-success">• Processed successfully</span>}
                </p>
              </div>
            </div>
            <motion.button
              whileHover={{ scale: 1.1 }}
              whileTap={{ scale: 0.9 }}
              onClick={removeFile}
              className="w-10 h-10 rounded-xl bg-surface-elevated hover:bg-error/20 flex items-center justify-center transition-colors group"
            >
              <X className="w-5 h-5 text-foreground-muted group-hover:text-error" />
            </motion.button>
          </motion.div>
        )}
      </AnimatePresence>
    </>
  );
};
