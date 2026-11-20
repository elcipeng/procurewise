import { Boxes, ClipboardList, Store, type LucideIcon } from 'lucide-react'

export type NavItem = {
  to: string
  label: string
  icon: LucideIcon
}

export const NAV_ITEMS: NavItem[] = [
  { to: '/kebutuhan', label: 'Kebutuhan', icon: ClipboardList },
  { to: '/vendor', label: 'Vendor', icon: Store },
  { to: '/material', label: 'Material', icon: Boxes },
]
