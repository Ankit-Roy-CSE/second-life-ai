import Link from "next/link"
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/Avatar"
import { Badge } from "@/components/ui/Badge"

export function NavBar() {
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
          <Link href="/sustainability" className="text-sm font-medium text-white hover:text-primary">Dashboard</Link>
          
          {/* Green Credit Balance */}
          <div className="flex items-center gap-2 ml-4 border-l border-white/20 pl-4">
            <span className="text-sm text-muted">Credits</span>
            <Badge variant="success" className="font-mono">150</Badge>
          </div>

          {/* User Menu / Avatar */}
          <Avatar aria-label="User menu" className="h-8 w-8 ml-2 cursor-pointer border border-border">
            <AvatarImage src="" alt="User" />
            <AvatarFallback>U</AvatarFallback>
          </Avatar>
        </nav>
      </div>
    </header>
  )
}
