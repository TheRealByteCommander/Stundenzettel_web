import { lazy } from "react";
import {
  Navigate,
  RouterProvider,
  createBrowserRouter,
} from "react-router-dom";
import { ProtectedLayout } from "./layouts/ProtectedLayout";
import { LazySuspense } from "../components/LazySuspense";

// Lazy Loading für Performance-Optimierung
const LoginPage = lazy(() =>
  import("../modules/auth/pages/LoginPage").then((m) => ({ default: m.LoginPage }))
);
const DashboardPage = lazy(() =>
  import("../modules/dashboard/pages/DashboardPage").then((m) => ({
    default: m.DashboardPage,
  }))
);
const TimesheetListPage = lazy(() =>
  import("../modules/timesheets/pages/TimesheetListPage").then((m) => ({
    default: m.TimesheetListPage,
  }))
);
const TimesheetDetailPage = lazy(() =>
  import("../modules/timesheets/pages/TimesheetDetailPage").then((m) => ({
    default: m.TimesheetDetailPage,
  }))
);
const TimesheetCreatePage = lazy(() =>
  import("../modules/timesheets/pages/TimesheetCreatePage").then((m) => ({
    default: m.TimesheetCreatePage,
  }))
);
const TimesheetAdminPage = lazy(() =>
  import("../modules/timesheets/pages/TimesheetAdminPage").then((m) => ({
    default: m.TimesheetAdminPage,
  }))
);
const TimesheetReportingPage = lazy(() =>
  import("../modules/timesheets/pages/TimesheetReportingPage").then((m) => ({
    default: m.TimesheetReportingPage,
  }))
);
const ExpensesOverviewPage = lazy(() =>
  import("../modules/expenses/pages/ExpensesOverviewPage").then((m) => ({
    default: m.ExpensesOverviewPage,
  }))
);
const ExpenseReportDetailPage = lazy(() =>
  import("../modules/expenses/pages/ExpenseReportDetailPage").then((m) => ({
    default: m.ExpenseReportDetailPage,
  }))
);
const VehicleManagementPage = lazy(() =>
  import("../modules/admin/pages/VehicleManagementPage").then((m) => ({
    default: m.VehicleManagementPage,
  }))
);
const UserManagementPage = lazy(() =>
  import("../modules/admin/pages/UserManagementPage").then((m) => ({
    default: m.UserManagementPage,
  }))
);
const SMTPConfigPage = lazy(() =>
  import("../modules/admin/pages/SMTPConfigPage").then((m) => ({
    default: m.SMTPConfigPage,
  }))
);
const AccountingPage = lazy(() =>
  import("../modules/admin/pages/AccountingPage").then((m) => ({
    default: m.AccountingPage,
  }))
);
const AnnouncementsPage = lazy(() =>
  import("../modules/announcements/pages/AnnouncementsPage").then((m) => ({
    default: m.AnnouncementsPage,
  }))
);
const VacationPage = lazy(() =>
  import("../modules/vacation/pages/VacationPage").then((m) => ({
    default: m.VacationPage,
  }))
);

const router = createBrowserRouter([
  {
    path: "/",
    element: <Navigate to="/login" replace />,
  },
  {
    path: "/login",
    element: (
      <LazySuspense>
        <LoginPage />
      </LazySuspense>
    ),
  },
  {
    path: "/app",
    element: <ProtectedLayout />,
    children: [
      {
        index: true,
        element: (
          <LazySuspense>
            <DashboardPage />
          </LazySuspense>
        ),
      },
      {
        path: "timesheets",
        children: [
          {
            index: true,
            element: (
              <LazySuspense>
                <TimesheetListPage />
              </LazySuspense>
            ),
          },
          {
            path: "new",
            element: (
              <LazySuspense>
                <TimesheetCreatePage />
              </LazySuspense>
            ),
          },
          {
            path: "admin/review",
            element: (
              <LazySuspense>
                <TimesheetAdminPage />
              </LazySuspense>
            ),
          },
          {
            path: "reporting",
            element: (
              <LazySuspense>
                <TimesheetReportingPage />
              </LazySuspense>
            ),
          },
          {
            path: ":id",
            element: (
              <LazySuspense>
                <TimesheetDetailPage />
              </LazySuspense>
            ),
          },
        ],
      },
      {
        path: "expenses",
        children: [
          {
            index: true,
            element: (
              <LazySuspense>
                <ExpensesOverviewPage />
              </LazySuspense>
            ),
          },
          {
            path: "reports/:id",
            element: (
              <LazySuspense>
                <ExpenseReportDetailPage />
              </LazySuspense>
            ),
          },
        ],
      },
      {
        path: "admin",
        children: [
          {
            path: "vehicles",
            element: (
              <LazySuspense>
                <VehicleManagementPage />
              </LazySuspense>
            ),
          },
          {
            path: "users",
            element: (
              <LazySuspense>
                <UserManagementPage />
              </LazySuspense>
            ),
          },
          {
            path: "smtp",
            element: (
              <LazySuspense>
                <SMTPConfigPage />
              </LazySuspense>
            ),
          },
          {
            path: "accounting",
            element: (
              <LazySuspense>
                <AccountingPage />
              </LazySuspense>
            ),
          },
        ],
      },
      {
        path: "announcements",
        element: (
          <LazySuspense>
            <AnnouncementsPage />
          </LazySuspense>
        ),
      },
      {
        path: "vacation",
        element: (
          <LazySuspense>
            <VacationPage />
          </LazySuspense>
        ),
      },
    ],
  },
  {
    path: "*",
    element: (
      <div className="flex min-h-screen flex-col items-center justify-center bg-gray-100 text-brand-gray">
        <h1 className="text-2xl font-semibold">Seite nicht gefunden</h1>
        <p className="mt-2 text-sm text-gray-600">
          Die angeforderte Seite existiert nicht.
        </p>
      </div>
    ),
  },
]);

export const AppRouter = () => <RouterProvider router={router} />;

