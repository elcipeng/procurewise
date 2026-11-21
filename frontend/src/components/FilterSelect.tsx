import { Select, SelectItem } from '@carbon/react'

export type Option = { value: string; label: string }

type FilterSelectProps = {
  id: string
  label: string
  value: string
  onChange: (value: string) => void
  options: Option[]
}

/** filter daftar di toolbar tabel, label disembunyikan secara visual tapi tetap dibaca screen reader */
export function FilterSelect({ id, label, value, onChange, options }: FilterSelectProps) {
  return (
    <Select
      id={id}
      labelText={label}
      hideLabel
      size="lg"
      className="pw-filter-select"
      value={value}
      onChange={(event) => onChange(event.target.value)}
    >
      {options.map((option) => (
        <SelectItem key={option.value} value={option.value} text={option.label} />
      ))}
    </Select>
  )
}
