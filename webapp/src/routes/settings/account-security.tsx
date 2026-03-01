import React, { useContext, useEffect, useState } from "react";

import { AuthContext } from "contexts";
import { useApi, UserAccountsApi } from "clients";

import { LoadingButton, PasswordValidationCard } from "components";
import {
  validatePassword,
  PasswordValidationInput,
  PasswordValidationResult,
} from "components/password";
import { Input } from "components/ui/input";
import { Label } from "components/ui/label";
import { Separator } from "components/ui/separator";
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
        updateUserAccountPasswordRequest: {
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
      <div className="mb-4">
        <h3 className="text-2xl font-semibold">Account security</h3>
        <Separator className="mt-2" />
      </div>
      <div className="mb-4">
        <h4 className="text-lg font-medium">Update password</h4>
      </div>
      <div className="grid gap-6 lg:grid-cols-2">
        <div className="space-y-4">
          <div className="space-y-2">
            <Label>Old password</Label>
            <Input
              type="password"
              name="oldPassword"
              value={passwordForm.oldPassword}
              onChange={handleFormChange}
            />
          </div>
          <div className="space-y-2">
            <Label>New password</Label>
            <Input
              type="password"
              name="password"
              value={passwordForm.password}
              onChange={handleFormChange}
            />
          </div>
          <div className="space-y-2">
            <Label>Confirm new password</Label>
            <Input
              type="password"
              name="passwordConfirm"
              value={passwordForm.passwordConfirm}
              onChange={handleFormChange}
            />
          </div>
          <LoadingButton
            size="sm"
            onClick={() => {
              handleFormSubmit({ ...passwordForm });
            }}
            loading={loading}
            disabled={!passwordValidation.valid}
          >
            Update password
          </LoadingButton>
        </div>
        <div>
          <PasswordValidationCard validation={passwordValidation} />
        </div>
      </div>
    </>
  );
};
