import React, { useContext } from "react";
import { Route, Routes, Navigate } from "react-router-dom";

import {
  AuthProvider,
  AuthContext,
  ThemeProvider,
  ThemeContext,
  ValuationRefreshProvider,
} from "contexts";

import { Toaster } from "sonner";
import { MainContainer, Navigation } from "components";
import { AppShell } from "components/app-shell";
import { ProfileSettings } from "./routes/settings/profile";
import { AccountSecuritySettings } from "./routes/settings/account-security";
import { LinkedAccountsSettings } from "./routes/settings/linked-accounts";
import { ProvidersSettings } from "./routes/settings/providers";
import { EmailDeliverySettingsPanel } from "./routes/settings/email-delivery";
import {
  LoginForm,
  SignupForm,
  Logout,
  MainDashboard,
  LinkedAccountDashboard,
  PortfolioEditor,
  Portfolios,
  Settings,
  Welcome,
} from "routes";

import "./assets/index.css";
import { AppearanceSettings } from "./routes/settings/appearance";

const GuestRouter = () => {
  return (
    <>
      <Navigation />
      <MainContainer>
        <Routes>
          <Route path="/login" element={<LoginForm />} />
          <Route path="/signup" element={<SignupForm />} />
          <Route path="*" element={<Navigate to={"/login"} replace />} />
        </Routes>
      </MainContainer>
    </>
  );
};

const UserRouter = () => {
  return (
    <AppShell>
      <Routes>
        <Route path="welcome" element={<Welcome />} />
        <Route path="dashboard" element={<MainDashboard />} />
        <Route
          path="dashboard/accounts/:linkedAccountId"
          element={<LinkedAccountDashboard />}
        />
        <Route path="portfolios" element={<Portfolios />} />
        <Route path="portfolios/:portfolioId" element={<PortfolioEditor />} />
        <Route path="logout" element={<Logout />} />
        <Route path="settings" element={<Settings />}>
          <Route path="profile" element={<ProfileSettings />} />
          <Route path="security" element={<AccountSecuritySettings />} />
          <Route path="linked" element={<LinkedAccountsSettings />} />
          <Route path="appearance" element={<AppearanceSettings />} />
          <Route path="admin/providers" element={<ProvidersSettings />} />
          <Route
            path="admin/email_delivery"
            element={<EmailDeliverySettingsPanel />}
          />
          <Route path="" element={<Navigate to={"/settings/profile"} />} />
          <Route path="*" element={<Navigate to={"/settings/profile"} />} />
        </Route>
        <Route path="*" element={<Navigate to={"/dashboard"} replace />} />
      </Routes>
    </AppShell>
  );
};

const AppRouter = () => {
  const { userAccountId } = useContext(AuthContext);
  return userAccountId ? <UserRouter /> : <GuestRouter />;
};

const ThemedToaster = () => {
  const { theme } = useContext(ThemeContext);
  return <Toaster position="bottom-right" duration={7000} theme={theme} />;
};

interface AppProps {}

const App: React.FC<AppProps> = () => {
  return (
    <ThemeProvider>
      <AuthProvider>
        <ThemedToaster />
        <ValuationRefreshProvider>
          <AppRouter />
        </ValuationRefreshProvider>
      </AuthProvider>
    </ThemeProvider>
  );
};

export default App;
