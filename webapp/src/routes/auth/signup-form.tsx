import React, { useEffect, useState } from "react";
import { Navigate } from "react-router-dom";
import { CheckCircle } from "lucide-react";

import { useApi, UserAccountsApi } from "clients";
import { isEmailValid } from "utils/email";

import { toast } from "sonner";
import { LoadingButton, PasswordValidationCard } from "components";
import {
  validatePassword,
  PasswordValidationInput,
  PasswordValidationResult,
} from "components/password";
import { Button } from "components/ui/button";
import { Input } from "components/ui/input";
import { Label } from "components/ui/label";
import { Badge } from "components/ui/badge";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "components/ui/select";

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
  form: RegistrationForm,
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
  const userAccountsApi = useApi(UserAccountsApi);
  const [registrationForm, setRegistrationForm] = useState<RegistrationForm>(
    DEFAULT_REGISTRATION_FORM,
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
      await userAccountsApi.createUserAccount({
        createUserAccountRequest: {
          email: form.email,
          fullName: form.fullName,
          password: form.password,
          settings: {
            valuationCcy: form.valuationCurrency,
          },
        },
      });
      setLoading(false);
      setRegistered(true);
      toast.success(
        `You have successfully signed up to finbot. You may now sign into your account`,
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
      <div className="mb-4">
        <h1 className="text-3xl font-bold">
          Register <span className="text-lg font-normal text-muted-foreground">a new finbot account</span>
        </h1>
      </div>
      <div hidden={step !== "personal"}>
        <div className="mb-2">
          <h4 className="text-lg font-semibold">
            <Badge className="mr-2">1</Badge> Personal information
          </h4>
        </div>
        <div className="max-w-lg space-y-4">
          <div className="space-y-2">
            <Label>Full name</Label>
            <div className="flex items-center gap-2">
              <Input
                onChange={handleFormChange}
                value={registrationForm.fullName}
                name="fullName"
                type="text"
              />
              {personalFormValidation.fullNameValid && (
                <CheckCircle className="h-5 w-5 shrink-0 text-green-500" />
              )}
            </div>
          </div>
          <div className="space-y-2">
            <Label>Email address</Label>
            <div className="flex items-center gap-2">
              <Input
                onChange={handleFormChange}
                value={registrationForm.email}
                name="email"
                type="email"
              />
              {personalFormValidation.emailValid && (
                <CheckCircle className="h-5 w-5 shrink-0 text-green-500" />
              )}
            </div>
          </div>
          <div className="space-y-2">
            <Label>Valuation currency</Label>
            <Select
              value={registrationForm.valuationCurrency}
              onValueChange={(value) => {
                setRegistrationForm({
                  ...registrationForm,
                  valuationCurrency: value,
                });
              }}
            >
              <SelectTrigger className="w-48">
                <SelectValue placeholder="Select a currency" />
              </SelectTrigger>
              <SelectContent>
                {VALUATION_CURRENCIES.map((currency) => (
                  <SelectItem key={currency} value={currency}>
                    {currency}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>
          <div className="pt-2">
            <Button
              disabled={!personalFormValidation.valid}
              onClick={async () => {
                if (
                  (
                    await userAccountsApi.isEmailAvailable({
                      email: registrationForm.email,
                    })
                  ).available
                ) {
                  setStep("password");
                } else {
                  toast.error(
                    `Email '${registrationForm.email}' is already used by another finbot account`,
                  );
                }
              }}
            >
              Next: password
            </Button>
          </div>
        </div>
      </div>
      <div hidden={step !== "password"}>
        <div className="grid gap-6 lg:grid-cols-2">
          <div className="space-y-4">
            <h4 className="text-lg font-semibold">
              <Badge className="mr-2">2</Badge> Password
            </h4>
            <div className="space-y-2">
              <Label>Password</Label>
              <Input
                onChange={handleFormChange}
                value={registrationForm.password}
                name="password"
                type="password"
              />
            </div>
            <div className="space-y-2">
              <Label>Confirm password</Label>
              <Input
                onChange={handleFormChange}
                value={registrationForm.passwordConfirm}
                name="passwordConfirm"
                type="password"
              />
            </div>
          </div>
          <div>
            <PasswordValidationCard validation={passwordValidation} />
          </div>
        </div>
        <div className="mt-4 flex items-center gap-2">
          <Button
            variant="outline"
            onClick={() => {
              setStep("personal");
            }}
          >
            Previous
          </Button>
          <LoadingButton
            disabled={!passwordValidation.valid}
            onClick={() => {
              handleSignup({ ...registrationForm });
            }}
            loading={loading}
          >
            Register
          </LoadingButton>
        </div>
      </div>
    </>
  );
};
