import { Card, CardContent, CardTitle } from "../../../components/ui/card";
import { useCurrentUserQuery } from "../../auth/hooks/useCurrentUser";

export const DashboardPage = () => {
  const { data: user } = useCurrentUserQuery();

  return (
    <div className="mx-auto flex max-w-4xl flex-col gap-6 px-4 py-8">
      <div>
        <h1 className="text-2xl font-semibold text-brand-gray">
          Willkommen zurück{user ? `, ${user.name}` : ""}!
        </h1>
        <p className="mt-1 text-sm text-gray-600">
          Dies ist die neue Tick-Guard-Oberfläche. Funktionen werden
          schrittweise migriert.
        </p>
      </div>

      <Card>
        <CardContent className="space-y-2 py-6">
          <CardTitle className="text-base text-brand-gray">
            Angemeldete Sitzung
          </CardTitle>
          <div className="text-sm text-gray-600">
            <p>E-Mail: {user?.email ?? "–"}</p>
            <p>Rolle: {user?.role ?? "–"}</p>
          </div>
        </CardContent>
      </Card>
    </div>
  );
};

