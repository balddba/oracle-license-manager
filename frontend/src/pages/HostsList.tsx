import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Link } from "react-router-dom";
import { Button, Card, toast } from "@heroui/react";
import { FormField } from "../components/FormField";
import { ErrorAlert } from "../components/ErrorAlert";
import { Modal } from "../components/Modal";
import { TablePageSkeleton } from "../components/PageSkeleton";
import { SelectField } from "../components/SelectField";
import { useState } from "react";
import {
  api,
  formatHostEnvironment,
  HOST_ENVIRONMENT_OPTIONS,
  type HostEnvironment,
  type HostListItem,
} from "../api/client";


const environmentOptions = [
  { value: "", label: "Select environment" },
  ...HOST_ENVIRONMENT_OPTIONS,
];

export function HostsList() {
  const queryClient = useQueryClient();
  const [hostname, setHostname] = useState("");
  const [environment, setEnvironment] = useState("");
  const [selectedHost, setSelectedHost] = useState<HostListItem | null>(null);

  const { data, isLoading, error } = useQuery({
    queryKey: ["hosts"],
    queryFn: api.listHosts,
  });

  const createMutation = useMutation({
    mutationFn: () =>
      api.createHost({
        hostname,
        environment: (environment || null) as HostEnvironment | null,
      }),
    onSuccess: () => {
      setHostname("");
      setEnvironment("");
      void queryClient.invalidateQueries({ queryKey: ["hosts"] });
      void queryClient.invalidateQueries({ queryKey: ["dashboard"] });
      toast.success("Host created");
    },
    onError: () => {
      toast.danger("Failed to create host.");
    },
  });

  if (isLoading) {
    return <TablePageSkeleton />;
  }
  if (error) {
    return <ErrorAlert title="Hosts unavailable" message="Failed to load hosts." />;
  }

  return (
    <div className="space-y-6">
      <h2 className="text-2xl font-semibold">Hosts</h2>
      <p className="text-sm text-muted">
        Servers that consume licenses. Open a host to record assigned products and compare against
        purchased inventory on the dashboard. Save a CPU profile on each host — unsaved form values
        do not appear here.
      </p>

      <Card className="space-y-3 p-4">
        <h3 className="font-medium">New host</h3>
        <div className="grid gap-3 sm:grid-cols-2">
          <FormField label="Hostname" value={hostname} onChange={(e) => setHostname(e.target.value)} />
          <SelectField
            label="Environment"
            value={environment}
            onChange={(e) => setEnvironment(e.target.value)}
            options={environmentOptions}
          />
        </div>
        <Button
          onPress={() => createMutation.mutate()}
          isDisabled={!hostname || createMutation.isPending}
        >
          Create host
        </Button>
      </Card>

      <div className="overflow-hidden rounded-lg border border-border bg-surface">
        <table className="min-w-full text-sm">
          <thead className="bg-default text-left">
            <tr>
              <th className="px-4 py-2">Hostname</th>
              <th className="px-4 py-2">Environment</th>
              <th className="px-4 py-2">Assigned products</th>
              <th className="px-4 py-2">Cores</th>
              <th className="px-4 py-2">Licenses required</th>
            </tr>
          </thead>
          <tbody>
            {data?.length === 0 ? (
              <tr>
                <td colSpan={5} className="px-4 py-6 text-center text-muted">
                  No hosts yet. Create a server, then assign products from the pool.
                </td>
              </tr>
            ) : (
              data?.map((host) => (
                <tr key={host.id} className="border-t border-separator">
                  <td className="px-4 py-2">
                    <Link className="text-link hover:underline" to={`/hosts/${host.id}`}>
                      {host.hostname}
                    </Link>
                  </td>
                  <td className="px-4 py-2">{formatHostEnvironment(host.environment)}</td>
                  <td className="px-4 py-2">
                    {(host.assigned_products ?? []).length > 0 ? (
                      <ul className="list-disc space-y-1 pl-4">
                        {host.assigned_products.map((product) => (
                          <li key={product}>{product}</li>
                        ))}
                      </ul>
                    ) : (
                      "None assigned"
                    )}
                  </td>
                  <td className="px-4 py-2">
                    {host.physical_cores != null ? (
                      host.physical_cores
                    ) : (
                      <span className="text-muted">—</span>
                    )}
                  </td>
                  <td className="px-4 py-2">
                    {host.licenses_required_label ? (
                      <button
                        type="button"
                        className="font-medium text-link underline-offset-2 hover:underline"
                        onClick={() => setSelectedHost(host)}
                      >
                        {host.licenses_required_label}
                      </button>
                    ) : (
                      <button
                        type="button"
                        className="text-muted underline-offset-2 hover:underline"
                        onClick={() => setSelectedHost(host)}
                      >
                        —
                      </button>
                    )}
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>

      <Modal
        title={
          selectedHost
            ? `Licenses required — ${selectedHost.hostname}`
            : "Licenses required"
        }
        isOpen={selectedHost != null}
        onClose={() => setSelectedHost(null)}
      >
        {selectedHost ? (
          <ul className="space-y-2">
            {(selectedHost.licenses_required_detail.length > 0
              ? selectedHost.licenses_required_detail
              : ["No calculation available yet."]
            ).map((line) => (
              <li key={line} className="leading-relaxed">
                {line}
              </li>
            ))}
          </ul>
        ) : null}
      </Modal>
    </div>
  );
}
