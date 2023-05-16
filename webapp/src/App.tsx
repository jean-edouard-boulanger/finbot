import React, { useContext } from "react";
import { Route, Routes, Navigate } from "react-router-dom";

import { AuthProvider, AuthContext, ServicesProvider } from "contexts";

import { ToastContainer, Slide } from "react-toastify";
import { MainContainer, Navigation } from "components";
import { ProfileSettings } from "./routes/settings/profile";
import { AccountSecuritySettings } from "./routes/settings/account-security";
import {
  AccountsPanel,
  LinkedAccountsSettings,
} from "./routes/settings/linked-accounts";
import { TwilioIntegrationSettings } from "./routes/settings/twilio-integration";
import { PlaidIntegrationSettings } from "./routes/settings/plaid-integration";
import { ProvidersSettings } from "./routes/settings/providers";
import { EmailDeliverySettingsPanel } from "./routes/settings/email-delivery";
import {
  UpdateLinkedAccountPanel,
  LinkedAccountStatusPanel,
} from "./routes/settings/linked-accounts";
import {
  LoginForm,
  SignupForm,
  Logout,
  MainDashboard,
  Settings,
  Welcome,
} from "routes";

import "datejs";

import "react-toastify/dist/ReactToastify.css";
import "bootswatch/dist/zephyr/bootstrap.min.css";
import "./assets/css/index.css";
import { LinkAccount } from "./routes/settings/link-account";

const GuestRouter = () => {
  return (
    <Routes>
      <Route path="/login" element={<LoginForm />} />
      <Route path="/signup" element={<SignupForm />} />
      <Route path="*" element={<Navigate to={"/login"} replace />} />
    </Routes>
  );
};

const UserRouter = () => {
  return (
    <Routes>
      <Route path="welcome" element={<Welcome />} />
      <Route path="dashboard" element={<MainDashboard />} />
      <Route path="logout" element={<Logout />} />
      <Route path="settings" element={<Settings />}>
        <Route path="profile" element={<ProfileSettings />} />
        <Route path="security" element={<AccountSecuritySettings />} />
        <Route path="linked" element={<LinkedAccountsSettings />}>
          <Route path="new" element={<LinkAccount />} />
          <Route
            path=":linkedAccountId/edit"
            element={<UpdateLinkedAccountPanel />}
          />
          <Route
            path=":linkedAccountId/status"
            element={<LinkedAccountStatusPanel />}
          />
          <Route path="" element={<AccountsPanel />} />
          <Route path="*" element={<AccountsPanel />} />
        </Route>
        <Route path="twilio" element={<TwilioIntegrationSettings />} />
        <Route path="plaid" element={<PlaidIntegrationSettings />} />
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
  );
};

const AppRouter = () => {
  const { isAuthenticated } = useContext(AuthContext);
  return isAuthenticated ? <UserRouter /> : <GuestRouter />;
};

interface AppProps {}

const App: React.FC<AppProps> = () => {
  return (
    <ServicesProvider>
      <AuthProvider>
        <ToastContainer
          autoClose={7000}
          transition={Slide}
          position="bottom-right"
        />
        <Navigation />
        <MainContainer>
          <AppRouter />
        </MainContainer>
      </AuthProvider>
    </ServicesProvider>
  );
};

export default App;
