import React, { useContext, useEffect, useState } from "react";

import {
  useApi,
  UserAccountsApi,
  UserAccountProfile,
  UserAccount,
  UpdateUserAccountProfileOperationRequest,
} from "clients";
import { AuthContext } from "contexts";
import { LoadingButton } from "components/loading-button";

import { Formik, Form as MetaForm, Field, ErrorMessage } from "formik";
import { Row, Col, Form } from "react-bootstrap";
import { toast } from "react-toastify";

import * as Yup from "yup";

const PROFILE_SCHEMA = Yup.object().shape({
  fullName: Yup.string().required().min(3).max(128).label("Full name"),
  email: Yup.string().required().max(128).email().label("Email"),
  mobilePhoneNumber: Yup.string()
    .max(64)
    .nullable()
    .label("Mobile phone number"),
});

const makeProfile = (
  profile?: Partial<UserAccountProfile> | Partial<UserAccount>,
): UserAccountProfile => {
  return {
    email: profile?.email ?? "",
    fullName: profile?.fullName ?? "",
    mobilePhoneNumber: profile?.mobilePhoneNumber ?? null,
  };
};

const makeUpdateRequest = (
  userAccountId: number,
  profile?: Partial<UserAccountProfile>,
): UpdateUserAccountProfileOperationRequest => {
  return {
    userAccountId: userAccountId,
    updateUserAccountProfileRequest: makeProfile(profile),
  };
};

export const ProfileSettings: React.FC<Record<string, never>> = () => {
  const { userAccountId } = useContext(AuthContext);
  const userAccountsApi = useApi(UserAccountsApi);
  const [profile, setProfile] = useState<UserAccountProfile | null>(null);

  useEffect(() => {
    const fetch = async () => {
      const result = await userAccountsApi.getUserAccount({
        userAccountId: userAccountId!,
      });
      setProfile(makeProfile(result.userAccount));
    };
    fetch();
  }, [userAccountsApi, userAccountId]);

  const handleSubmit = async (
    values: UserAccountProfile,
    { setSubmitting }: { setSubmitting: (submitting: boolean) => void },
  ) => {
    try {
      const result = await userAccountsApi.updateUserAccountProfile(
        makeUpdateRequest(userAccountId!, values),
      );
      setProfile(result.profile);
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
          <hr />
        </Col>
      </Row>
      <Row className={"mb-4"}>
        <Col>
          <h4>Update profile</h4>
        </Col>
      </Row>
      <Row>
        <Col md={6}>
          <Formik
            enableReinitialize
            validationSchema={PROFILE_SCHEMA}
            initialValues={profile ?? makeProfile()}
            onSubmit={handleSubmit}
          >
            {({ isSubmitting, submitForm }) => (
              <MetaForm>
                <Form.Group className="mb-3">
                  <Form.Label>Full name</Form.Label>
                  <Field type="text" name="fullName" className="form-control" />
                  <ErrorMessage
                    className="text-danger"
                    name="fullName"
                    component="div"
                  />
                </Form.Group>
                <Form.Group className="mb-3">
                  <Form.Label>Email</Form.Label>
                  <Field type="text" name="email" className="form-control" />
                  <ErrorMessage
                    className="text-danger"
                    name="email"
                    component="div"
                  />
                </Form.Group>
                <Form.Group className="mb-3">
                  <Form.Label>Mobile phone number</Form.Label>
                  <Field
                    type="text"
                    name="mobilePhoneNumber"
                    className="form-control"
                  />
                  <ErrorMessage
                    className="text-danger"
                    name="mobilePhoneNumber"
                    component="div"
                  />
                </Form.Group>
                <LoadingButton
                  size={"sm"}
                  onClick={submitForm}
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
