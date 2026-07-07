import { Breadcrumbs } from "@heroui/react";
import { Link } from "react-router-dom";

interface BreadcrumbItem {
  label: string;
  to?: string;
}

interface PageBreadcrumbsProps {
  items: BreadcrumbItem[];
}

/** Hierarchical navigation trail for detail pages. */
export function PageBreadcrumbs({ items }: PageBreadcrumbsProps) {
  return (
    <Breadcrumbs>
      {items.map((item) =>
        item.to ? (
          <Breadcrumbs.Item key={item.to}>
            <Link to={item.to} className="text-link hover:underline">
              {item.label}
            </Link>
          </Breadcrumbs.Item>
        ) : (
          <Breadcrumbs.Item key={item.label}>{item.label}</Breadcrumbs.Item>
        ),
      )}
    </Breadcrumbs>
  );
}
