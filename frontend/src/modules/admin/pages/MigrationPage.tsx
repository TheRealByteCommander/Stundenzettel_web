import { useState, useEffect } from "react";
import { Alert } from "../../../components/ui/alert";
import { Button } from "../../../components/ui/button";
import {
  Card,
  CardContent,
  CardTitle,
} from "../../../components/ui/card";
import { Input } from "../../../components/ui/input";
import { Label } from "../../../components/ui/label";
import {
  testSourceConnection,
  startMigration,
  getMigrationStatus,
  type SourceConfig,
  type MigrationRequest,
} from "../../../services/api/migration";
import { useQuery } from "@tanstack/react-query";

export const MigrationPage = () => {
  const [sourceType, setSourceType] = useState<"mongo" | "mysql">("mongo");
  const [sourceConfig, setSourceConfig] = useState<SourceConfig>({
    type: "mongo",
    database: "",
  });
  const [message, setMessage] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [testing, setTesting] = useState(false);
  const [migrating, setMigrating] = useState(false);
  const [skipUsers, setSkipUsers] = useState(false);
  const [skipTimesheets, setSkipTimesheets] = useState(false);
  const [skipTravelExpenses, setSkipTravelExpenses] = useState(false);

  // Poll migration status
  const { data: status } = useQuery({
    queryKey: ["migration-status"],
    queryFn: getMigrationStatus,
    enabled: migrating,
    refetchInterval: migrating ? 2000 : false,
  });

  useEffect(() => {
    if (status?.running === false && migrating) {
      setMigrating(false);
      if (status.error) {
        setError(status.error);
      } else if (status.results) {
        setMessage("Migration erfolgreich abgeschlossen!");
      }
    }
  }, [status, migrating]);

  const handleTestConnection = async () => {
    setMessage(null);
    setError(null);
    setTesting(true);

    try {
      const result = await testSourceConnection(sourceConfig);
      setMessage(result.message);
    } catch (err) {
      const errorMessage =
        (err as { response?: { data?: { detail?: string } } }).response?.data
          ?.detail ?? (err as { message?: string }).message ?? "Fehler beim Testen der Verbindung";
      setError(errorMessage);
    } finally {
      setTesting(false);
    }
  };

  const handleStartMigration = async () => {
    if (!sourceConfig.database) {
      setError("Datenbank-Name ist erforderlich");
      return;
    }

    setMessage(null);
    setError(null);
    setMigrating(true);

    try {
      const request: MigrationRequest = {
        source: sourceConfig,
        skip_users: skipUsers,
        skip_timesheets: skipTimesheets,
        skip_travel_expenses: skipTravelExpenses,
      };
      await startMigration(request);
      setMessage("Migration gestartet. Bitte warten...");
    } catch (err) {
      const errorMessage =
        (err as { response?: { data?: { detail?: string } } }).response?.data
          ?.detail ?? (err as { message?: string }).message ?? "Fehler beim Starten der Migration";
      setError(errorMessage);
      setMigrating(false);
    }
  };

  return (
    <div className="mx-auto flex max-w-4xl flex-col gap-4 sm:gap-6 px-3 sm:px-4 py-4 sm:py-8">
      <div>
        <h1 className="text-xl sm:text-2xl font-semibold text-brand-gray">
          Datenbank-Migration
        </h1>
        <p className="text-xs sm:text-sm text-gray-600">
          Migrieren Sie Daten aus einer bestehenden Datenbank. Die Source-Datenbank wird nur gelesen, niemals verändert.
        </p>
      </div>

      {message && <Alert variant="success">{message}</Alert>}
      {error && <Alert variant="destructive">{error}</Alert>}

      {status && (
        <Card>
          <CardContent className="space-y-2 py-4 sm:py-6">
            <CardTitle className="text-base sm:text-lg text-brand-gray">
              Migrations-Status
            </CardTitle>
            <div className="space-y-2 text-sm">
              <p>
                <strong>Status:</strong> {status.running ? "Läuft..." : "Abgeschlossen"}
              </p>
              {status.progress && (
                <p>
                  <strong>Fortschritt:</strong> {status.progress}
                </p>
              )}
              {status.error && (
                <p className="text-red-600">
                  <strong>Fehler:</strong> {status.error}
                </p>
              )}
              {status.results && (
                <div>
                  <strong>Ergebnisse:</strong>
                  <pre className="mt-2 p-2 bg-gray-100 rounded text-xs overflow-auto">
                    {JSON.stringify(status.results as Record<string, unknown>, null, 2)}
                  </pre>
                </div>
              )}
            </div>
          </CardContent>
        </Card>
      )}

      <Card>
        <CardContent className="space-y-4 py-4 sm:py-6">
          <CardTitle className="text-base sm:text-lg text-brand-gray">
            Source-Datenbank konfigurieren
          </CardTitle>

          <div className="space-y-4">
            <div className="space-y-2">
              <Label htmlFor="source-type">Datenbank-Typ</Label>
              <select
                id="source-type"
                className="w-full rounded-md border border-gray-300 bg-white px-3 py-2 text-sm text-gray-700 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-brand-primary focus-visible:ring-offset-2 min-h-[44px] sm:min-h-[40px]"
                value={sourceType}
                onChange={(e) => {
                  const newType = e.target.value as "mongo" | "mysql";
                  setSourceType(newType);
                  setSourceConfig({ ...sourceConfig, type: newType });
                }}
              >
                <option value="mongo">MongoDB</option>
                <option value="mysql">MySQL</option>
              </select>
            </div>

            {sourceType === "mongo" ? (
              <>
                <div className="space-y-2">
                  <Label htmlFor="mongo-connection-string">Connection String (optional)</Label>
                  <Input
                    id="mongo-connection-string"
                    type="text"
                    placeholder="mongodb://localhost:27017"
                    value={sourceConfig.connection_string || ""}
                    onChange={(e) =>
                      setSourceConfig({ ...sourceConfig, connection_string: e.target.value })
                    }
                  />
                </div>
                <div className="grid gap-4 md:grid-cols-2">
                  <div className="space-y-2">
                    <Label htmlFor="mongo-host">Host (falls kein Connection String)</Label>
                    <Input
                      id="mongo-host"
                      type="text"
                      placeholder="localhost"
                      value={sourceConfig.host || ""}
                      onChange={(e) =>
                        setSourceConfig({ ...sourceConfig, host: e.target.value })
                      }
                    />
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="mongo-port">Port</Label>
                    <Input
                      id="mongo-port"
                      type="number"
                      placeholder="27017"
                      value={sourceConfig.port || ""}
                      onChange={(e) =>
                        setSourceConfig({
                          ...sourceConfig,
                          port: e.target.value ? Number(e.target.value) : undefined,
                        })
                      }
                    />
                  </div>
                </div>
              </>
            ) : (
              <div className="grid gap-4 md:grid-cols-2">
                <div className="space-y-2">
                  <Label htmlFor="mysql-host">Host</Label>
                  <Input
                    id="mysql-host"
                    type="text"
                    placeholder="localhost"
                    value={sourceConfig.host || ""}
                    onChange={(e) =>
                      setSourceConfig({ ...sourceConfig, host: e.target.value })
                    }
                  />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="mysql-port">Port</Label>
                  <Input
                    id="mysql-port"
                    type="number"
                    placeholder="3306"
                    value={sourceConfig.port || ""}
                    onChange={(e) =>
                      setSourceConfig({
                        ...sourceConfig,
                        port: e.target.value ? Number(e.target.value) : undefined,
                      })
                    }
                  />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="mysql-user">Benutzername</Label>
                  <Input
                    id="mysql-user"
                    type="text"
                    value={sourceConfig.user || ""}
                    onChange={(e) =>
                      setSourceConfig({ ...sourceConfig, user: e.target.value })
                    }
                  />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="mysql-password">Passwort</Label>
                  <Input
                    id="mysql-password"
                    type="password"
                    value={sourceConfig.password || ""}
                    onChange={(e) =>
                      setSourceConfig({ ...sourceConfig, password: e.target.value })
                    }
                  />
                </div>
              </div>
            )}

            <div className="space-y-2">
              <Label htmlFor="database-name">Datenbank-Name *</Label>
              <Input
                id="database-name"
                type="text"
                value={sourceConfig.database}
                onChange={(e) =>
                  setSourceConfig({ ...sourceConfig, database: e.target.value })
                }
                required
              />
            </div>

            <div className="flex gap-2">
              <Button
                variant="outline"
                onClick={handleTestConnection}
                disabled={testing || !sourceConfig.database}
                className="flex-1"
              >
                {testing ? "Teste..." : "Verbindung testen"}
              </Button>
            </div>
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardContent className="space-y-4 py-4 sm:py-6">
          <CardTitle className="text-base sm:text-lg text-brand-gray">
            Migrations-Optionen
          </CardTitle>

          <div className="space-y-3">
            <label className="flex items-center gap-2 cursor-pointer">
              <input
                type="checkbox"
                checked={skipUsers}
                onChange={(e) => setSkipUsers(e.target.checked)}
                className="rounded border-gray-300 text-brand-primary focus:ring-brand-primary"
              />
              <span className="text-sm text-gray-700">Benutzer überspringen</span>
            </label>
            <label className="flex items-center gap-2 cursor-pointer">
              <input
                type="checkbox"
                checked={skipTimesheets}
                onChange={(e) => setSkipTimesheets(e.target.checked)}
                className="rounded border-gray-300 text-brand-primary focus:ring-brand-primary"
              />
              <span className="text-sm text-gray-700">Stundenzettel überspringen</span>
            </label>
            <label className="flex items-center gap-2 cursor-pointer">
              <input
                type="checkbox"
                checked={skipTravelExpenses}
                onChange={(e) => setSkipTravelExpenses(e.target.checked)}
                className="rounded border-gray-300 text-brand-primary focus:ring-brand-primary"
              />
              <span className="text-sm text-gray-700">Reisekosten überspringen</span>
            </label>
          </div>

          <div className="pt-4">
            <Button
              onClick={handleStartMigration}
              disabled={migrating || !sourceConfig.database || status?.running}
              className="w-full"
            >
              {migrating || status?.running
                ? "Migration läuft..."
                : "Migration starten"}
            </Button>
          </div>
        </CardContent>
      </Card>
    </div>
  );
};

