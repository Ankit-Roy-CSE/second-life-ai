"use client"

import Link from "next/link"
import { useRouter } from "next/navigation"
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/Avatar"
import { Badge } from "@/components/ui/Badge"
import { Button } from "@/components/ui/Button"
import { useAuth } from "@/lib/auth-context"

export function NavBar() {
  const { user, logout } = useAuth()
  const router = useRouter()

  const handleLogout = () => {
    logout()
    router.push("/login")
  }

  return (
    <header className="sticky top-0 z-[1100] w-full bg-secondary text-secondary-foreground shadow-sm h-header">
      <div className="mx-auto flex h-full max-w-screen-xl items-center justify-between px-4 md:px-6 lg:px-8">
        <Link href="/" className="flex items-center gap-2 font-bold hover:text-primary">
          <span>Amazon Second Life AI</span>
        </Link>
        <nav className="flex items-center gap-6">
          <Link href="/returns" className="text-sm font-medium text-white hover:text-primary">Returns</Link>
          <Link href="/matches" className="text-sm font-medium text-white hover:text-primary">Matches</Link>
          <Link href="/marketplace" className="text-sm font-medium text-white hover:text-primary">Marketplace</Link>
          <Link href="/dashboard" className="text-sm font-medium text-white hover:text-primary">Dashboard</Link>

          {user ? (
            <>
              {/* Green Credit Balance */}
              <Link href="/sustainability" className="flex items-center gap-2 ml-4 border-l border-white/20 pl-4 hover:opacity-80 transition-opacity">
                <span className="text-sm text-muted">Credits</span>
                <Badge variant="success" className="font-mono">{user.green_credits ?? 0}</Badge>
              </Link>

              {/* User Menu / Avatar */}
              <Avatar aria-label="User menu" className="h-8 w-8 ml-2 cursor-pointer border border-border">
                <AvatarImage src="" alt="User" />
                <AvatarFallback>{user.display_name?.[0]?.toUpperCase() ?? "?"}</AvatarFallback>
              </Avatar>

              {/* Logout */}
              <Button variant="ghost" size="sm" onClick={handleLogout}>
                Log out
              </Button>
            </>
          ) : (
            <Link href="/login" className="text-sm font-medium text-white hover:text-primary ml-4 border-l border-white/20 pl-4">
              Sign in
            </Link>
          )}
        </nav>
      </div>
    </header>
  )
}
