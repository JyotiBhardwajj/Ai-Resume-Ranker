'use client';

import * as React from 'react';
import {
    AlertCircle,
    FileText,
    Trash2,
    Upload,
    X,
    Loader2
} from 'lucide-react';
import { toast } from 'sonner';
import { createClient } from '@/utils/supabase/client';

interface FileUploadProps {
    onUploadComplete?: () => void;
}

export function FileUpload({ onUploadComplete }: FileUploadProps) {
    const [files, setFiles] = React.useState<File[]>([]);
    const [isDragging, setIsDragging] = React.useState(false);
    const [uploading, setUploading] = React.useState(false);
    const [errors, setErrors] = React.useState<string[]>([]);
    const fileInputRef = React.useRef<HTMLInputElement>(null);

    const handleDragEnter = (e: React.DragEvent) => { e.preventDefault(); setIsDragging(true); };
    const handleDragLeave = (e: React.DragEvent) => { e.preventDefault(); setIsDragging(false); };
    const handleDragOver = (e: React.DragEvent) => { e.preventDefault(); };
    const handleDrop = (e: React.DragEvent) => {
        e.preventDefault();
        setIsDragging(false);
        const droppedFiles = Array.from(e.dataTransfer.files).filter(f => f.type === 'application/pdf');
        if (droppedFiles.length === 0) {
            setErrors(['Only PDF files are allowed.']);
            return;
        }
        setFiles(prev => [...prev, ...droppedFiles]);
        setErrors([]);
    };

    const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
        if (e.target.files) {
            const selectedFiles = Array.from(e.target.files).filter(f => f.type === 'application/pdf');
            if (selectedFiles.length === 0) {
                setErrors(['Only PDF files are allowed.']);
                return;
            }
            setFiles(prev => [...prev, ...selectedFiles]);
            setErrors([]);
        }
    };

    const removeFile = (index: number) => {
        setFiles(prev => prev.filter((_, i) => i !== index));
    };

    const handleUpload = async () => {
        if (files.length === 0) return;
        setUploading(true);
        const formData = new FormData();
        files.forEach(f => formData.append('files', f));

        try {
            const supabase = createClient();
            const { data: { session } } = await supabase.auth.getSession();
            if (session?.user?.id) {
                formData.append('user_id', session.user.id);
            }

            const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
            const res = await fetch(`${apiUrl}/api/candidates/upload`, {
                method: 'POST',
                body: formData
            });
            if (!res.ok) throw new Error('Upload failed');
            toast.success("Resumes uploaded and parsed successfully!");
            setFiles([]);
            if (onUploadComplete) onUploadComplete();
        } catch (e: any) {
            setErrors([e.message || 'Upload failed']);
            toast.error("Failed to upload resumes");
        } finally {
            setUploading(false);
        }
    };

    return (
        <div className="flex flex-col gap-2">
            <div
                className={`border-input relative flex min-h-52 flex-col items-center overflow-hidden rounded-xl border border-dashed p-4 transition-colors ${
                    isDragging ? 'bg-accent/50 border-primary' : ''
                } ${files.length === 0 ? 'justify-center' : ''}`}
                onDragEnter={handleDragEnter}
                onDragLeave={handleDragLeave}
                onDragOver={handleDragOver}
                onDrop={handleDrop}
            >
                <input
                    className="sr-only"
                    ref={fileInputRef}
                    type="file"
                    accept=".pdf,application/pdf"
                    multiple
                    onChange={handleFileSelect}
                />

                {files.length > 0 ? (
                    <div className="flex w-full flex-col gap-3">
                        <div className="flex items-center justify-between gap-2">
                            <h3 className="truncate text-sm font-medium">Files ({files.length})</h3>
                            <div className="flex gap-2">
                                <button onClick={() => fileInputRef.current?.click()} className="flex items-center gap-1.5 px-3 py-1.5 border rounded-lg text-xs font-medium hover:bg-accent disabled:opacity-50" disabled={uploading}>
                                    <Upload className="size-3.5 opacity-60" /> Add files
                                </button>
                                <button onClick={() => setFiles([])} className="flex items-center gap-1.5 px-3 py-1.5 border rounded-lg text-xs font-medium hover:bg-accent disabled:opacity-50" disabled={uploading}>
                                    <Trash2 className="size-3.5 opacity-60" /> Remove all
                                </button>
                            </div>
                        </div>

                        <div className="w-full space-y-2 max-h-48 overflow-y-auto pr-2">
                            {files.map((file, idx) => (
                                <div key={idx} className="bg-background flex flex-col gap-1 rounded-lg border p-2 pe-3 transition-opacity duration-300">
                                    <div className="flex items-center justify-between gap-2">
                                        <div className="flex items-center gap-3 overflow-hidden">
                                            <div className="flex aspect-square size-10 shrink-0 items-center justify-center rounded border bg-muted/50">
                                                <FileText className="size-5 text-primary/70" />
                                            </div>
                                            <div className="flex min-w-0 flex-col gap-0.5">
                                                <p className="truncate text-[13px] font-medium">{file.name}</p>
                                                <p className="text-muted-foreground text-xs">{(file.size / 1024 / 1024).toFixed(2)} MB</p>
                                            </div>
                                        </div>
                                        <button onClick={() => removeFile(idx)} className="text-muted-foreground/80 hover:text-foreground size-8 flex items-center justify-center rounded-md hover:bg-accent" disabled={uploading}>
                                            <X className="size-4" />
                                        </button>
                                    </div>
                                </div>
                            ))}
                        </div>
                        <div className="mt-2 flex justify-end">
                            <button onClick={handleUpload} disabled={uploading} className="bg-primary text-primary-foreground px-4 py-2 rounded-lg text-sm font-medium flex items-center gap-2 hover:bg-primary/90 disabled:opacity-50">
                                {uploading ? <Loader2 className="size-4 animate-spin" /> : <Upload className="size-4" />}
                                {uploading ? 'Processing Resumes...' : 'Upload & Parse Resumes'}
                            </button>
                        </div>
                    </div>
                ) : (
                    <div className="flex flex-col items-center justify-center px-4 py-3 text-center">
                        <div className="bg-background mb-2 flex size-11 shrink-0 items-center justify-center rounded-full border">
                            <Upload className="size-5 opacity-60" />
                        </div>
                        <p className="mb-1.5 text-sm font-medium">Drop your PDF resumes here</p>
                        <p className="text-muted-foreground text-xs">Upload candidate resumes to rank</p>
                        <button className="mt-4 flex items-center gap-2 px-4 py-2 border rounded-lg text-sm font-medium hover:bg-accent" onClick={() => fileInputRef.current?.click()}>
                            Select PDFs
                        </button>
                    </div>
                )}
            </div>
            {errors.length > 0 && (
                <div className="text-destructive flex items-center gap-1.5 text-xs mt-2" role="alert">
                    <AlertCircle className="size-3.5 shrink-0" />
                    <span>{errors[0]}</span>
                </div>
            )}
        </div>
    );
}
