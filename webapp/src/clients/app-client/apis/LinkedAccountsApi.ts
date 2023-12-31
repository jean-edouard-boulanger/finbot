/* tslint:disable */
/* eslint-disable */
/**
 * Finbot application service
 * API documentation for appwsrv
 *
 * The version of the OpenAPI document: v0.0.3
 *
 *
 * NOTE: This class is auto generated by OpenAPI Generator (https://openapi-generator.tech).
 * https://openapi-generator.tech
 * Do not edit the class manually.
 */

import * as runtime from "../runtime";
import type {
  AppGetLinkedAccountResponse,
  AppGetLinkedAccountsResponse,
  AppLinkAccountRequest,
  AppUpdateLinkedAccountCredentialsRequest,
  AppUpdateLinkedAccountMetadataRequest,
  ValidationErrorElement,
} from "../models/index";
import {
  AppGetLinkedAccountResponseFromJSON,
  AppGetLinkedAccountResponseToJSON,
  AppGetLinkedAccountsResponseFromJSON,
  AppGetLinkedAccountsResponseToJSON,
  AppLinkAccountRequestFromJSON,
  AppLinkAccountRequestToJSON,
  AppUpdateLinkedAccountCredentialsRequestFromJSON,
  AppUpdateLinkedAccountCredentialsRequestToJSON,
  AppUpdateLinkedAccountMetadataRequestFromJSON,
  AppUpdateLinkedAccountMetadataRequestToJSON,
  ValidationErrorElementFromJSON,
  ValidationErrorElementToJSON,
} from "../models/index";

export interface DeleteLinkedAccountRequest {
  userAccountId: number;
  linkedAccountId: number;
}

export interface GetLinkedAccountRequest {
  userAccountId: number;
  linkedAccountId: number;
}

export interface GetUserAccountLinkedAccountsRequest {
  userAccountId: number;
}

export interface LinkNewAccountRequest {
  userAccountId: number;
  validate?: boolean;
  persist?: boolean;
  appLinkAccountRequest?: AppLinkAccountRequest;
}

export interface UpdateLinkedAccountCredentialsRequest {
  userAccountId: number;
  linkedAccountId: number;
  validate?: boolean;
  persist?: boolean;
  appUpdateLinkedAccountCredentialsRequest?: AppUpdateLinkedAccountCredentialsRequest;
}

export interface UpdateLinkedAccountMetadataRequest {
  userAccountId: number;
  linkedAccountId: number;
  appUpdateLinkedAccountMetadataRequest?: AppUpdateLinkedAccountMetadataRequest;
}

/**
 * LinkedAccountsApi - interface
 *
 * @export
 * @interface LinkedAccountsApiInterface
 */
export interface LinkedAccountsApiInterface {
  /**
   *
   * @summary Delete linked account
   * @param {number} userAccountId
   * @param {number} linkedAccountId
   * @param {*} [options] Override http request option.
   * @throws {RequiredError}
   * @memberof LinkedAccountsApiInterface
   */
  deleteLinkedAccountRaw(
    requestParameters: DeleteLinkedAccountRequest,
    initOverrides?: RequestInit | runtime.InitOverrideFunction,
  ): Promise<runtime.ApiResponse<object>>;

  /**
   *
   * Delete linked account
   */
  deleteLinkedAccount(
    requestParameters: DeleteLinkedAccountRequest,
    initOverrides?: RequestInit | runtime.InitOverrideFunction,
  ): Promise<object>;

  /**
   *
   * @summary Get linked account
   * @param {number} userAccountId
   * @param {number} linkedAccountId
   * @param {*} [options] Override http request option.
   * @throws {RequiredError}
   * @memberof LinkedAccountsApiInterface
   */
  getLinkedAccountRaw(
    requestParameters: GetLinkedAccountRequest,
    initOverrides?: RequestInit | runtime.InitOverrideFunction,
  ): Promise<runtime.ApiResponse<AppGetLinkedAccountResponse>>;

  /**
   *
   * Get linked account
   */
  getLinkedAccount(
    requestParameters: GetLinkedAccountRequest,
    initOverrides?: RequestInit | runtime.InitOverrideFunction,
  ): Promise<AppGetLinkedAccountResponse>;

  /**
   *
   * @summary Get linked accounts
   * @param {number} userAccountId
   * @param {*} [options] Override http request option.
   * @throws {RequiredError}
   * @memberof LinkedAccountsApiInterface
   */
  getUserAccountLinkedAccountsRaw(
    requestParameters: GetUserAccountLinkedAccountsRequest,
    initOverrides?: RequestInit | runtime.InitOverrideFunction,
  ): Promise<runtime.ApiResponse<AppGetLinkedAccountsResponse>>;

  /**
   *
   * Get linked accounts
   */
  getUserAccountLinkedAccounts(
    requestParameters: GetUserAccountLinkedAccountsRequest,
    initOverrides?: RequestInit | runtime.InitOverrideFunction,
  ): Promise<AppGetLinkedAccountsResponse>;

  /**
   *
   * @summary Link new account
   * @param {number} userAccountId
   * @param {boolean} [validate]
   * @param {boolean} [persist]
   * @param {AppLinkAccountRequest} [appLinkAccountRequest]
   * @param {*} [options] Override http request option.
   * @throws {RequiredError}
   * @memberof LinkedAccountsApiInterface
   */
  linkNewAccountRaw(
    requestParameters: LinkNewAccountRequest,
    initOverrides?: RequestInit | runtime.InitOverrideFunction,
  ): Promise<runtime.ApiResponse<object>>;

  /**
   *
   * Link new account
   */
  linkNewAccount(
    requestParameters: LinkNewAccountRequest,
    initOverrides?: RequestInit | runtime.InitOverrideFunction,
  ): Promise<object>;

  /**
   *
   * @summary Update linked account credentials
   * @param {number} userAccountId
   * @param {number} linkedAccountId
   * @param {boolean} [validate]
   * @param {boolean} [persist]
   * @param {AppUpdateLinkedAccountCredentialsRequest} [appUpdateLinkedAccountCredentialsRequest]
   * @param {*} [options] Override http request option.
   * @throws {RequiredError}
   * @memberof LinkedAccountsApiInterface
   */
  updateLinkedAccountCredentialsRaw(
    requestParameters: UpdateLinkedAccountCredentialsRequest,
    initOverrides?: RequestInit | runtime.InitOverrideFunction,
  ): Promise<runtime.ApiResponse<object>>;

  /**
   *
   * Update linked account credentials
   */
  updateLinkedAccountCredentials(
    requestParameters: UpdateLinkedAccountCredentialsRequest,
    initOverrides?: RequestInit | runtime.InitOverrideFunction,
  ): Promise<object>;

  /**
   *
   * @summary Update linked account metadata
   * @param {number} userAccountId
   * @param {number} linkedAccountId
   * @param {AppUpdateLinkedAccountMetadataRequest} [appUpdateLinkedAccountMetadataRequest]
   * @param {*} [options] Override http request option.
   * @throws {RequiredError}
   * @memberof LinkedAccountsApiInterface
   */
  updateLinkedAccountMetadataRaw(
    requestParameters: UpdateLinkedAccountMetadataRequest,
    initOverrides?: RequestInit | runtime.InitOverrideFunction,
  ): Promise<runtime.ApiResponse<object>>;

  /**
   *
   * Update linked account metadata
   */
  updateLinkedAccountMetadata(
    requestParameters: UpdateLinkedAccountMetadataRequest,
    initOverrides?: RequestInit | runtime.InitOverrideFunction,
  ): Promise<object>;
}

/**
 *
 */
export class LinkedAccountsApi
  extends runtime.BaseAPI
  implements LinkedAccountsApiInterface
{
  /**
   *
   * Delete linked account
   */
  async deleteLinkedAccountRaw(
    requestParameters: DeleteLinkedAccountRequest,
    initOverrides?: RequestInit | runtime.InitOverrideFunction,
  ): Promise<runtime.ApiResponse<object>> {
    if (
      requestParameters.userAccountId === null ||
      requestParameters.userAccountId === undefined
    ) {
      throw new runtime.RequiredError(
        "userAccountId",
        "Required parameter requestParameters.userAccountId was null or undefined when calling deleteLinkedAccount.",
      );
    }

    if (
      requestParameters.linkedAccountId === null ||
      requestParameters.linkedAccountId === undefined
    ) {
      throw new runtime.RequiredError(
        "linkedAccountId",
        "Required parameter requestParameters.linkedAccountId was null or undefined when calling deleteLinkedAccount.",
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
        path: `/api/v1/accounts/{user_account_id}/linked_accounts/{linked_account_id}/`
          .replace(
            `{${"user_account_id"}}`,
            encodeURIComponent(String(requestParameters.userAccountId)),
          )
          .replace(
            `{${"linked_account_id"}}`,
            encodeURIComponent(String(requestParameters.linkedAccountId)),
          ),
        method: "DELETE",
        headers: headerParameters,
        query: queryParameters,
      },
      initOverrides,
    );

    return new runtime.JSONApiResponse<any>(response);
  }

  /**
   *
   * Delete linked account
   */
  async deleteLinkedAccount(
    requestParameters: DeleteLinkedAccountRequest,
    initOverrides?: RequestInit | runtime.InitOverrideFunction,
  ): Promise<object> {
    const response = await this.deleteLinkedAccountRaw(
      requestParameters,
      initOverrides,
    );
    return await response.value();
  }

  /**
   *
   * Get linked account
   */
  async getLinkedAccountRaw(
    requestParameters: GetLinkedAccountRequest,
    initOverrides?: RequestInit | runtime.InitOverrideFunction,
  ): Promise<runtime.ApiResponse<AppGetLinkedAccountResponse>> {
    if (
      requestParameters.userAccountId === null ||
      requestParameters.userAccountId === undefined
    ) {
      throw new runtime.RequiredError(
        "userAccountId",
        "Required parameter requestParameters.userAccountId was null or undefined when calling getLinkedAccount.",
      );
    }

    if (
      requestParameters.linkedAccountId === null ||
      requestParameters.linkedAccountId === undefined
    ) {
      throw new runtime.RequiredError(
        "linkedAccountId",
        "Required parameter requestParameters.linkedAccountId was null or undefined when calling getLinkedAccount.",
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
        path: `/api/v1/accounts/{user_account_id}/linked_accounts/{linked_account_id}/`
          .replace(
            `{${"user_account_id"}}`,
            encodeURIComponent(String(requestParameters.userAccountId)),
          )
          .replace(
            `{${"linked_account_id"}}`,
            encodeURIComponent(String(requestParameters.linkedAccountId)),
          ),
        method: "GET",
        headers: headerParameters,
        query: queryParameters,
      },
      initOverrides,
    );

    return new runtime.JSONApiResponse(response, (jsonValue) =>
      AppGetLinkedAccountResponseFromJSON(jsonValue),
    );
  }

  /**
   *
   * Get linked account
   */
  async getLinkedAccount(
    requestParameters: GetLinkedAccountRequest,
    initOverrides?: RequestInit | runtime.InitOverrideFunction,
  ): Promise<AppGetLinkedAccountResponse> {
    const response = await this.getLinkedAccountRaw(
      requestParameters,
      initOverrides,
    );
    return await response.value();
  }

  /**
   *
   * Get linked accounts
   */
  async getUserAccountLinkedAccountsRaw(
    requestParameters: GetUserAccountLinkedAccountsRequest,
    initOverrides?: RequestInit | runtime.InitOverrideFunction,
  ): Promise<runtime.ApiResponse<AppGetLinkedAccountsResponse>> {
    if (
      requestParameters.userAccountId === null ||
      requestParameters.userAccountId === undefined
    ) {
      throw new runtime.RequiredError(
        "userAccountId",
        "Required parameter requestParameters.userAccountId was null or undefined when calling getUserAccountLinkedAccounts.",
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
        path: `/api/v1/accounts/{user_account_id}/linked_accounts/`.replace(
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
      AppGetLinkedAccountsResponseFromJSON(jsonValue),
    );
  }

  /**
   *
   * Get linked accounts
   */
  async getUserAccountLinkedAccounts(
    requestParameters: GetUserAccountLinkedAccountsRequest,
    initOverrides?: RequestInit | runtime.InitOverrideFunction,
  ): Promise<AppGetLinkedAccountsResponse> {
    const response = await this.getUserAccountLinkedAccountsRaw(
      requestParameters,
      initOverrides,
    );
    return await response.value();
  }

  /**
   *
   * Link new account
   */
  async linkNewAccountRaw(
    requestParameters: LinkNewAccountRequest,
    initOverrides?: RequestInit | runtime.InitOverrideFunction,
  ): Promise<runtime.ApiResponse<object>> {
    if (
      requestParameters.userAccountId === null ||
      requestParameters.userAccountId === undefined
    ) {
      throw new runtime.RequiredError(
        "userAccountId",
        "Required parameter requestParameters.userAccountId was null or undefined when calling linkNewAccount.",
      );
    }

    const queryParameters: any = {};

    if (requestParameters.validate !== undefined) {
      queryParameters["validate"] = requestParameters.validate;
    }

    if (requestParameters.persist !== undefined) {
      queryParameters["persist"] = requestParameters.persist;
    }

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
        path: `/api/v1/accounts/{user_account_id}/linked_accounts/`.replace(
          `{${"user_account_id"}}`,
          encodeURIComponent(String(requestParameters.userAccountId)),
        ),
        method: "POST",
        headers: headerParameters,
        query: queryParameters,
        body: AppLinkAccountRequestToJSON(
          requestParameters.appLinkAccountRequest,
        ),
      },
      initOverrides,
    );

    return new runtime.JSONApiResponse<any>(response);
  }

  /**
   *
   * Link new account
   */
  async linkNewAccount(
    requestParameters: LinkNewAccountRequest,
    initOverrides?: RequestInit | runtime.InitOverrideFunction,
  ): Promise<object> {
    const response = await this.linkNewAccountRaw(
      requestParameters,
      initOverrides,
    );
    return await response.value();
  }

  /**
   *
   * Update linked account credentials
   */
  async updateLinkedAccountCredentialsRaw(
    requestParameters: UpdateLinkedAccountCredentialsRequest,
    initOverrides?: RequestInit | runtime.InitOverrideFunction,
  ): Promise<runtime.ApiResponse<object>> {
    if (
      requestParameters.userAccountId === null ||
      requestParameters.userAccountId === undefined
    ) {
      throw new runtime.RequiredError(
        "userAccountId",
        "Required parameter requestParameters.userAccountId was null or undefined when calling updateLinkedAccountCredentials.",
      );
    }

    if (
      requestParameters.linkedAccountId === null ||
      requestParameters.linkedAccountId === undefined
    ) {
      throw new runtime.RequiredError(
        "linkedAccountId",
        "Required parameter requestParameters.linkedAccountId was null or undefined when calling updateLinkedAccountCredentials.",
      );
    }

    const queryParameters: any = {};

    if (requestParameters.validate !== undefined) {
      queryParameters["validate"] = requestParameters.validate;
    }

    if (requestParameters.persist !== undefined) {
      queryParameters["persist"] = requestParameters.persist;
    }

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
        path: `/api/v1/accounts/{user_account_id}/linked_accounts/{linked_account_id}/credentials/`
          .replace(
            `{${"user_account_id"}}`,
            encodeURIComponent(String(requestParameters.userAccountId)),
          )
          .replace(
            `{${"linked_account_id"}}`,
            encodeURIComponent(String(requestParameters.linkedAccountId)),
          ),
        method: "PUT",
        headers: headerParameters,
        query: queryParameters,
        body: AppUpdateLinkedAccountCredentialsRequestToJSON(
          requestParameters.appUpdateLinkedAccountCredentialsRequest,
        ),
      },
      initOverrides,
    );

    return new runtime.JSONApiResponse<any>(response);
  }

  /**
   *
   * Update linked account credentials
   */
  async updateLinkedAccountCredentials(
    requestParameters: UpdateLinkedAccountCredentialsRequest,
    initOverrides?: RequestInit | runtime.InitOverrideFunction,
  ): Promise<object> {
    const response = await this.updateLinkedAccountCredentialsRaw(
      requestParameters,
      initOverrides,
    );
    return await response.value();
  }

  /**
   *
   * Update linked account metadata
   */
  async updateLinkedAccountMetadataRaw(
    requestParameters: UpdateLinkedAccountMetadataRequest,
    initOverrides?: RequestInit | runtime.InitOverrideFunction,
  ): Promise<runtime.ApiResponse<object>> {
    if (
      requestParameters.userAccountId === null ||
      requestParameters.userAccountId === undefined
    ) {
      throw new runtime.RequiredError(
        "userAccountId",
        "Required parameter requestParameters.userAccountId was null or undefined when calling updateLinkedAccountMetadata.",
      );
    }

    if (
      requestParameters.linkedAccountId === null ||
      requestParameters.linkedAccountId === undefined
    ) {
      throw new runtime.RequiredError(
        "linkedAccountId",
        "Required parameter requestParameters.linkedAccountId was null or undefined when calling updateLinkedAccountMetadata.",
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
        path: `/api/v1/accounts/{user_account_id}/linked_accounts/{linked_account_id}/metadata/`
          .replace(
            `{${"user_account_id"}}`,
            encodeURIComponent(String(requestParameters.userAccountId)),
          )
          .replace(
            `{${"linked_account_id"}}`,
            encodeURIComponent(String(requestParameters.linkedAccountId)),
          ),
        method: "PUT",
        headers: headerParameters,
        query: queryParameters,
        body: AppUpdateLinkedAccountMetadataRequestToJSON(
          requestParameters.appUpdateLinkedAccountMetadataRequest,
        ),
      },
      initOverrides,
    );

    return new runtime.JSONApiResponse<any>(response);
  }

  /**
   *
   * Update linked account metadata
   */
  async updateLinkedAccountMetadata(
    requestParameters: UpdateLinkedAccountMetadataRequest,
    initOverrides?: RequestInit | runtime.InitOverrideFunction,
  ): Promise<object> {
    const response = await this.updateLinkedAccountMetadataRaw(
      requestParameters,
      initOverrides,
    );
    return await response.value();
  }
}
