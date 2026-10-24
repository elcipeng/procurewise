import { Boxes, Store, type LucideIcon } from 'lucide-react'

export type NavItem = {
  to: string
  label: string
  icon: LucideIcon
}

export const NAV_ITEMS: NavItem[] = [
  { to: '/vendor', label: 'Vendor', icon: Store },
  { to: '/material', label: 'Material', icon: Boxes },
]
