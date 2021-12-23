import React from "react";
import { Card, ListGroup } from "react-bootstrap";
import { FaCheckCircle } from "react-icons/fa";

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
  input: PasswordValidationInput
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
      <ListGroup className={"list-group-flush"}>
        <ListGroup.Item>
          <strong>Password rules</strong>
        </ListGroup.Item>
        {validation.rules.map((rule, index) => {
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
  );
};
