import React from "react";
import { CheckCircle } from "lucide-react";

import { Card, CardContent, CardHeader, CardTitle } from "components/ui/card";

export interface PasswordValidationInput {
  password: string;
  passwordConfirm: string;
}

interface PasswordValidationRule {
  description: string;
  validator(form: PasswordValidationInput): boolean;
}

const PASSWORD_VALIDATION_RULES: Array<PasswordValidationRule> = [
  {
    description: "Must be at least 8 characters",
    validator: ({ password }) => {
      return password.length >= 8;
    },
  },
  {
    description: "Must contain at least a number",
    validator: ({ password }) => {
      return /\d/.test(password);
    },
  },
  {
    description: "Must contain at least one uppercase character",
    validator: ({ password }) => {
      return /[A-Z]/.test(password);
    },
  },
  {
    description: "Must contain at least one special character",
    validator: ({ password }) => {
      return /[!@#$%^&*()_+\-=\[\]{};':"\\|,.<>\/?]+/.test(password); //eslint-disable-line
    },
  },
  {
    description: "Passwords must match",
    validator: ({ password, passwordConfirm }) => {
      return password.length > 0 && password === passwordConfirm;
    },
  },
];

export interface PasswordValidationRuleResult {
  description: string;
  valid: boolean;
}

export interface PasswordValidationResult {
  valid: boolean;
  rules: Array<PasswordValidationRuleResult>;
}

export const validatePassword = (
  input: PasswordValidationInput,
): PasswordValidationResult => {
  let allValid = true;
  const rules: Array<PasswordValidationRuleResult> =
    PASSWORD_VALIDATION_RULES.map((rule) => {
      const valid = rule.validator(input);
      allValid = allValid && valid;
      return {
        description: rule.description,
        valid: rule.validator(input),
      };
    });
  return { valid: allValid, rules };
};

export interface PasswordValidationCardProps {
  validation: PasswordValidationResult;
}

export const PasswordValidationCard: React.FC<PasswordValidationCardProps> = ({
  validation,
}) => {
  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-base">Password rules</CardTitle>
      </CardHeader>
      <CardContent className="p-0">
        <div className="divide-y">
          {validation.rules.map((rule, index) => {
            return (
              <div key={`${index}`} className="px-6 py-3 text-sm">
                {rule.description}
                {rule.valid && (
                  <span className="ml-2 text-green-500">
                    <CheckCircle className="inline h-4 w-4" />
                  </span>
                )}
              </div>
            );
          })}
        </div>
      </CardContent>
    </Card>
  );
};
