"use client";
import { useState, useRef } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { Upload, X, FileText, Check } from "lucide-react";
import { cn } from "../../lib/utils";

interface FileUploadProps {
    onChange?: (file: File | null) => void;
    onUpload?: (file: File) => Promise<void>;
    accept?: string;
    className?: string;
    label?: string;
    description?: string;
}

export const FileUpload = ({
    onChange,
    onUpload,
    accept = ".pdf,.doc,.docx,.txt",
    className,
    label = "Upload your file",
    description = "Drag and drop or click to browse",
}: FileUploadProps) => {
    const [file, setFile] = useState<File | null>(null);
    const [isDragging, setIsDragging] = useState(false);
    const [isUploading, setIsUploading] = useState(false);
    const [uploadSuccess, setUploadSuccess] = useState(false);
    const inputRef = useRef<HTMLInputElement>(null);

    const handleDragEnter = (e: React.DragEvent) => {
        e.preventDefault();
        e.stopPropagation();
        setIsDragging(true);
    };

    const handleDragLeave = (e: React.DragEvent) => {
        e.preventDefault();
        e.stopPropagation();
        setIsDragging(false);
    };

    const handleDragOver = (e: React.DragEvent) => {
        e.preventDefault();
        e.stopPropagation();
    };

    const handleDrop = async (e: React.DragEvent) => {
        e.preventDefault();
        e.stopPropagation();
        setIsDragging(false);

        const droppedFile = e.dataTransfer.files[0];
        if (droppedFile) {
            await handleFile(droppedFile);
        }
    };

    const handleFile = async (newFile: File) => {
        setFile(newFile);
        onChange?.(newFile);

        if (onUpload) {
            setIsUploading(true);
            try {
                await onUpload(newFile);
                setUploadSuccess(true);
                setTimeout(() => setUploadSuccess(false), 2000);
            } catch (error) {
                console.error("Upload failed:", error);
            } finally {
                setIsUploading(false);
            }
        }
    };

    const handleInputChange = async (e: React.ChangeEvent<HTMLInputElement>) => {
        const selectedFile = e.target.files?.[0];
        if (selectedFile) {
            await handleFile(selectedFile);
        }
    };

    const removeFile = () => {
        setFile(null);
        onChange?.(null);
        if (inputRef.current) {
            inputRef.current.value = "";
        }
    };

    return (
        <div className={cn("w-full", className)}>
            <motion.div
                onDragEnter={handleDragEnter}
                onDragLeave={handleDragLeave}
                onDragOver={handleDragOver}
                onDrop={handleDrop}
                onClick={() => inputRef.current?.click()}
                whileHover={{ scale: 1.01 }}
                whileTap={{ scale: 0.99 }}
                className={cn(
                    "relative cursor-pointer rounded-xl p-8 transition-all duration-300",
                    "border-2 border-dashed",
                    isDragging
                        ? "border-primary bg-primary/10 scale-[1.02]"
                        : "border-border hover:border-primary/50 bg-surface hover:bg-surface-light",
                    file && "border-solid border-primary/30"
                )}
            >
                {/* Grid background effect */}
                <div className="absolute inset-0 rounded-xl overflow-hidden pointer-events-none">
                    <div className="absolute inset-0 [background-image:linear-gradient(to_right,rgba(58,12,163,0.05)_1px,transparent_1px),linear-gradient(to_bottom,rgba(58,12,163,0.05)_1px,transparent_1px)] [background-size:24px_24px]" />
                </div>

                <input
                    ref={inputRef}
                    type="file"
                    accept={accept}
                    onChange={handleInputChange}
                    className="hidden"
                />

                <AnimatePresence mode="wait">
                    {!file ? (
                        <motion.div
                            key="upload"
                            initial={{ opacity: 0, y: 10 }}
                            animate={{ opacity: 1, y: 0 }}
                            exit={{ opacity: 0, y: -10 }}
                            className="flex flex-col items-center gap-4 relative z-10"
                        >
                            <motion.div
                                animate={{ y: isDragging ? -5 : 0 }}
                                className={cn(
                                    "w-16 h-16 rounded-full flex items-center justify-center",
                                    isDragging ? "bg-primary/20" : "bg-surface-elevated"
                                )}
                            >
                                <Upload
                                    className={cn(
                                        "w-8 h-8 transition-colors",
                                        isDragging ? "text-primary" : "text-foreground-muted"
                                    )}
                                />
                            </motion.div>
                            <div className="text-center">
                                <p className="font-medium text-foreground">{label}</p>
                                <p className="text-sm text-foreground-muted mt-1">
                                    {description}
                                </p>
                            </div>
                        </motion.div>
                    ) : (
                        <motion.div
                            key="file"
                            initial={{ opacity: 0, y: 10 }}
                            animate={{ opacity: 1, y: 0 }}
                            exit={{ opacity: 0, y: -10 }}
                            className="flex items-center gap-4 relative z-10"
                        >
                            <div className="w-12 h-12 rounded-lg bg-primary/20 flex items-center justify-center">
                                {isUploading ? (
                                    <motion.div
                                        animate={{ rotate: 360 }}
                                        transition={{ duration: 1, repeat: Infinity, ease: "linear" }}
                                        className="w-6 h-6 border-2 border-primary border-t-transparent rounded-full"
                                    />
                                ) : uploadSuccess ? (
                                    <Check className="w-6 h-6 text-success" />
                                ) : (
                                    <FileText className="w-6 h-6 text-primary" />
                                )}
                            </div>
                            <div className="flex-1 min-w-0">
                                <p className="font-medium text-foreground truncate">
                                    {file.name}
                                </p>
                                <p className="text-sm text-foreground-muted">
                                    {(file.size / 1024).toFixed(1)} KB
                                </p>
                            </div>
                            <button
                                onClick={(e) => {
                                    e.stopPropagation();
                                    removeFile();
                                }}
                                className="w-8 h-8 rounded-full bg-surface-elevated hover:bg-error/20 flex items-center justify-center transition-colors group"
                            >
                                <X className="w-4 h-4 text-foreground-muted group-hover:text-error" />
                            </button>
                        </motion.div>
                    )}
                </AnimatePresence>
            </motion.div>
        </div>
    );
};
