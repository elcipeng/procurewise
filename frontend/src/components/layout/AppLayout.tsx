import { useState } from 'react'
import {
  Content,
  Header,
  HeaderGlobalBar,
  HeaderMenuButton,
  HeaderName,
  SideNav,
  SideNavItems,
  SideNavLink,
  SkipToContent,
  Theme,
} from '@carbon/react'
import { Link, NavLink, Outlet, useLocation } from 'react-router'
import { ErrorBoundary } from '@/components/ErrorBoundary'
import { NAV_ITEMS } from './navigation'
import { ServerStatus } from './ServerStatus'
import { SlowServerNotice } from './SlowServerNotice'

export function AppLayout() {
  const [navOpen, setNavOpen] = useState(false)
  const location = useLocation()

  return (
    <>
      {/* header gelap g100 sesuai pola UI Shell carbon, konten tetap tema terang g10 */}
      <Theme theme="g100">
        <Header aria-label="ProcureWise">
          <SkipToContent href="#main-content">Lewati ke konten utama</SkipToContent>
          <HeaderMenuButton
            aria-label={navOpen ? 'Tutup menu navigasi' : 'Buka menu navigasi'}
            isActive={navOpen}
            aria-expanded={navOpen}
            onClick={() => setNavOpen((open) => !open)}
          />
          <HeaderName as={Link} to="/kebutuhan" prefix="">
            ProcureWise
          </HeaderName>
          <HeaderGlobalBar>
            <ServerStatus />
          </HeaderGlobalBar>
        </Header>
      </Theme>
      <SideNav
        aria-label="Navigasi utama"
        expanded={navOpen}
        onOverlayClick={() => setNavOpen(false)}
        href="#main-content"
      >
        <SideNavItems>
          {NAV_ITEMS.map(({ to, label, icon }) => (
            <SideNavLink
              key={to}
              as={NavLink}
              to={to}
              renderIcon={icon}
              isActive={location.pathname.startsWith(to)}
              onClick={() => setNavOpen(false)}
            >
              {label}
            </SideNavLink>
          ))}
        </SideNavItems>
      </SideNav>

      <Content id="main-content" className="pw-content">
        <SlowServerNotice />
        {/* key per halaman supaya error di satu halaman hilang saat pindah halaman */}
        <ErrorBoundary key={location.pathname}>
          <Outlet />
        </ErrorBoundary>
      </Content>
    </>
  )
}
