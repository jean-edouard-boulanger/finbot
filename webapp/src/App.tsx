import React, { useContext } from "react";
import { Route, Switch, Redirect } from "react-router-dom";

import { AuthProvider, AuthContext, ServicesProvider } from "contexts";

import { ToastContainer, Slide, toast } from "react-toastify";
import { MainContainer, Navigation } from "components";
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
import "bootswatch/dist/lux/bootstrap.min.css";
import "./assets/css/index.css";

toast.configure();

const GuestRouter = () => {
  return (
    <Switch>
      <Route exact path="/login" render={() => <LoginForm />} />
      <Route exact path="/signup" render={() => <SignupForm />} />
      <Redirect to={"/login"} />
    </Switch>
  );
};

const UserRouter = () => {
  return (
    <Switch>
      <Route exact path="/welcome" render={() => <Welcome />} />
      <Route exact path="/dashboard" render={() => <MainDashboard />} />
      <Route exact path="/logout" render={() => <Logout />} />
      <Route path="/settings" render={() => <Settings />} />

      <Redirect to={"/dashboard"} />
    </Switch>
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
