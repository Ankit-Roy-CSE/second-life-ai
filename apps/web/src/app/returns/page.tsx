"use client"

import React, { useState } from "react"
import { useRouter } from "next/navigation"
import { Button } from "@/components/ui/Button"
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from "@/components/ui/Card"
import { Label } from "@/components/ui/Label"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/Select"
import { FileUpload } from "@/components/features/FileUpload"
import { PageHeader } from "@/components/features/PageHeader"
import { apiClient } from "@/lib/api-client"
import { useToast } from "@/hooks/use-toast"
import { GradePanel } from "@/components/features/GradePanel"
import { Grade } from "../../../types/enums"
import { Progress } from "@/components/ui/Progress"

export default function ReturnsPage() {
  const [files, setFiles] = useState<File[]>([])
  const [reason, setReason] = useState<string>("")
  const [isSubmitting, setIsSubmitting] = useState(false)
  const [gradingProgress, setGradingProgress] = useState(0)
  const [gradeResult, setGradeResult] = useState<{grade: Grade, confidence: number, damageSummary: string, defects: string[]} | null>(null)
  
  const router = useRouter()
  const { toast } = useToast()

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!reason || files.length === 0) {
      toast({ title: "Incomplete", description: "Please select a reason and upload media.", variant: "warning" })
      return
    }

    setIsSubmitting(true)
    
    try {
      await apiClient.createReturn({
        product_id: "prod_demo", // Hardcoded for demo
        reason,
        media_urls: files.map(f => `mock_url_${f.name}`)
      })

      toast({ title: "Return Submitted", description: "Analyzing condition with AI...", variant: "info" })

      // 2. Simulate grading progress
      let p = 0;
      const interval = setInterval(() => {
        p += 20;
        setGradingProgress(p)
        if (p >= 100) clearInterval(interval)
      }, 500)

      // 3. Wait 3 seconds and then show mock Grade Panel (or navigate to detail page)
      setTimeout(() => {
        setGradeResult({
          grade: Grade.A,
          confidence: 0.98,
          damageSummary: "Item appears in excellent condition. No visible scratches or dents.",
          defects: []
        })
        setIsSubmitting(false)
        setGradingProgress(0)
        toast({ title: "Grading Complete", description: "AI analysis finished.", variant: "success" })
      }, 3000)

    } catch (error: unknown) {
      const err = error as Error
      toast({ title: "Error", description: err.message, variant: "destructive" })
      setIsSubmitting(false)
    }
  }

  return (
    <div className="container mx-auto py-8 max-w-screen-xl px-4 md:px-6">
      <PageHeader 
        title="Submit a Return" 
        subtitle="Upload photos or videos of your item to get an instant AI evaluation." 
        className="mb-8"
      />

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        <div className="lg:col-span-2 space-y-6">
          <Card>
            <CardHeader>
              <CardTitle>Item Condition</CardTitle>
              <CardDescription>Select the reason for return and upload evidence.</CardDescription>
            </CardHeader>
            <CardContent>
              <form id="return-form" onSubmit={handleSubmit} className="space-y-6">
                <div className="space-y-3">
                  <Label htmlFor="reason">Reason for return</Label>
                  <Select value={reason} onValueChange={setReason} disabled={isSubmitting || !!gradeResult}>
                    <SelectTrigger id="reason">
                      <SelectValue placeholder="Select a reason" />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="DEFECTIVE">Defective / Does not work</SelectItem>
                      <SelectItem value="DAMAGED">Damaged during shipping</SelectItem>
                      <SelectItem value="NOT_NEEDED">No longer needed</SelectItem>
                      <SelectItem value="WRONG_ITEM">Wrong item sent</SelectItem>
                      <SelectItem value="INACCURATE">Website description inaccurate</SelectItem>
                    </SelectContent>
                  </Select>
                </div>

                <div className="space-y-3">
                  <Label>Media Upload (Images/Video)</Label>
                  <FileUpload 
                    onChange={setFiles} 
                    disabled={isSubmitting || !!gradeResult} 
                  />
                </div>
              </form>
            </CardContent>
            <CardFooter className="flex justify-between border-t p-6 bg-muted/50">
              <Button variant="outline" onClick={() => router.back()} disabled={isSubmitting}>Cancel</Button>
              <Button type="submit" form="return-form" disabled={isSubmitting || !!gradeResult}>
                {isSubmitting ? "Submitting..." : "Submit for AI Inspection"}
              </Button>
            </CardFooter>
          </Card>
        </div>

        <div className="space-y-6 lg:col-span-1">
          {isSubmitting && (
            <Card className="animate-in fade-in-0 slide-in-from-bottom-4">
              <CardHeader>
                <CardTitle className="text-lg">AI Inspecting...</CardTitle>
                <CardDescription>Analyzing images and determining lifecycle path.</CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <Progress value={gradingProgress} className="h-2" />
                <p className="text-sm text-muted-foreground text-center">{gradingProgress}% Complete</p>
              </CardContent>
            </Card>
          )}

          {gradeResult && (
            <div className="animate-in fade-in-0 zoom-in-95 duration-500">
              <GradePanel 
                grade={gradeResult.grade}
                confidence={gradeResult.confidence}
                damageSummary={gradeResult.damageSummary}
                defects={gradeResult.defects}
              />
              <Button className="w-full mt-4" onClick={() => router.push('/returns/mock-id')}>
                View Full Decision
              </Button>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
