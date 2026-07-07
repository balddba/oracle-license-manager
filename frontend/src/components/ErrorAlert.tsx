import { Alert } from "@heroui/react";

interface ErrorAlertProps {
  message: string;
  title?: string;
}

/** Inline danger alert for page-level or form errors. */
export function ErrorAlert({ message, title }: ErrorAlertProps) {
  return (
    <Alert status="danger">
      <Alert.Indicator />
      <Alert.Content>
        {title ? <Alert.Title>{title}</Alert.Title> : null}
        <Alert.Description>{message}</Alert.Description>
      </Alert.Content>
    </Alert>
  );
}
