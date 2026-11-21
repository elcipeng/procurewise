import type { FormEvent, ReactNode } from 'react'
import { Button, ComposedModal, InlineLoading, ModalBody, ModalFooter, ModalHeader } from '@carbon/react'

type FormModalProps = {
  open: boolean
  onClose: () => void
  formId: string
  title: string
  description: string
  submitLabel: string
  isPending: boolean
  onSubmit: (event: FormEvent<HTMLFormElement>) => void
  children: ReactNode
}

/** modal form create dan update. tombol simpan ada di footer modal dan terhubung ke form lewat atribut form */
export function FormModal({
  open,
  onClose,
  formId,
  title,
  description,
  submitLabel,
  isPending,
  onSubmit,
  children,
}: FormModalProps) {
  // modal tidak bisa ditutup selama request simpan berjalan supaya hasilnya tidak hilang tanpa umpan balik
  const close = () => {
    if (!isPending) onClose()
  }
  return (
    <ComposedModal open={open} onClose={close} size="md" preventCloseOnClickOutside>
      <ModalHeader title={title} label={description} closeModal={close} />
      <ModalBody hasForm>
        <form id={formId} onSubmit={onSubmit} className="pw-form" noValidate>
          {children}
        </form>
      </ModalBody>
      <ModalFooter>
        <Button kind="secondary" onClick={onClose} disabled={isPending}>
          Batal
        </Button>
        <Button kind="primary" type="submit" form={formId} disabled={isPending}>
          {isPending ? <InlineLoading description="Menyimpan..." /> : submitLabel}
        </Button>
      </ModalFooter>
    </ComposedModal>
  )
}
