import type { ReactNode } from 'react'
import { Label } from '@/components/ui/label'
import { fieldErrorId } from '@/lib/feedback'

type FormFieldProps = {
  id: string
  label: string
  error?: string
  hint?: string
  optional?: boolean
  children: ReactNode
}

export function FormField({ id, label, error, hint, optional, children }: FormFieldProps) {
  return (
    <div className="flex flex-col gap-1.5">
      <Label htmlFor={id}>
        {label}
        {optional && <span className="font-normal text-muted-foreground">(opsional)</span>}
      </Label>
      {children}
      {error ? (
        <p id={fieldErrorId(id)} className="text-caption text-destructive first-letter:uppercase" role="alert">
          {error}
        </p>
      ) : (
        hint && <p className="text-caption text-muted-foreground">{hint}</p>
      )}
    </div>
  )
}
