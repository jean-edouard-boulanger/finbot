import React, { useContext, useState } from "react";
import { Link } from "react-router-dom";

import { AuthContext } from "contexts";

import { FinbotMark, LoadingButton } from "components";
import { Credentials } from "contexts/auth";
import { useDocumentTitle } from "hooks/use-document-title";
import { Card, CardContent } from "components/ui/card";
import { Label } from "components/ui/label";
import { Alert, AlertDescription } from "components/ui/alert";
import { Formik, Form as MetaForm, Field, ErrorMessage } from "formik";

import * as Yup from "yup";

export interface LoginFormProps {}

const CREDENTIALS_SCHEMA = Yup.object().shape({
  email: Yup.string().required().label("Email"),
  password: Yup.string().required().label("Password"),
});

export const LoginForm: React.FC<LoginFormProps> = () => {
  const { login } = useContext(AuthContext);
  const [loginError, setLoginError] = useState<string | null>(null);
  useDocumentTitle("Sign in");

  const handleSubmit = async (
    values: Credentials,
    { setSubmitting }: { setSubmitting: (submitting: boolean) => void },
  ) => {
    try {
      await login!(values);
    } catch (e) {
      setLoginError(`${e}`);
    }
    setSubmitting(false);
  };

  return (
    <div className="mt-10 flex justify-center">
      <div className="w-full max-w-md">
        <div className="mb-6 flex flex-col items-center text-center">
          <div className="flex items-center gap-2 text-primary">
            <FinbotMark className="h-9 w-9" />
            <span className="text-2xl font-semibold tracking-tight text-foreground">
              finbot
            </span>
          </div>
          <h1 className="mt-4 text-2xl font-semibold tracking-tight">
            Sign in
          </h1>
          <p className="mt-1 text-sm text-muted-foreground">Welcome back.</p>
        </div>

        {loginError && (
          <Alert variant="destructive" className="mb-4">
            <AlertDescription>Invalid email or password</AlertDescription>
          </Alert>
        )}

        <Card>
          <CardContent className="pt-6">
            <Formik
              initialValues={{ email: "", password: "" }}
              validationSchema={CREDENTIALS_SCHEMA}
              onSubmit={handleSubmit}
            >
              {({ isSubmitting }) => (
                <MetaForm>
                  <div className="mb-4 space-y-2">
                    <Label htmlFor="email">Email address</Label>
                    <Field
                      id="email"
                      type="text"
                      name="email"
                      autoFocus
                      className="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background placeholder:text-muted-foreground focus-visible:outline-hidden focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2"
                    />
                    <ErrorMessage
                      className="text-sm text-red-500"
                      name="email"
                      component="div"
                    />
                  </div>
                  <div className="mb-4 space-y-2">
                    <Label htmlFor="password">Password</Label>
                    <Field
                      id="password"
                      type="password"
                      name="password"
                      className="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background placeholder:text-muted-foreground focus-visible:outline-hidden focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2"
                    />
                    <ErrorMessage
                      className="text-sm text-red-500"
                      name="password"
                      component="div"
                    />
                  </div>
                  <LoadingButton
                    type="submit"
                    className="w-full"
                    loading={isSubmitting}
                    onClick={() => setLoginError(null)}
                  >
                    Sign in
                  </LoadingButton>
                </MetaForm>
              )}
            </Formik>
          </CardContent>
        </Card>

        <div className="mt-4 text-center text-sm text-muted-foreground">
          Don&apos;t have an account?{" "}
          <Link
            to="/signup"
            className="text-primary underline underline-offset-4 hover:text-primary/80"
          >
            Register
          </Link>
        </div>
      </div>
    </div>
  );
};

export default LoginForm;
