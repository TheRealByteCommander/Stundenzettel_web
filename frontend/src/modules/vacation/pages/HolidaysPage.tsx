import { useState } from "react";
import { Card, CardContent, CardTitle } from "../../../components/ui/card";
import { Input } from "../../../components/ui/input";
import { Label } from "../../../components/ui/label";
import { useHolidaysQuery } from "../hooks/useHolidays";

const getCurrentYear = () => new Date().getFullYear();

export const HolidaysPage = () => {
  const [year, setYear] = useState(getCurrentYear());
  const { data: holidays, isLoading } = useHolidaysQuery(year);

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString("de-DE", {
      weekday: "long",
      year: "numeric",
      month: "long",
      day: "numeric",
    });
  };

  return (
    <div className="mx-auto flex max-w-4xl flex-col gap-4 sm:gap-6 px-3 sm:px-4 py-4 sm:py-8">
      <div className="flex flex-col gap-2 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <h1 className="text-xl sm:text-2xl font-semibold text-brand-gray">
            Feiertage
          </h1>
          <p className="text-xs sm:text-sm text-gray-600">
            Übersicht aller deutschen und sächsischen Feiertage.
          </p>
        </div>
        <div className="flex items-center gap-2">
          <Label htmlFor="year-select" className="text-sm">Jahr:</Label>
          <Input
            id="year-select"
            type="number"
            min="2020"
            max="2100"
            value={year}
            onChange={(e) => setYear(Number(e.target.value))}
            className="w-24"
          />
        </div>
      </div>

      <Card>
        <CardContent className="space-y-3 sm:space-y-4 py-4 sm:py-6">
          <CardTitle className="text-base sm:text-lg text-brand-gray">
            Feiertage {year}
          </CardTitle>

          {isLoading ? (
            <p className="text-center text-gray-500 py-6">Lade Feiertage…</p>
          ) : holidays && holidays.length > 0 ? (
            <div className="space-y-2">
              {holidays.map((holiday, index) => (
                <div
                  key={index}
                  className="flex flex-col sm:flex-row sm:items-center sm:justify-between rounded-lg border border-gray-200 bg-white p-3 sm:p-4"
                >
                  <div>
                    <p className="font-semibold text-brand-gray">{holiday.name}</p>
                    <p className="text-xs sm:text-sm text-gray-600">
                      {formatDate(holiday.date)}
                    </p>
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <p className="text-center text-gray-500 py-6">
              Keine Feiertage für {year} gefunden.
            </p>
          )}
        </CardContent>
      </Card>
    </div>
  );
};

