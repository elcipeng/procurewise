import type { ComponentType } from 'react'
import { Catalog, Document, Store } from '@carbon/icons-react'

export type NavItem = {
  to: string
  label: string
  icon: ComponentType
}

export const NAV_ITEMS: NavItem[] = [
  { to: '/kebutuhan', label: 'Kebutuhan', icon: Document },
  { to: '/vendor', label: 'Vendor', icon: Store },
  { to: '/material', label: 'Material', icon: Catalog },
]
