import { Card, Skeleton } from "@heroui/react";

/** Skeleton placeholder for dashboard stat cards and inventory table. */
export function DashboardSkeleton() {
  return (
    <div className="space-y-6">
      <Skeleton className="h-8 w-40 rounded-lg" />
      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        {Array.from({ length: 4 }).map((_, index) => (
          <Card key={index} className="p-4">
            <Skeleton className="h-4 w-24 rounded" />
            <Skeleton className="mt-3 h-9 w-16 rounded-lg" />
          </Card>
        ))}
      </div>
      <div className="grid gap-4 sm:grid-cols-3">
        {Array.from({ length: 3 }).map((_, index) => (
          <Card key={index} className="p-4">
            <Skeleton className="h-4 w-32 rounded" />
            <Skeleton className="mt-3 h-9 w-12 rounded-lg" />
          </Card>
        ))}
      </div>
      <div className="space-y-3">
        <Skeleton className="h-6 w-48 rounded" />
        <Skeleton className="h-4 w-full max-w-2xl rounded" />
        <Skeleton className="h-48 w-full rounded-lg" />
      </div>
    </div>
  );
}

/** Skeleton placeholder for list pages with a form and table. */
export function TablePageSkeleton() {
  return (
    <div className="space-y-6">
      <Skeleton className="h-8 w-48 rounded-lg" />
      <Card className="space-y-3 p-4">
        <Skeleton className="h-5 w-32 rounded" />
        <div className="grid gap-3 sm:grid-cols-2">
          <Skeleton className="h-10 rounded-lg" />
          <Skeleton className="h-10 rounded-lg" />
        </div>
        <Skeleton className="h-9 w-36 rounded-lg" />
      </Card>
      <Skeleton className="h-64 w-full rounded-lg" />
    </div>
  );
}

/** Skeleton placeholder for detail pages with header card and content sections. */
export function DetailPageSkeleton() {
  return (
    <div className="space-y-6">
      <Skeleton className="h-4 w-48 rounded" />
      <Card className="space-y-3 p-4">
        <Skeleton className="h-8 w-64 rounded-lg" />
        <Skeleton className="h-4 w-40 rounded" />
        <Skeleton className="h-4 w-56 rounded" />
      </Card>
      <Card className="space-y-3 p-4">
        <Skeleton className="h-5 w-40 rounded" />
        <Skeleton className="h-32 w-full rounded-lg" />
      </Card>
    </div>
  );
}
