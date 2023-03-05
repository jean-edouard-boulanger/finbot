import React, { useContext, useEffect, useState } from "react";
import { Navigate } from "react-router-dom";

import { ServicesContext } from "contexts";

import { isEmailValid } from "utils/email";

import { toast } from "react-toastify";
import { LoadingButton, PasswordValidationCard } from "components";
import {
  validatePassword,
  PasswordValidationInput,
  PasswordValidationResult,
} from "components/password";
import {
  Row,
  Col,
  Form,
  Dropdown,
  Button,
  Badge,
  InputGroup,
} from "react-bootstrap";
import { FaCheckCircle } from "react-icons/fa";

const VALUATION_CURRENCIES = [
  "EUR",
  "GBP",
  "AUD",
  "USD",
  "CAD",
  "JPY",
  "CNY",
  "INR",
  "CHF",
];

type FormStep = "personal" | "password";

interface RegistrationForm extends PasswordValidationInput {
  fullName: string;
  email: string;
  valuationCurrency: string;
}

const DEFAULT_REGISTRATION_FORM: RegistrationForm = {
  fullName: "",
  email: "",
  valuationCurrency: "",
  password: "",
  passwordConfirm: "",
};

interface PersonalFormValidationResult {
  valid: boolean;
  fullNameValid: boolean;
  emailValid: boolean;
  currencyValid: boolean;
}

const validatePersonalForm = (
  form: RegistrationForm
): PersonalFormValidationResult => {
  const fullNameValid = form.fullName.length >= 3;
  const emailValid = isEmailValid(form.email);
  const currencyValid = form.valuationCurrency.length > 0;
  return {
    valid: fullNameValid && emailValid && currencyValid,
    fullNameValid,
    emailValid,
    currencyValid,
  };
};

export const SignupForm: React.FC<Record<string, never>> = () => {
  const { finbotClient } = useContext(ServicesContext);
  const [registrationForm, setRegistrationForm] = useState<RegistrationForm>(
    DEFAULT_REGISTRATION_FORM
  );
  const [passwordValidation, setPasswordValidation] =
    useState<PasswordValidationResult>(() => {
      return validatePassword(registrationForm);
    });
  const [personalFormValidation, setPersonalFormValidation] =
    useState<PersonalFormValidationResult>(() => {
      return validatePersonalForm(registrationForm);
    });
  const [step, setStep] = useState<FormStep>("personal");
  const [loading, setLoading] = useState(false);
  const [registered, setRegistered] = useState(false);

  useEffect(() => {
    if (step === "password") {
      setPasswordValidation(validatePassword(registrationForm));
    }
  }, [step, registrationForm]);

  useEffect(() => {
    if (step === "personal") {
      setPersonalFormValidation(validatePersonalForm(registrationForm));
    }
  }, [step, registrationForm]);

  const handleFormChange = (event: React.ChangeEvent<HTMLInputElement>) => {
    const { name, value } = event.currentTarget;
    setRegistrationForm({
      ...registrationForm,
      [name]: value,
    });
  };

  const handleSignup = async (form: RegistrationForm) => {
    try {
      setLoading(true);
      await finbotClient!.registerAccount({
        email: form.email,
        full_name: form.fullName,
        password: form.password,
        valuation_ccy: form.valuationCurrency,
      });
      setLoading(false);
      setRegistered(true);
      toast.success(
        `You have successfully signed up to finbot. You may now sign into your account`
      );
    } catch (e) {
      setLoading(false);
      toast.error(`${e}`);
    }
  };

  if (registered) {
    return <Navigate to={"/login"} replace />;
  }

  return (
    <>
      <Row>
        <Col>
          <div className={"page-header mb-4"}>
            <h1>
              Register <small>a new finbot account</small>
            </h1>
          </div>
        </Col>
      </Row>
      <div hidden={step !== "personal"}>
        <>
          <Row className={"mb-2"}>
            <Col>
              <h4>
                <Badge variant={"primary"}>1</Badge> Personal information
              </h4>
            </Col>
          </Row>
          <Row>
            <Col lg={6}>
              <Form.Group>
                <Form.Label>Full name</Form.Label>
                <InputGroup>
                  <Form.Control
                    onChange={handleFormChange}
                    value={registrationForm.fullName}
                    name={"fullName"}
                    type={"text"}
                  />
                  {personalFormValidation.fullNameValid && (
                    <InputGroup.Append>
                      <InputGroup.Text>
                        <FaCheckCircle />
                      </InputGroup.Text>
                    </InputGroup.Append>
                  )}
                </InputGroup>
              </Form.Group>
            </Col>
          </Row>
          <Row>
            <Col lg={6}>
              <Form.Group>
                <Form.Label>Email address</Form.Label>
                <InputGroup>
                  <Form.Control
                    onChange={handleFormChange}
                    value={registrationForm.email}
                    name={"email"}
                    type={"email"}
                  />
                  {personalFormValidation.emailValid && (
                    <InputGroup.Append>
                      <InputGroup.Text>
                        <FaCheckCircle />
                      </InputGroup.Text>
                    </InputGroup.Append>
                  )}
                </InputGroup>
              </Form.Group>
            </Col>
          </Row>
          <Row className={"mb-4"}>
            <Col lg={6}>
              <Form.Group>
                <Form.Label>Valuation currency</Form.Label>
                <Dropdown>
                  <Dropdown.Toggle size={"sm"} variant={"secondary"}>
                    {registrationForm.valuationCurrency || "Select a currency"}
                  </Dropdown.Toggle>
                  <Dropdown.Menu>
                    {VALUATION_CURRENCIES.map((currency) => {
                      return (
                        <Dropdown.Item
                          key={currency}
                          active={
                            currency === registrationForm.valuationCurrency
                          }
                          onClick={() => {
                            setRegistrationForm({
                              ...registrationForm,
                              valuationCurrency: currency,
                            });
                          }}
                        >
                          {currency}
                        </Dropdown.Item>
                      );
                    })}
                  </Dropdown.Menu>
                </Dropdown>
              </Form.Group>
            </Col>
          </Row>
          <Row className={"mb-4"}>
            <Col>
              <Button
                disabled={!personalFormValidation.valid}
                onClick={async () => {
                  if (
                    await finbotClient!.isEmailAvailable(registrationForm.email)
                  ) {
                    setStep("password");
                  } else {
                    toast.error(
                      `Email '${registrationForm.email}' is already used by another finbot account`
                    );
                  }
                }}
              >
                Next: password
              </Button>
            </Col>
          </Row>
        </>
      </div>
      <div hidden={step !== "password"}>
        <>
          <Row>
            <Col lg={6}>
              <Row className={"mb-2"}>
                <Col>
                  <h4>
                    <Badge variant={"primary"}>2</Badge> Password
                  </h4>
                </Col>
              </Row>
              <Row>
                <Col>
                  <Form.Group>
                    <Form.Label>Password</Form.Label>
                    <Form.Control
                      onChange={handleFormChange}
                      value={registrationForm.password}
                      name={"password"}
                      type={"password"}
                    />
                  </Form.Group>
                </Col>
              </Row>
              <Row>
                <Col>
                  <Form.Group>
                    <Form.Label>Confirm password</Form.Label>
                    <Form.Control
                      onChange={handleFormChange}
                      value={registrationForm.passwordConfirm}
                      name={"passwordConfirm"}
                      type={"password"}
                    />
                  </Form.Group>
                </Col>
              </Row>
            </Col>
            <Col lg={6}>
              <PasswordValidationCard validation={passwordValidation} />
            </Col>
          </Row>
          <Row>
            <Col>
              <Button
                onClick={() => {
                  setStep("personal");
                }}
              >
                Previous
              </Button>
              &nbsp;
              <LoadingButton
                disabled={!passwordValidation.valid}
                onClick={() => {
                  handleSignup({ ...registrationForm });
                }}
                loading={loading}
              >
                Register
              </LoadingButton>
            </Col>
          </Row>
        </>
      </div>
    </>
  );
};
