import { Modal } from '@carbon/react'

type ConfirmDialogProps = {
  open: boolean
  onOpenChange: (open: boolean) => void
  title: string
  description: string
  confirmLabel: string
  isPending: boolean
  onConfirm: () => void
  // destructive untuk hapus atau nonaktifkan, default untuk aksi yang tidak menghilangkan data
  tone?: 'destructive' | 'default'
}

export function ConfirmDialog({
  open,
  onOpenChange,
  title,
  description,
  confirmLabel,
  isPending,
  onConfirm,
  tone = 'destructive',
}: ConfirmDialogProps) {
  return (
    <Modal
      open={open}
      size="sm"
      danger={tone === 'destructive'}
      modalHeading={title}
      primaryButtonText={confirmLabel}
      secondaryButtonText="Batal"
      // dialog ditutup oleh pemanggil setelah request selesai, bukan saat tombol diklik
      onRequestSubmit={onConfirm}
      onRequestClose={() => !isPending && onOpenChange(false)}
      loadingStatus={isPending ? 'active' : 'inactive'}
      loadingDescription="Memproses..."
      primaryButtonDisabled={isPending}
    >
      <p>{description}</p>
    </Modal>
  )
}
