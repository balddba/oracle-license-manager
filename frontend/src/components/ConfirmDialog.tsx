import { Button } from "@heroui/react";
import { Modal } from "./Modal";

interface ConfirmDialogProps {
  title: string;
  message: string;
  confirmLabel?: string;
  cancelLabel?: string;
  isOpen: boolean;
  isPending?: boolean;
  variant?: "default" | "danger";
  onConfirm: () => void;
  onClose: () => void;
}

/** Modal confirmation dialog for destructive or important actions. */
export function ConfirmDialog({
  title,
  message,
  confirmLabel = "Confirm",
  cancelLabel = "Cancel",
  isOpen,
  isPending = false,
  variant = "default",
  onConfirm,
  onClose,
}: ConfirmDialogProps) {
  return (
    <Modal title={title} isOpen={isOpen} onClose={onClose}>
      <p className="text-muted">{message}</p>
      <div className="mt-4 flex justify-end gap-2">
        <Button variant="tertiary" onPress={onClose} isDisabled={isPending}>
          {cancelLabel}
        </Button>
        <Button
          variant={variant === "danger" ? "danger" : "primary"}
          onPress={onConfirm}
          isDisabled={isPending}
        >
          {confirmLabel}
        </Button>
      </div>
    </Modal>
  );
}
