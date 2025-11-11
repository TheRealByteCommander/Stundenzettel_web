import {
  Navigate,
  RouterProvider,
  createBrowserRouter,
} from "react-router-dom";
import { LoginPage } from "../modules/auth/pages/LoginPage";
import { DashboardPage } from "../modules/dashboard/pages/DashboardPage";
import { TimesheetListPage } from "../modules/timesheets/pages/TimesheetListPage";
import { TimesheetDetailPage } from "../modules/timesheets/pages/TimesheetDetailPage";
import { TimesheetCreatePage } from "../modules/timesheets/pages/TimesheetCreatePage";
import { TimesheetAdminPage } from "../modules/timesheets/pages/TimesheetAdminPage";
import { ExpensesOverviewPage } from "../modules/expenses/pages/ExpensesOverviewPage";
import { ExpenseReportDetailPage } from "../modules/expenses/pages/ExpenseReportDetailPage";
import { VehicleManagementPage } from "../modules/admin/pages/VehicleManagementPage";
import { ProtectedLayout } from "./layouts/ProtectedLayout";

const router = createBrowserRouter([
  {
    path: "/",
    element: <Navigate to="/login" replace />,
  },
  {
    path: "/login",
    element: <LoginPage />,
  },
  {
    path: "/app",
    element: <ProtectedLayout />,
    children: [
      {
        index: true,
        element: <DashboardPage />,
      },
      {
        path: "timesheets",
        children: [
          {
            index: true,
            element: <TimesheetListPage />,
          },
          {
            path: "new",
            element: <TimesheetCreatePage />,
          },
          {
            path: "admin/review",
            element: <TimesheetAdminPage />,
          },
          {
            path: ":id",
            element: <TimesheetDetailPage />,
          },
        ],
      },
      {
        path: "expenses",
        children: [
          {
            index: true,
            element: <ExpensesOverviewPage />,
          },
          {
            path: "reports/:id",
            element: <ExpenseReportDetailPage />,
          },
        ],
      },
      {
        path: "admin",
        children: [
          {
            path: "vehicles",
            element: <VehicleManagementPage />,
          },
        ],
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

