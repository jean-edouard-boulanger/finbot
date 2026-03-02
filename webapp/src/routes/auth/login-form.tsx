import React, { useContext, useState } from "react";
import { useNavigate } from "react-router-dom";

import { AuthContext } from "contexts";

import { LoadingButton } from "components";
import { Credentials } from "contexts/auth";
import { Card, CardContent, CardHeader, CardTitle } from "components/ui/card";
import { Button } from "components/ui/button";
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
  const navigate = useNavigate();
  const { login } = useContext(AuthContext);
  const [loginError, setLoginError] = useState<string | null>(null);

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
        {loginError && (
          <Alert variant="destructive" className="mb-4">
            <AlertDescription>Invalid email or password</AlertDescription>
          </Alert>
        )}
        <Card>
          <CardHeader>
            <CardTitle>Sign-in</CardTitle>
          </CardHeader>
          <CardContent>
            <Formik
              initialValues={{ email: "", password: "" }}
              validationSchema={CREDENTIALS_SCHEMA}
              onSubmit={handleSubmit}
            >
              {({ isSubmitting, submitForm }) => (
                <MetaForm>
                  <div className="mb-4 space-y-2">
                    <Label>Email address</Label>
                    <Field
                      type="text"
                      name="email"
                      className="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2"
                    />
                    <ErrorMessage
                      className="text-sm text-red-500"
                      name="email"
                      component="div"
                    />
                  </div>
                  <div className="mb-4 space-y-2">
                    <Label>Password</Label>
                    <Field
                      type="password"
                      name="password"
                      className="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2"
                    />
                    <ErrorMessage
                      className="text-sm text-red-500"
                      name="password"
                      component="div"
                    />
                  </div>
                  <div className="flex items-center gap-2">
                    <LoadingButton
                      loading={isSubmitting}
                      onClick={() => {
                        setLoginError(null);
                        submitForm();
                      }}
                    >
                      Sign-in
                    </LoadingButton>
                    <Button variant="link" onClick={() => navigate("/signup")}>
                      Register
                    </Button>
                  </div>
                </MetaForm>
              )}
            </Formik>
          </CardContent>
        </Card>
      </div>
    </div>
  );
};

export default LoginForm;
