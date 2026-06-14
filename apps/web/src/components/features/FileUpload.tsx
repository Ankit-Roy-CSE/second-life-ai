"use client"

import React, { useCallback, useState } from "react"
import { UploadCloud, X } from "lucide-react"

import { cn } from "@/lib/utils"

export interface FileUploadProps {
  accept?: string
  maxFiles?: number
  onChange?: (files: File[]) => void
  disabled?: boolean
  className?: string
}

export function FileUpload({
  accept = "image/*,video/*",
  maxFiles = 8,
  onChange,
  disabled = false,
  className,
}: FileUploadProps) {
  const [files, setFiles] = useState<File[]>([])
  const [isDragging, setIsDragging] = useState(false)

  const handleDragOver = useCallback((e: React.DragEvent) => {
    e.preventDefault()
    if (!disabled) setIsDragging(true)
  }, [disabled])

  const handleDragLeave = useCallback((e: React.DragEvent) => {
    e.preventDefault()
    setIsDragging(false)
  }, [])

  const handleDrop = useCallback(
    (e: React.DragEvent) => {
      e.preventDefault()
      setIsDragging(false)
      if (disabled) return

      const droppedFiles = Array.from(e.dataTransfer.files)
      const validFiles = droppedFiles.filter((f) => {
        if (accept.includes("image") && f.type.startsWith("image/")) return true
        if (accept.includes("video") && f.type.startsWith("video/")) return true
        return false
      })

      const newFiles = [...files, ...validFiles].slice(0, maxFiles)
      setFiles(newFiles)
      if (onChange) onChange(newFiles)
    },
    [accept, disabled, files, maxFiles, onChange]
  )

  const handleFileSelect = useCallback(
    (e: React.ChangeEvent<HTMLInputElement>) => {
      if (e.target.files && !disabled) {
        const selectedFiles = Array.from(e.target.files)
        const newFiles = [...files, ...selectedFiles].slice(0, maxFiles)
        setFiles(newFiles)
        if (onChange) onChange(newFiles)
      }
    },
    [disabled, files, maxFiles, onChange]
  )

  const removeFile = useCallback(
    (indexToRemove: number) => {
      if (disabled) return
      const newFiles = files.filter((_, idx) => idx !== indexToRemove)
      setFiles(newFiles)
      if (onChange) onChange(newFiles)
    },
    [disabled, files, onChange]
  )

  return (
    <div className={cn("space-y-4", className)}>
      <div
        className={cn(
          "relative flex cursor-pointer flex-col items-center justify-center rounded-lg border-2 border-dashed border-border p-8 text-center transition-colors",
          isDragging && "border-primary bg-primary/5",
          disabled && "cursor-not-allowed opacity-50",
          !disabled && !isDragging && "hover:border-primary hover:bg-primary/5"
        )}
        onDragOver={handleDragOver}
        onDragLeave={handleDragLeave}
        onDrop={handleDrop}
      >
        <input
          type="file"
          accept={accept}
          multiple
          className="absolute inset-0 z-10 h-full w-full cursor-pointer opacity-0"
          onChange={handleFileSelect}
          disabled={disabled}
        />
        <UploadCloud className="mb-4 h-10 w-10 text-muted-foreground" />
        <h4 className="text-lg font-semibold text-foreground">
          Drag & drop media here
        </h4>
        <p className="mt-1 text-sm text-muted-foreground">
          Or click to browse (max {maxFiles} files)
        </p>
      </div>

      {files.length > 0 && (
        <div className="grid grid-cols-2 gap-4 sm:grid-cols-3 md:grid-cols-4">
          {files.map((file, idx) => (
            <div
              key={`${file.name}-${idx}`}
              className="group relative overflow-hidden rounded-md border border-border"
            >
              {file.type.startsWith("image/") ? (
                // eslint-disable-next-line @next/next/no-img-element
                <img
                  src={URL.createObjectURL(file)}
                  alt={file.name}
                  className="h-24 w-full object-cover"
                />
              ) : (
                <div className="flex h-24 w-full items-center justify-center bg-muted">
                  <span className="text-xs font-semibold text-muted-foreground">
                    VIDEO
                  </span>
                </div>
              )}
              {!disabled && (
                <button
                  type="button"
                  onClick={() => removeFile(idx)}
                  className="absolute right-1 top-1 flex h-6 w-6 items-center justify-center rounded-full bg-black/50 text-white opacity-0 transition-opacity group-hover:opacity-100 focus:opacity-100 hover:bg-danger"
                  aria-label="Remove file"
                >
                  <X className="h-4 w-4" />
                </button>
              )}
              <div className="truncate bg-background p-1 text-center text-xs text-muted-foreground">
                {file.name}
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}
