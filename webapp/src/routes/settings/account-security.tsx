import React, { useContext, useEffect, useState } from "react";

import { Card, Col, Form, ListGroup, Row } from "react-bootstrap";

import { LoadingButton } from "components/loading-button";
import { FaCheckCircle } from "react-icons/fa";
import { toast } from "react-toastify";
import { ServicesContext, AuthContext } from "contexts";

interface PasswordForm {
  oldPassword: string;
  newPassword: string;
  newPasswordConfirm: string;
}

interface PasswordValidationRule {
  description: string;
  validator(form: PasswordForm): boolean;
}

const PASSWORD_VALIDATION_RULES: Array<PasswordValidationRule> = [
  {
    description: "Must be at least 8 characters",
    validator: ({ newPassword }) => {
      return newPassword.length >= 8;
    },
  },
  {
    description: "Must contain at least a number",
    validator: ({ newPassword }) => {
      return /\d/.test(newPassword);
    },
  },
  {
    description: "Must contain at least one lowercase character",
    validator: ({ newPassword }) => {
      return /[a-z]/.test(newPassword);
    },
  },
  {
    description: "Must contain at least one uppercase character",
    validator: ({ newPassword }) => {
      return /[!@#$%^&*()_+\-=\[\]{};':"\\|,.<>\/?]+/.test(newPassword); //eslint-disable-line
    },
  },
  {
    description: "New passwords must match",
    validator: ({ newPassword, newPasswordConfirm }) => {
      console.log([newPassword, newPasswordConfirm]);
      return newPassword.length > 0 && newPassword === newPasswordConfirm;
    },
  },
];

const DEFAULT_PASSWORD_FORM: PasswordForm = {
  oldPassword: "",
  newPassword: "",
  newPasswordConfirm: "",
};

interface PasswordValidationRuleResult {
  description: string;
  valid: boolean;
}

interface PasswordValidation {
  valid: boolean;
  rules: Array<PasswordValidationRuleResult>;
}

const validatePasswordForm = (form: PasswordForm): PasswordValidation => {
  let allValid = true;
  const rules: Array<PasswordValidationRuleResult> = PASSWORD_VALIDATION_RULES.map(
    (rule) => {
      const valid = rule.validator(form);
      allValid = allValid && valid;
      return {
        description: rule.description,
        valid: rule.validator(form),
      };
    }
  );
  return { valid: allValid, rules };
};

export interface AccountSecuritySettingsProps {}

export const AccountSecuritySettings: React.FC<AccountSecuritySettingsProps> = () => {
  const { finbotClient } = useContext(ServicesContext);
  const auth = useContext(AuthContext);
  const [loading, setLoading] = useState<boolean>(false);
  const [passwordForm, setPasswordForm] = useState<PasswordForm>(
    DEFAULT_PASSWORD_FORM
  );
  const [
    passwordValidation,
    setPasswordValidation,
  ] = useState<PasswordValidation>(() => {
    return validatePasswordForm(passwordForm);
  });
  const userAccountId = auth.account!.id;

  useEffect(() => {
    setPasswordValidation(validatePasswordForm(passwordForm));
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
      await finbotClient!.updateUserAccountPassword({
        account_id: userAccountId,
        old_password: form.oldPassword,
        new_password: form.newPassword,
      });
      toast.success("Password updated successfully");
      setPasswordForm(DEFAULT_PASSWORD_FORM);
    } catch (e) {
      toast.error(`Failed to update password: ${e}`);
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
            <Form.Group>
              <Form.Label>Old password</Form.Label>
              <Form.Control
                type="password"
                name="oldPassword"
                value={passwordForm.oldPassword}
                onChange={handleFormChange}
              />
            </Form.Group>
            <Form.Group>
              <Form.Label>New password</Form.Label>
              <Form.Control
                type="password"
                name="newPassword"
                value={passwordForm.newPassword}
                onChange={handleFormChange}
              />
            </Form.Group>
            <Form.Group>
              <Form.Label>Confirm new password</Form.Label>
              <Form.Control
                type="password"
                name="newPasswordConfirm"
                value={passwordForm.newPasswordConfirm}
                onChange={handleFormChange}
              />
            </Form.Group>
            <LoadingButton
              size={"sm"}
              onClick={() => {
                handleFormSubmit({ ...passwordForm });
              }}
              variant="dark"
              loading={loading}
              disabled={!passwordValidation.valid}
            >
              Update password
            </LoadingButton>
          </Form>
        </Col>
        <Col>
          <Card>
            <ListGroup className={"list-group-flush"}>
              <ListGroup.Item>
                <strong>Password validation rules</strong>
              </ListGroup.Item>
              {passwordValidation.rules.map((rule, index) => {
                return (
                  <ListGroup.Item key={`${index}`}>
                    {rule.description}
                    {rule.valid && (
                      <span className={"text-success"}>
                        &nbsp;
                        <FaCheckCircle />
                      </span>
                    )}
                  </ListGroup.Item>
                );
              })}
            </ListGroup>
          </Card>
        </Col>
      </Row>
    </>
  );
};
