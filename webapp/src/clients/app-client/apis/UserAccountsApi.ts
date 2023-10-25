/* tslint:disable */
/* eslint-disable */
/**
 * Finbot application service
 * API documentation for appwsrv
 *
 * The version of the OpenAPI document: v0.0.2
 *
 *
 * NOTE: This class is auto generated by OpenAPI Generator (https://openapi-generator.tech).
 * https://openapi-generator.tech
 * Do not edit the class manually.
 */

import * as runtime from "../runtime";
import type {
  AppCreateUserAccountRequest,
  AppCreateUserAccountResponse,
  AppGetUserAccountResponse,
  AppGetUserAccountSettingsResponse,
  AppIsEmailAvailableResponse,
  AppIsUserAccountConfiguredResponse,
  AppUpdateUserAccountPasswordRequest,
  AppUpdateUserAccountProfileRequest,
  AppUpdateUserAccountProfileResponse,
  ValidationErrorElement,
} from "../models/index";
import {
  AppCreateUserAccountRequestFromJSON,
  AppCreateUserAccountRequestToJSON,
  AppCreateUserAccountResponseFromJSON,
  AppCreateUserAccountResponseToJSON,
  AppGetUserAccountResponseFromJSON,
  AppGetUserAccountResponseToJSON,
  AppGetUserAccountSettingsResponseFromJSON,
  AppGetUserAccountSettingsResponseToJSON,
  AppIsEmailAvailableResponseFromJSON,
  AppIsEmailAvailableResponseToJSON,
  AppIsUserAccountConfiguredResponseFromJSON,
  AppIsUserAccountConfiguredResponseToJSON,
  AppUpdateUserAccountPasswordRequestFromJSON,
  AppUpdateUserAccountPasswordRequestToJSON,
  AppUpdateUserAccountProfileRequestFromJSON,
  AppUpdateUserAccountProfileRequestToJSON,
  AppUpdateUserAccountProfileResponseFromJSON,
  AppUpdateUserAccountProfileResponseToJSON,
  ValidationErrorElementFromJSON,
  ValidationErrorElementToJSON,
} from "../models/index";

export interface CreateUserAccountRequest {
  appCreateUserAccountRequest?: AppCreateUserAccountRequest;
}

export interface GetUserAccountRequest {
  userAccountId: number;
}

export interface GetUserAccountSettingsRequest {
  userAccountId: number;
}

export interface IsEmailAvailableRequest {
  email: string;
}

export interface IsUserAccountConfiguredRequest {
  userAccountId: number;
}

export interface UpdateUserAccountPasswordRequest {
  userAccountId: number;
  appUpdateUserAccountPasswordRequest?: AppUpdateUserAccountPasswordRequest;
}

export interface UpdateUserAccountProfileRequest {
  userAccountId: number;
  appUpdateUserAccountProfileRequest?: AppUpdateUserAccountProfileRequest;
}

/**
 * UserAccountsApi - interface
 *
 * @export
 * @interface UserAccountsApiInterface
 */
export interface UserAccountsApiInterface {
  /**
   *
   * @summary create_user_account <POST>
   * @param {AppCreateUserAccountRequest} [appCreateUserAccountRequest]
   * @param {*} [options] Override http request option.
   * @throws {RequiredError}
   * @memberof UserAccountsApiInterface
   */
  createUserAccountRaw(
    requestParameters: CreateUserAccountRequest,
    initOverrides?: RequestInit | runtime.InitOverrideFunction,
  ): Promise<runtime.ApiResponse<AppCreateUserAccountResponse>>;

  /**
   *
   * create_user_account <POST>
   */
  createUserAccount(
    requestParameters: CreateUserAccountRequest,
    initOverrides?: RequestInit | runtime.InitOverrideFunction,
  ): Promise<AppCreateUserAccountResponse>;

  /**
   *
   * @summary get_user_account <GET>
   * @param {number} userAccountId
   * @param {*} [options] Override http request option.
   * @throws {RequiredError}
   * @memberof UserAccountsApiInterface
   */
  getUserAccountRaw(
    requestParameters: GetUserAccountRequest,
    initOverrides?: RequestInit | runtime.InitOverrideFunction,
  ): Promise<runtime.ApiResponse<AppGetUserAccountResponse>>;

  /**
   *
   * get_user_account <GET>
   */
  getUserAccount(
    requestParameters: GetUserAccountRequest,
    initOverrides?: RequestInit | runtime.InitOverrideFunction,
  ): Promise<AppGetUserAccountResponse>;

  /**
   *
   * @summary get_user_account_settings <GET>
   * @param {number} userAccountId
   * @param {*} [options] Override http request option.
   * @throws {RequiredError}
   * @memberof UserAccountsApiInterface
   */
  getUserAccountSettingsRaw(
    requestParameters: GetUserAccountSettingsRequest,
    initOverrides?: RequestInit | runtime.InitOverrideFunction,
  ): Promise<runtime.ApiResponse<AppGetUserAccountSettingsResponse>>;

  /**
   *
   * get_user_account_settings <GET>
   */
  getUserAccountSettings(
    requestParameters: GetUserAccountSettingsRequest,
    initOverrides?: RequestInit | runtime.InitOverrideFunction,
  ): Promise<AppGetUserAccountSettingsResponse>;

  /**
   *
   * @summary is_email_available <GET>
   * @param {string} email
   * @param {*} [options] Override http request option.
   * @throws {RequiredError}
   * @memberof UserAccountsApiInterface
   */
  isEmailAvailableRaw(
    requestParameters: IsEmailAvailableRequest,
    initOverrides?: RequestInit | runtime.InitOverrideFunction,
  ): Promise<runtime.ApiResponse<AppIsEmailAvailableResponse>>;

  /**
   *
   * is_email_available <GET>
   */
  isEmailAvailable(
    requestParameters: IsEmailAvailableRequest,
    initOverrides?: RequestInit | runtime.InitOverrideFunction,
  ): Promise<AppIsEmailAvailableResponse>;

  /**
   *
   * @summary is_user_account_configured <GET>
   * @param {number} userAccountId
   * @param {*} [options] Override http request option.
   * @throws {RequiredError}
   * @memberof UserAccountsApiInterface
   */
  isUserAccountConfiguredRaw(
    requestParameters: IsUserAccountConfiguredRequest,
    initOverrides?: RequestInit | runtime.InitOverrideFunction,
  ): Promise<runtime.ApiResponse<AppIsUserAccountConfiguredResponse>>;

  /**
   *
   * is_user_account_configured <GET>
   */
  isUserAccountConfigured(
    requestParameters: IsUserAccountConfiguredRequest,
    initOverrides?: RequestInit | runtime.InitOverrideFunction,
  ): Promise<AppIsUserAccountConfiguredResponse>;

  /**
   *
   * @summary update_user_account_password <PUT>
   * @param {number} userAccountId
   * @param {AppUpdateUserAccountPasswordRequest} [appUpdateUserAccountPasswordRequest]
   * @param {*} [options] Override http request option.
   * @throws {RequiredError}
   * @memberof UserAccountsApiInterface
   */
  updateUserAccountPasswordRaw(
    requestParameters: UpdateUserAccountPasswordRequest,
    initOverrides?: RequestInit | runtime.InitOverrideFunction,
  ): Promise<runtime.ApiResponse<object>>;

  /**
   *
   * update_user_account_password <PUT>
   */
  updateUserAccountPassword(
    requestParameters: UpdateUserAccountPasswordRequest,
    initOverrides?: RequestInit | runtime.InitOverrideFunction,
  ): Promise<object>;

  /**
   *
   * @summary update_user_account_profile <PUT>
   * @param {number} userAccountId
   * @param {AppUpdateUserAccountProfileRequest} [appUpdateUserAccountProfileRequest]
   * @param {*} [options] Override http request option.
   * @throws {RequiredError}
   * @memberof UserAccountsApiInterface
   */
  updateUserAccountProfileRaw(
    requestParameters: UpdateUserAccountProfileRequest,
    initOverrides?: RequestInit | runtime.InitOverrideFunction,
  ): Promise<runtime.ApiResponse<AppUpdateUserAccountProfileResponse>>;

  /**
   *
   * update_user_account_profile <PUT>
   */
  updateUserAccountProfile(
    requestParameters: UpdateUserAccountProfileRequest,
    initOverrides?: RequestInit | runtime.InitOverrideFunction,
  ): Promise<AppUpdateUserAccountProfileResponse>;
}

/**
 *
 */
export class UserAccountsApi
  extends runtime.BaseAPI
  implements UserAccountsApiInterface
{
  /**
   *
   * create_user_account <POST>
   */
  async createUserAccountRaw(
    requestParameters: CreateUserAccountRequest,
    initOverrides?: RequestInit | runtime.InitOverrideFunction,
  ): Promise<runtime.ApiResponse<AppCreateUserAccountResponse>> {
    const queryParameters: any = {};

    const headerParameters: runtime.HTTPHeaders = {};

    headerParameters["Content-Type"] = "application/json";

    const response = await this.request(
      {
        path: `/api/v1/accounts/`,
        method: "POST",
        headers: headerParameters,
        query: queryParameters,
        body: AppCreateUserAccountRequestToJSON(
          requestParameters.appCreateUserAccountRequest,
        ),
      },
      initOverrides,
    );

    return new runtime.JSONApiResponse(response, (jsonValue) =>
      AppCreateUserAccountResponseFromJSON(jsonValue),
    );
  }

  /**
   *
   * create_user_account <POST>
   */
  async createUserAccount(
    requestParameters: CreateUserAccountRequest = {},
    initOverrides?: RequestInit | runtime.InitOverrideFunction,
  ): Promise<AppCreateUserAccountResponse> {
    const response = await this.createUserAccountRaw(
      requestParameters,
      initOverrides,
    );
    return await response.value();
  }

  /**
   *
   * get_user_account <GET>
   */
  async getUserAccountRaw(
    requestParameters: GetUserAccountRequest,
    initOverrides?: RequestInit | runtime.InitOverrideFunction,
  ): Promise<runtime.ApiResponse<AppGetUserAccountResponse>> {
    if (
      requestParameters.userAccountId === null ||
      requestParameters.userAccountId === undefined
    ) {
      throw new runtime.RequiredError(
        "userAccountId",
        "Required parameter requestParameters.userAccountId was null or undefined when calling getUserAccount.",
      );
    }

    const queryParameters: any = {};

    const headerParameters: runtime.HTTPHeaders = {};

    if (this.configuration && this.configuration.accessToken) {
      const token = this.configuration.accessToken;
      const tokenString = await token("bearerAuth", []);

      if (tokenString) {
        headerParameters["Authorization"] = `Bearer ${tokenString}`;
      }
    }
    const response = await this.request(
      {
        path: `/api/v1/accounts/{user_account_id}/`.replace(
          `{${"user_account_id"}}`,
          encodeURIComponent(String(requestParameters.userAccountId)),
        ),
        method: "GET",
        headers: headerParameters,
        query: queryParameters,
      },
      initOverrides,
    );

    return new runtime.JSONApiResponse(response, (jsonValue) =>
      AppGetUserAccountResponseFromJSON(jsonValue),
    );
  }

  /**
   *
   * get_user_account <GET>
   */
  async getUserAccount(
    requestParameters: GetUserAccountRequest,
    initOverrides?: RequestInit | runtime.InitOverrideFunction,
  ): Promise<AppGetUserAccountResponse> {
    const response = await this.getUserAccountRaw(
      requestParameters,
      initOverrides,
    );
    return await response.value();
  }

  /**
   *
   * get_user_account_settings <GET>
   */
  async getUserAccountSettingsRaw(
    requestParameters: GetUserAccountSettingsRequest,
    initOverrides?: RequestInit | runtime.InitOverrideFunction,
  ): Promise<runtime.ApiResponse<AppGetUserAccountSettingsResponse>> {
    if (
      requestParameters.userAccountId === null ||
      requestParameters.userAccountId === undefined
    ) {
      throw new runtime.RequiredError(
        "userAccountId",
        "Required parameter requestParameters.userAccountId was null or undefined when calling getUserAccountSettings.",
      );
    }

    const queryParameters: any = {};

    const headerParameters: runtime.HTTPHeaders = {};

    if (this.configuration && this.configuration.accessToken) {
      const token = this.configuration.accessToken;
      const tokenString = await token("bearerAuth", []);

      if (tokenString) {
        headerParameters["Authorization"] = `Bearer ${tokenString}`;
      }
    }
    const response = await this.request(
      {
        path: `/api/v1/accounts/{user_account_id}/settings/`.replace(
          `{${"user_account_id"}}`,
          encodeURIComponent(String(requestParameters.userAccountId)),
        ),
        method: "GET",
        headers: headerParameters,
        query: queryParameters,
      },
      initOverrides,
    );

    return new runtime.JSONApiResponse(response, (jsonValue) =>
      AppGetUserAccountSettingsResponseFromJSON(jsonValue),
    );
  }

  /**
   *
   * get_user_account_settings <GET>
   */
  async getUserAccountSettings(
    requestParameters: GetUserAccountSettingsRequest,
    initOverrides?: RequestInit | runtime.InitOverrideFunction,
  ): Promise<AppGetUserAccountSettingsResponse> {
    const response = await this.getUserAccountSettingsRaw(
      requestParameters,
      initOverrides,
    );
    return await response.value();
  }

  /**
   *
   * is_email_available <GET>
   */
  async isEmailAvailableRaw(
    requestParameters: IsEmailAvailableRequest,
    initOverrides?: RequestInit | runtime.InitOverrideFunction,
  ): Promise<runtime.ApiResponse<AppIsEmailAvailableResponse>> {
    if (
      requestParameters.email === null ||
      requestParameters.email === undefined
    ) {
      throw new runtime.RequiredError(
        "email",
        "Required parameter requestParameters.email was null or undefined when calling isEmailAvailable.",
      );
    }

    const queryParameters: any = {};

    if (requestParameters.email !== undefined) {
      queryParameters["email"] = requestParameters.email;
    }

    const headerParameters: runtime.HTTPHeaders = {};

    if (this.configuration && this.configuration.accessToken) {
      const token = this.configuration.accessToken;
      const tokenString = await token("bearerAuth", []);

      if (tokenString) {
        headerParameters["Authorization"] = `Bearer ${tokenString}`;
      }
    }
    const response = await this.request(
      {
        path: `/api/v1/accounts/email_available/`,
        method: "GET",
        headers: headerParameters,
        query: queryParameters,
      },
      initOverrides,
    );

    return new runtime.JSONApiResponse(response, (jsonValue) =>
      AppIsEmailAvailableResponseFromJSON(jsonValue),
    );
  }

  /**
   *
   * is_email_available <GET>
   */
  async isEmailAvailable(
    requestParameters: IsEmailAvailableRequest,
    initOverrides?: RequestInit | runtime.InitOverrideFunction,
  ): Promise<AppIsEmailAvailableResponse> {
    const response = await this.isEmailAvailableRaw(
      requestParameters,
      initOverrides,
    );
    return await response.value();
  }

  /**
   *
   * is_user_account_configured <GET>
   */
  async isUserAccountConfiguredRaw(
    requestParameters: IsUserAccountConfiguredRequest,
    initOverrides?: RequestInit | runtime.InitOverrideFunction,
  ): Promise<runtime.ApiResponse<AppIsUserAccountConfiguredResponse>> {
    if (
      requestParameters.userAccountId === null ||
      requestParameters.userAccountId === undefined
    ) {
      throw new runtime.RequiredError(
        "userAccountId",
        "Required parameter requestParameters.userAccountId was null or undefined when calling isUserAccountConfigured.",
      );
    }

    const queryParameters: any = {};

    const headerParameters: runtime.HTTPHeaders = {};

    if (this.configuration && this.configuration.accessToken) {
      const token = this.configuration.accessToken;
      const tokenString = await token("bearerAuth", []);

      if (tokenString) {
        headerParameters["Authorization"] = `Bearer ${tokenString}`;
      }
    }
    const response = await this.request(
      {
        path: `/api/v1/accounts/{user_account_id}/is_configured/`.replace(
          `{${"user_account_id"}}`,
          encodeURIComponent(String(requestParameters.userAccountId)),
        ),
        method: "GET",
        headers: headerParameters,
        query: queryParameters,
      },
      initOverrides,
    );

    return new runtime.JSONApiResponse(response, (jsonValue) =>
      AppIsUserAccountConfiguredResponseFromJSON(jsonValue),
    );
  }

  /**
   *
   * is_user_account_configured <GET>
   */
  async isUserAccountConfigured(
    requestParameters: IsUserAccountConfiguredRequest,
    initOverrides?: RequestInit | runtime.InitOverrideFunction,
  ): Promise<AppIsUserAccountConfiguredResponse> {
    const response = await this.isUserAccountConfiguredRaw(
      requestParameters,
      initOverrides,
    );
    return await response.value();
  }

  /**
   *
   * update_user_account_password <PUT>
   */
  async updateUserAccountPasswordRaw(
    requestParameters: UpdateUserAccountPasswordRequest,
    initOverrides?: RequestInit | runtime.InitOverrideFunction,
  ): Promise<runtime.ApiResponse<object>> {
    if (
      requestParameters.userAccountId === null ||
      requestParameters.userAccountId === undefined
    ) {
      throw new runtime.RequiredError(
        "userAccountId",
        "Required parameter requestParameters.userAccountId was null or undefined when calling updateUserAccountPassword.",
      );
    }

    const queryParameters: any = {};

    const headerParameters: runtime.HTTPHeaders = {};

    headerParameters["Content-Type"] = "application/json";

    if (this.configuration && this.configuration.accessToken) {
      const token = this.configuration.accessToken;
      const tokenString = await token("bearerAuth", []);

      if (tokenString) {
        headerParameters["Authorization"] = `Bearer ${tokenString}`;
      }
    }
    const response = await this.request(
      {
        path: `/api/v1/accounts/{user_account_id}/password/`.replace(
          `{${"user_account_id"}}`,
          encodeURIComponent(String(requestParameters.userAccountId)),
        ),
        method: "PUT",
        headers: headerParameters,
        query: queryParameters,
        body: AppUpdateUserAccountPasswordRequestToJSON(
          requestParameters.appUpdateUserAccountPasswordRequest,
        ),
      },
      initOverrides,
    );

    return new runtime.JSONApiResponse<any>(response);
  }

  /**
   *
   * update_user_account_password <PUT>
   */
  async updateUserAccountPassword(
    requestParameters: UpdateUserAccountPasswordRequest,
    initOverrides?: RequestInit | runtime.InitOverrideFunction,
  ): Promise<object> {
    const response = await this.updateUserAccountPasswordRaw(
      requestParameters,
      initOverrides,
    );
    return await response.value();
  }

  /**
   *
   * update_user_account_profile <PUT>
   */
  async updateUserAccountProfileRaw(
    requestParameters: UpdateUserAccountProfileRequest,
    initOverrides?: RequestInit | runtime.InitOverrideFunction,
  ): Promise<runtime.ApiResponse<AppUpdateUserAccountProfileResponse>> {
    if (
      requestParameters.userAccountId === null ||
      requestParameters.userAccountId === undefined
    ) {
      throw new runtime.RequiredError(
        "userAccountId",
        "Required parameter requestParameters.userAccountId was null or undefined when calling updateUserAccountProfile.",
      );
    }

    const queryParameters: any = {};

    const headerParameters: runtime.HTTPHeaders = {};

    headerParameters["Content-Type"] = "application/json";

    if (this.configuration && this.configuration.accessToken) {
      const token = this.configuration.accessToken;
      const tokenString = await token("bearerAuth", []);

      if (tokenString) {
        headerParameters["Authorization"] = `Bearer ${tokenString}`;
      }
    }
    const response = await this.request(
      {
        path: `/api/v1/accounts/{user_account_id}/profile/`.replace(
          `{${"user_account_id"}}`,
          encodeURIComponent(String(requestParameters.userAccountId)),
        ),
        method: "PUT",
        headers: headerParameters,
        query: queryParameters,
        body: AppUpdateUserAccountProfileRequestToJSON(
          requestParameters.appUpdateUserAccountProfileRequest,
        ),
      },
      initOverrides,
    );

    return new runtime.JSONApiResponse(response, (jsonValue) =>
      AppUpdateUserAccountProfileResponseFromJSON(jsonValue),
    );
  }

  /**
   *
   * update_user_account_profile <PUT>
   */
  async updateUserAccountProfile(
    requestParameters: UpdateUserAccountProfileRequest,
    initOverrides?: RequestInit | runtime.InitOverrideFunction,
  ): Promise<AppUpdateUserAccountProfileResponse> {
    const response = await this.updateUserAccountProfileRaw(
      requestParameters,
      initOverrides,
    );
    return await response.value();
  }
}
