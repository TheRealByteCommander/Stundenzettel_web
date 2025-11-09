import { AppProviders } from "./providers";
import { AppRouter } from "./routes";

export const App = () => {
  return (
    <AppProviders>
      <AppRouter />
    </AppProviders>
  );
};

