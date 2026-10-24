import { useState } from 'react'
import { Menu } from 'lucide-react'
import { Outlet, useLocation } from 'react-router'
import { ErrorBoundary } from '@/components/ErrorBoundary'
import { Button } from '@/components/ui/button'
import { Sheet, SheetContent, SheetDescription, SheetHeader, SheetTitle } from '@/components/ui/sheet'
import { ServerStatus } from './ServerStatus'
import { Brand, SidebarNav } from './SidebarNav'

export function AppLayout() {
  const [menuOpen, setMenuOpen] = useState(false)
  const location = useLocation()

  return (
    <div className="min-h-svh bg-background">
      <aside className="fixed inset-y-0 left-0 hidden w-sidebar flex-col gap-6 border-r border-sidebar-border bg-sidebar px-4 py-5 lg:flex">
        <Brand />
        <SidebarNav />
      </aside>

      <div className="lg:pl-sidebar">
        <header className="sticky top-0 z-30 flex h-header items-center gap-3 border-b bg-card/95 px-4 backdrop-blur sm:px-6 lg:px-8">
          <Button
            variant="ghost"
            size="icon"
            className="lg:hidden"
            onClick={() => setMenuOpen(true)}
            aria-label="Buka menu navigasi"
          >
            <Menu />
          </Button>
          <div className="lg:hidden">
            <Brand />
          </div>
          <div className="ml-auto">
            <ServerStatus />
          </div>
        </header>

        <main className="mx-auto w-full max-w-content px-4 py-6 sm:px-6 lg:px-8">
          {/* key per halaman supaya error di satu halaman hilang saat pindah halaman */}
          <ErrorBoundary key={location.pathname}>
            <Outlet />
          </ErrorBoundary>
        </main>
      </div>

      <Sheet open={menuOpen} onOpenChange={setMenuOpen}>
        <SheetContent side="left" className="w-sidebar gap-6 px-4 py-5">
          <SheetHeader className="p-0">
            <SheetTitle className="sr-only">Menu navigasi</SheetTitle>
            <SheetDescription className="sr-only">Pilih halaman yang ingin dibuka</SheetDescription>
            <Brand />
          </SheetHeader>
          <SidebarNav onNavigate={() => setMenuOpen(false)} />
        </SheetContent>
      </Sheet>
    </div>
  )
}
