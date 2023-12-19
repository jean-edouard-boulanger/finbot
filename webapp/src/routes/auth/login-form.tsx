import React, { useContext, useState } from "react";
import { useNavigate } from "react-router-dom";

import { AuthContext } from "contexts";

import { LoadingButton } from "components";
import { Credentials } from "contexts/auth";
import { Row, Col, Button, Card, Form, Alert } from "react-bootstrap";
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
    <Row className={"justify-content-center mt-5"}>
      <Col md={5}>
        {loginError && (
          <Row>
            <Col>
              <Alert variant={"danger"}>Invalid email or password</Alert>
            </Col>
          </Row>
        )}
        <Row>
          <Col>
            <Card>
              <Card.Header>Sign-in</Card.Header>
              <Card.Body>
                <Formik
                  initialValues={{ email: "", password: "" }}
                  validationSchema={CREDENTIALS_SCHEMA}
                  onSubmit={handleSubmit}
                >
                  {({ isSubmitting, submitForm }) => (
                    <MetaForm>
                      <Form.Group className="mb-3">
                        <Form.Label>Email address</Form.Label>
                        <Field
                          type="text"
                          name="email"
                          className="form-control"
                        />
                        <ErrorMessage
                          className="text-danger"
                          name="email"
                          component="div"
                        />
                      </Form.Group>
                      <Form.Group className="mb-3">
                        <Form.Label>Password</Form.Label>
                        <Field
                          type="password"
                          name="password"
                          className="form-control"
                        />
                        <ErrorMessage
                          className="text-danger"
                          name="password"
                          component="div"
                        />
                      </Form.Group>
                      <LoadingButton
                        variant="primary"
                        loading={isSubmitting}
                        onClick={() => {
                          setLoginError(null);
                          submitForm();
                        }}
                      >
                        Sign-in
                      </LoadingButton>
                      <Button
                        variant={"link"}
                        onClick={() => navigate("/signup")}
                      >
                        Register
                      </Button>
                    </MetaForm>
                  )}
                </Formik>
              </Card.Body>
            </Card>
          </Col>
        </Row>
      </Col>
    </Row>
  );
};

export default LoginForm;
