const TIME_ZONE = 'Asia/Jakarta'

const dateTimeFormatter = new Intl.DateTimeFormat('id-ID', {
  dateStyle: 'medium',
  timeStyle: 'short',
  timeZone: TIME_ZONE,
})
const dateFormatter = new Intl.DateTimeFormat('id-ID', { dateStyle: 'medium', timeZone: 'UTC' })
const rupiahFormatter = new Intl.NumberFormat('id-ID', {
  style: 'currency',
  currency: 'IDR',
  maximumFractionDigits: 0,
})
const percentFormatter = new Intl.NumberFormat('id-ID', { style: 'percent', maximumFractionDigits: 1 })
const decimalFormatter = new Intl.NumberFormat('id-ID', { maximumFractionDigits: 2 })
// en-CA menghasilkan format yyyy-mm-dd, sama dengan format tanggal dari API
const isoDateFormatter = new Intl.DateTimeFormat('en-CA', { timeZone: TIME_ZONE })

export const formatDateTime = (value: string) => dateTimeFormatter.format(new Date(value))

// tanggal tanpa jam dari API diparse sebagai utc, jadi diformat dengan zona utc supaya tidak bergeser sehari
export const formatDate = (value: string) => dateFormatter.format(new Date(value))

export const formatRupiah = (value: number) => rupiahFormatter.format(value)

export const formatPercent = (value: number) => percentFormatter.format(value)

export const formatNumber = (value: number) => decimalFormatter.format(value)

export const todayInJakarta = () => isoDateFormatter.format(new Date())

// tanggal dari date picker adalah tengah malam waktu lokal, jadi bagian tanggalnya diambil tanpa konversi zona
export const toIsoDate = (date: Date) =>
  `${date.getFullYear()}-${String(date.getMonth() + 1).padStart(2, '0')}-${String(date.getDate()).padStart(2, '0')}`
