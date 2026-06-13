import { cn } from "@/lib/utils"
import { NavBar } from "@/components/layout/NavBar"

export function AppShell({ children }: { children: React.ReactNode }) {
  return (
    <div className="flex min-h-screen flex-col">
      <NavBar />
      <main className="mx-auto w-full max-w-screen-xl flex-1 px-4 py-8 md:px-6 lg:px-8">
        {children}
      </main>
    </div>
  )
}
