import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { cn } from '@/lib/utils'

export type Option = { value: string; label: string }

type OptionSelectProps = {
  value: string
  onValueChange: (value: string) => void
  options: Option[]
  placeholder?: string
  id?: string
  className?: string
  invalid?: boolean
  describedBy?: string
  'aria-label'?: string
  'aria-labelledby'?: string
}

export function OptionSelect({
  value,
  onValueChange,
  options,
  placeholder,
  id,
  className,
  invalid,
  describedBy,
  ...aria
}: OptionSelectProps) {
  return (
    <Select value={value} onValueChange={onValueChange}>
      <SelectTrigger
        id={id}
        className={cn('w-full', className)}
        aria-invalid={invalid || undefined}
        aria-describedby={describedBy}
        {...aria}
      >
        <SelectValue placeholder={placeholder} />
      </SelectTrigger>
      <SelectContent>
        {options.map((option) => (
          <SelectItem key={option.value} value={option.value}>
            {option.label}
          </SelectItem>
        ))}
      </SelectContent>
    </Select>
  )
}
