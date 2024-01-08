import React, { useContext, useEffect, useState } from "react";

import { AuthContext } from "contexts";
import { useApi, UserAccountsApi } from "clients";

import { LoadingButton, PasswordValidationCard } from "components";
import {
  validatePassword,
  PasswordValidationInput,
  PasswordValidationResult,
} from "components/password";
import { Col, Form, Row } from "react-bootstrap";
import { toast } from "react-toastify";

interface PasswordForm extends PasswordValidationInput {
  oldPassword: string;
}

const DEFAULT_PASSWORD_FORM: PasswordForm = {
  oldPassword: "",
  password: "",
  passwordConfirm: "",
};

export interface AccountSecuritySettingsProps {}

export const AccountSecuritySettings: React.FC<
  AccountSecuritySettingsProps
> = () => {
  const { userAccountId } = useContext(AuthContext);
  const [loading, setLoading] = useState<boolean>(false);
  const [passwordForm, setPasswordForm] = useState<PasswordForm>(
    DEFAULT_PASSWORD_FORM,
  );
  const [passwordValidation, setPasswordValidation] =
    useState<PasswordValidationResult>(() => {
      return validatePassword(passwordForm);
    });
  const userAccountsApi = useApi(UserAccountsApi);

  useEffect(() => {
    setPasswordValidation(validatePassword(passwordForm));
  }, [passwordForm]);

  const handleFormChange = (event: React.ChangeEvent<HTMLInputElement>) => {
    const { name, value } = event.currentTarget;
    setPasswordForm({
      ...passwordForm,
      [name]: value,
    });
  };

  const handleFormSubmit = async (form: PasswordForm) => {
    try {
      setLoading(true);
      await userAccountsApi.updateUserAccountPassword({
        userAccountId: userAccountId!,
        appUpdateUserAccountPasswordRequest: {
          oldPassword: form.oldPassword,
          newPassword: form.password,
        },
      });
      toast.success("Password updated successfully");
      setPasswordForm(DEFAULT_PASSWORD_FORM);
    } catch (e) {
      toast.error(`${e}`);
    }
    setLoading(false);
  };

  return (
    <>
      <Row className={"mb-4"}>
        <Col>
          <h3>Account security</h3>
          <hr />
        </Col>
      </Row>
      <Row className={"mb-4"}>
        <Col>
          <h4>Update password</h4>
        </Col>
      </Row>
      <Row>
        <Col>
          <Form>
            <Form.Group className="mb-4">
              <Form.Label>Old password</Form.Label>
              <Form.Control
                type="password"
                name="oldPassword"
                value={passwordForm.oldPassword}
                onChange={handleFormChange}
              />
            </Form.Group>
            <Form.Group className="mb-4">
              <Form.Label>New password</Form.Label>
              <Form.Control
                type="password"
                name="password"
                value={passwordForm.password}
                onChange={handleFormChange}
              />
            </Form.Group>
            <Form.Group className="mb-4">
              <Form.Label>Confirm new password</Form.Label>
              <Form.Control
                type="password"
                name="passwordConfirm"
                value={passwordForm.passwordConfirm}
                onChange={handleFormChange}
              />
            </Form.Group>
            <LoadingButton
              size={"sm"}
              onClick={() => {
                handleFormSubmit({ ...passwordForm });
              }}
              variant="primary"
              loading={loading}
              disabled={!passwordValidation.valid}
            >
              Update password
            </LoadingButton>
          </Form>
        </Col>
        <Col>
          <PasswordValidationCard validation={passwordValidation} />
        </Col>
      </Row>
    </>
  );
};
