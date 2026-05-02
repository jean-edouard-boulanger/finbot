import React, { useContext, useEffect, useState } from "react";
import { Link, Navigate } from "react-router-dom";

import { AuthContext } from "contexts";
import { ArrowLeft, ArrowRight, Check, Circle } from "lucide-react";

import { useApi, UserAccountsApi } from "clients";
import { isEmailValid } from "utils/email";
import { formatApiError } from "utils/errors";
import { useDocumentTitle } from "hooks/use-document-title";

import { toast } from "sonner";
import { FinbotMark, LoadingButton } from "components";
import {
  validatePassword,
  PasswordValidationInput,
  PasswordValidationResult,
} from "components/password";
import { Button } from "components/ui/button";
import { Input } from "components/ui/input";
import { Label } from "components/ui/label";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "components/ui/card";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "components/ui/select";
import { cn } from "lib/utils";

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

const StepDots: React.FC<{ current: 1 | 2; total: number }> = ({
  current,
  total,
}) => (
  <div className="flex items-center gap-1.5" aria-hidden="true">
    {Array.from({ length: total }, (_, i) => i + 1).map((n) => (
      <div
        key={n}
        className={cn(
          "h-1.5 w-6 rounded-full transition-colors",
          n === current
            ? "bg-primary"
            : n < current
              ? "bg-primary/40"
              : "bg-muted",
        )}
      />
    ))}
  </div>
);

interface ValidatedInputProps {
  name: string;
  type: string;
  value: string;
  valid: boolean;
  autoFocus?: boolean;
  onChange: React.ChangeEventHandler<HTMLInputElement>;
}

const ValidatedInput: React.FC<ValidatedInputProps> = ({
  name,
  type,
  value,
  valid,
  autoFocus,
  onChange,
}) => (
  <div className="relative">
    <Input
      onChange={onChange}
      value={value}
      name={name}
      id={name}
      type={type}
      autoFocus={autoFocus}
      className={valid ? "pr-9" : ""}
    />
    {valid && (
      <Check className="pointer-events-none absolute right-3 top-1/2 h-4 w-4 -translate-y-1/2 text-green-500" />
    )}
  </div>
);

const PasswordRulesList: React.FC<{ validation: PasswordValidationResult }> = ({
  validation,
}) => (
  <ul className="space-y-1.5 rounded-md border bg-muted/30 p-3 text-sm">
    {validation.rules.map((rule, index) => (
      <li key={index} className="flex items-center gap-2">
        {rule.valid ? (
          <Check className="h-3.5 w-3.5 shrink-0 text-green-500" />
        ) : (
          <Circle className="h-3.5 w-3.5 shrink-0 text-muted-foreground/40" />
        )}
        <span
          className={rule.valid ? "text-foreground" : "text-muted-foreground"}
        >
          {rule.description}
        </span>
      </li>
    ))}
  </ul>
);

export const SignupForm: React.FC<Record<string, never>> = () => {
  const userAccountsApi = useApi(UserAccountsApi);
  const { login } = useContext(AuthContext);
  useDocumentTitle("Create account");
  const [registrationForm, setRegistrationForm] = useState<RegistrationForm>(
    DEFAULT_REGISTRATION_FORM,
  );
  const [passwordValidation, setPasswordValidation] =
    useState<PasswordValidationResult>(() =>
      validatePassword(registrationForm),
    );
  const [personalFormValidation, setPersonalFormValidation] =
    useState<PersonalFormValidationResult>(() =>
      validatePersonalForm(registrationForm),
    );
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

  const handleNextFromPersonal = async () => {
    const result = await userAccountsApi.isEmailAvailable({
      email: registrationForm.email,
    });
    if (result.available) {
      setStep("password");
    } else {
      toast.error(
        `Email '${registrationForm.email}' is already used by another finbot account`,
      );
    }
  };

  const handlePersonalSubmit = async (
    event: React.FormEvent<HTMLFormElement>,
  ) => {
    event.preventDefault();
    if (!personalFormValidation.valid) {
      return;
    }
    await handleNextFromPersonal();
  };

  const handlePasswordSubmit = async (
    event: React.FormEvent<HTMLFormElement>,
  ) => {
    event.preventDefault();
    if (!passwordValidation.valid || loading) {
      return;
    }
    await handleSignup({ ...registrationForm });
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
    } catch (e) {
      setLoading(false);
      toast.error(formatApiError(e));
      return;
    }
    try {
      await login!({ email: form.email, password: form.password });
      toast.success("Welcome to finbot!");
    } catch {
      setLoading(false);
      toast.success("Account created. Please sign in.");
      setRegistered(true);
    }
  };

  if (registered) {
    return <Navigate to={"/login"} replace />;
  }

  const stepNumber = step === "personal" ? 1 : 2;
  const stepLabel = step === "personal" ? "Personal info" : "Password";

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
            Create your account
          </h1>
          <p className="mt-1 text-sm text-muted-foreground">
            It only takes a minute.
          </p>
        </div>

        <Card>
          <CardHeader className="space-y-3">
            <div className="flex items-center justify-between">
              <CardTitle className="text-base">
                Step {stepNumber} of 2 — {stepLabel}
              </CardTitle>
              <StepDots current={stepNumber as 1 | 2} total={2} />
            </div>
            <CardDescription>
              {step === "personal"
                ? "Tell us a bit about yourself."
                : "Pick a strong password to protect your account."}
            </CardDescription>
          </CardHeader>
          <CardContent>
            {step === "personal" && (
              <form onSubmit={handlePersonalSubmit} className="space-y-4">
                <div className="space-y-2">
                  <Label htmlFor="fullName">Full name</Label>
                  <ValidatedInput
                    name="fullName"
                    type="text"
                    value={registrationForm.fullName}
                    valid={personalFormValidation.fullNameValid}
                    onChange={handleFormChange}
                    autoFocus
                  />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="email">Email address</Label>
                  <ValidatedInput
                    name="email"
                    type="email"
                    value={registrationForm.email}
                    valid={personalFormValidation.emailValid}
                    onChange={handleFormChange}
                  />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="valuationCurrency">Valuation currency</Label>
                  <Select
                    value={registrationForm.valuationCurrency}
                    onValueChange={(value) =>
                      setRegistrationForm({
                        ...registrationForm,
                        valuationCurrency: value,
                      })
                    }
                  >
                    <SelectTrigger id="valuationCurrency" className="w-full">
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
                <Button
                  type="submit"
                  className="w-full"
                  disabled={!personalFormValidation.valid}
                >
                  Continue
                  <ArrowRight className="ml-2 h-4 w-4" />
                </Button>
              </form>
            )}

            {step === "password" && (
              <form onSubmit={handlePasswordSubmit} className="space-y-4">
                <div className="space-y-2">
                  <Label htmlFor="password">Password</Label>
                  <Input
                    onChange={handleFormChange}
                    value={registrationForm.password}
                    name="password"
                    id="password"
                    type="password"
                    autoFocus
                  />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="passwordConfirm">Confirm password</Label>
                  <Input
                    onChange={handleFormChange}
                    value={registrationForm.passwordConfirm}
                    name="passwordConfirm"
                    id="passwordConfirm"
                    type="password"
                  />
                </div>
                <PasswordRulesList validation={passwordValidation} />
                <div className="flex items-center gap-2 pt-1">
                  <Button
                    type="button"
                    variant="outline"
                    onClick={() => setStep("personal")}
                  >
                    <ArrowLeft className="mr-2 h-4 w-4" />
                    Back
                  </Button>
                  <LoadingButton
                    type="submit"
                    className="flex-1"
                    disabled={!passwordValidation.valid || loading}
                    loading={loading}
                  >
                    Create account
                  </LoadingButton>
                </div>
              </form>
            )}
          </CardContent>
        </Card>

        <div className="mt-4 text-center text-sm text-muted-foreground">
          Already have an account?{" "}
          <Link
            to="/login"
            className="text-primary underline underline-offset-4 hover:text-primary/80"
          >
            Sign in
          </Link>
        </div>
      </div>
    </div>
  );
};
