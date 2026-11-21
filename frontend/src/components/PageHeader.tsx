import type { ReactNode } from 'react'

type PageHeaderProps = {
  title: string
  description: string
  actions?: ReactNode
}

export function PageHeader({ title, description, actions }: PageHeaderProps) {
  return (
    <div className="pw-page-header">
      <div>
        <h1 className="pw-page-header__title">{title}</h1>
        <p className="pw-page-header__description">{description}</p>
      </div>
      {actions && <div className="pw-page-header__actions">{actions}</div>}
    </div>
  )
}
