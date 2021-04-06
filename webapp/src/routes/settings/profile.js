import React, { useContext, useEffect, useState } from "react";

import { ServicesContext, AuthContext } from "contexts";

import { Formik, Form as MetaForm, Field, ErrorMessage } from "formik";
import { Row, Col, Form } from "react-bootstrap";
import { LoadingButton } from "../../components/loading-button";
import { toast } from "react-toastify";

import * as Yup from "yup";

const PROFILE_SCHEMA = Yup.object().shape({
  full_name: Yup.string().required().min(3).max(128).label("Full name"),
  email: Yup.string().required().max(128).email().label("Email"),
});

export const ProfileSettings = () => {
  const { finbotClient } = useContext(ServicesContext);
  const auth = useContext(AuthContext);
  const [account, setAccount] = useState(null);

  useEffect(() => {
    const fetch = async () => {
      const userAccount = await finbotClient.getAccount({
        account_id: auth.account.id,
      });
      setAccount(userAccount);
    };
    fetch();
  }, [finbotClient, auth.account]);

  const handleSubmit = async (values, { setSubmitting }) => {
    try {
      const userAccount = await finbotClient.updateAccountProfile({
        account_id: auth.account.id,
        email: values.email,
        full_name: values.full_name,
      });
      setAccount(userAccount);
      toast.success("Profile updated");
    } catch (e) {
      toast.error(`Failed to update profile: ${e}`);
    }
    setSubmitting(false);
  };

  return (
    <>
      <Row className={"mb-4"}>
        <Col>
          <h3>Profile</h3>
        </Col>
      </Row>
      <Row>
        <Col>
          <Formik
            enableReinitialize
            validationSchema={PROFILE_SCHEMA}
            initialValues={account}
            onSubmit={handleSubmit}
          >
            {({ isSubmitting, submitForm }) => (
              <MetaForm>
                <Form.Group>
                  <Form.Label>Full name</Form.Label>
                  <Field
                    type="text"
                    name="full_name"
                    className="form-control"
                  />
                  <ErrorMessage
                    className="text-danger"
                    name="full_name"
                    component="div"
                  />
                </Form.Group>
                <Form.Group>
                  <Form.Label>Email</Form.Label>
                  <Field type="text" name="email" className="form-control" />
                  <ErrorMessage
                    className="text-danger"
                    name="email"
                    component="div"
                  />
                </Form.Group>
                <LoadingButton
                  size={"sm"}
                  onClick={submitForm}
                  variant="dark"
                  loading={isSubmitting}
                >
                  Update
                </LoadingButton>
              </MetaForm>
            )}
          </Formik>
        </Col>
      </Row>
    </>
  );
};
