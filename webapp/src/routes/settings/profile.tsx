import React, { useContext, useEffect, useState } from "react";

import { ServicesContext, AuthContext } from "contexts";
import { LoadingButton } from "components/loading-button";
import {
  UpdateAccountProfileRequest,
  UserAccount,
  UserAccountProfile,
} from "clients/finbot-client/types";

import { Formik, Form as MetaForm, Field, ErrorMessage } from "formik";
import { Row, Col, Form } from "react-bootstrap";
import { toast } from "react-toastify";

import * as Yup from "yup";

const PROFILE_SCHEMA = Yup.object().shape({
  full_name: Yup.string().required().min(3).max(128).label("Full name"),
  email: Yup.string().required().max(128).email().label("Email"),
  mobile_phone_number: Yup.string()
    .max(64)
    .nullable()
    .label("Mobile phone number"),
});

const makeProfile = (
  profile?: Partial<UserAccountProfile> | Partial<UserAccount>
): UserAccountProfile => {
  return {
    email: profile?.email ?? "",
    full_name: profile?.full_name ?? "",
    mobile_phone_number: profile?.mobile_phone_number ?? null,
  };
};

const makeUpdateRequest = (
  accountId: number,
  profile?: Partial<UserAccountProfile>
): UpdateAccountProfileRequest => {
  return {
    account_id: accountId,
    ...makeProfile(profile),
  };
};

export const ProfileSettings = () => {
  const { finbotClient } = useContext(ServicesContext);
  const auth = useContext(AuthContext);
  const [profile, setProfile] = useState<UserAccountProfile | null>(null);
  const userAccountId = auth.account!.id;

  useEffect(() => {
    const fetch = async () => {
      const userAccount = await finbotClient!.getUserAccount({
        account_id: userAccountId,
      });
      setProfile(makeProfile(userAccount));
    };
    fetch();
  }, [finbotClient, auth.account]);

  const handleSubmit = async (
    values: UserAccountProfile,
    { setSubmitting }: { setSubmitting: (submitting: boolean) => void }
  ) => {
    try {
      const newProfile = await finbotClient!.updateAccountProfile(
        makeUpdateRequest(userAccountId, values)
      );
      setProfile(newProfile);
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
            initialValues={profile ?? makeProfile()}
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
                <Form.Group>
                  <Form.Label>Mobile phone number</Form.Label>
                  <Field
                    type="text"
                    name="mobile_phone_number"
                    className="form-control"
                  />
                  <ErrorMessage
                    className="text-danger"
                    name="mobile_phone_number"
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
