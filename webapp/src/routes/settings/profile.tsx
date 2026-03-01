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
import { Label } from "components/ui/label";
import { Separator } from "components/ui/separator";
import { toast } from "sonner";

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
      <div className="mb-4">
        <h3 className="text-2xl font-semibold">Profile</h3>
        <Separator className="mt-2" />
      </div>
      <div className="mb-4">
        <h4 className="text-lg font-medium">Update profile</h4>
      </div>
      <div className="max-w-md">
        <Formik
          enableReinitialize
          validationSchema={PROFILE_SCHEMA}
          initialValues={profile ?? makeProfile()}
          onSubmit={handleSubmit}
        >
          {({ isSubmitting, submitForm }) => (
            <MetaForm>
              <div className="mb-4 space-y-2">
                <Label>Full name</Label>
                <Field
                  type="text"
                  name="fullName"
                  className="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2"
                />
                <ErrorMessage
                  className="text-sm text-red-500"
                  name="fullName"
                  component="div"
                />
              </div>
              <div className="mb-4 space-y-2">
                <Label>Email</Label>
                <Field
                  type="text"
                  name="email"
                  className="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2"
                />
                <ErrorMessage
                  className="text-sm text-red-500"
                  name="email"
                  component="div"
                />
              </div>
              <div className="mb-4 space-y-2">
                <Label>Mobile phone number</Label>
                <Field
                  type="text"
                  name="mobilePhoneNumber"
                  className="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2"
                />
                <ErrorMessage
                  className="text-sm text-red-500"
                  name="mobilePhoneNumber"
                  component="div"
                />
              </div>
              <LoadingButton
                size="sm"
                onClick={submitForm}
                loading={isSubmitting}
              >
                Update
              </LoadingButton>
            </MetaForm>
          )}
        </Formik>
      </div>
    </>
  );
};
