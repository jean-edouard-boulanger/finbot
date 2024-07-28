/* tslint:disable */
/* eslint-disable */
/**
 * Finbot application service
 * API documentation for appwsrv
 *
 *
 *
 * NOTE: This class is auto generated by OpenAPI Generator (https://openapi-generator.tech).
 * https://openapi-generator.tech
 * Do not edit the class manually.
 */

import * as runtime from "../runtime";
import type {
  AppCreateOrUpdateProviderRequest,
  AppCreateOrUpdateProviderResponse,
  AppGetPlaidSettingsResponse,
  AppGetProviderResponse,
  AppGetProvidersResponse,
  ValidationErrorElement,
} from "../models/index";
import {
  AppCreateOrUpdateProviderRequestFromJSON,
  AppCreateOrUpdateProviderRequestToJSON,
  AppCreateOrUpdateProviderResponseFromJSON,
  AppCreateOrUpdateProviderResponseToJSON,
  AppGetPlaidSettingsResponseFromJSON,
  AppGetPlaidSettingsResponseToJSON,
  AppGetProviderResponseFromJSON,
  AppGetProviderResponseToJSON,
  AppGetProvidersResponseFromJSON,
  AppGetProvidersResponseToJSON,
  ValidationErrorElementFromJSON,
  ValidationErrorElementToJSON,
} from "../models/index";

export interface DeleteFinancialDataProviderRequest {
  providerId: string;
}

export interface GetFinancialDataProviderRequest {
  providerId: string;
}

export interface UpdateOrCreateFinancialDataProviderRequest {
  appCreateOrUpdateProviderRequest?: AppCreateOrUpdateProviderRequest;
}

/**
 * FinancialDataProvidersApi - interface
 *
 * @export
 * @interface FinancialDataProvidersApiInterface
 */
export interface FinancialDataProvidersApiInterface {
  /**
   *
   * @summary Delete provider
   * @param {string} providerId
   * @param {*} [options] Override http request option.
   * @throws {RequiredError}
   * @memberof FinancialDataProvidersApiInterface
   */
  deleteFinancialDataProviderRaw(
    requestParameters: DeleteFinancialDataProviderRequest,
    initOverrides?: RequestInit | runtime.InitOverrideFunction,
  ): Promise<runtime.ApiResponse<object>>;

  /**
   *
   * Delete provider
   */
  deleteFinancialDataProvider(
    requestParameters: DeleteFinancialDataProviderRequest,
    initOverrides?: RequestInit | runtime.InitOverrideFunction,
  ): Promise<object>;

  /**
   *
   * @summary Get provider
   * @param {string} providerId
   * @param {*} [options] Override http request option.
   * @throws {RequiredError}
   * @memberof FinancialDataProvidersApiInterface
   */
  getFinancialDataProviderRaw(
    requestParameters: GetFinancialDataProviderRequest,
    initOverrides?: RequestInit | runtime.InitOverrideFunction,
  ): Promise<runtime.ApiResponse<AppGetProviderResponse>>;

  /**
   *
   * Get provider
   */
  getFinancialDataProvider(
    requestParameters: GetFinancialDataProviderRequest,
    initOverrides?: RequestInit | runtime.InitOverrideFunction,
  ): Promise<AppGetProviderResponse>;

  /**
   *
   * @summary Get providers
   * @param {*} [options] Override http request option.
   * @throws {RequiredError}
   * @memberof FinancialDataProvidersApiInterface
   */
  getFinancialDataProvidersRaw(
    initOverrides?: RequestInit | runtime.InitOverrideFunction,
  ): Promise<runtime.ApiResponse<AppGetProvidersResponse>>;

  /**
   *
   * Get providers
   */
  getFinancialDataProviders(
    initOverrides?: RequestInit | runtime.InitOverrideFunction,
  ): Promise<AppGetProvidersResponse>;

  /**
   *
   * @summary Get plaid settings
   * @param {*} [options] Override http request option.
   * @throws {RequiredError}
   * @memberof FinancialDataProvidersApiInterface
   */
  getPlaidSettingsRaw(
    initOverrides?: RequestInit | runtime.InitOverrideFunction,
  ): Promise<runtime.ApiResponse<AppGetPlaidSettingsResponse>>;

  /**
   *
   * Get plaid settings
   */
  getPlaidSettings(
    initOverrides?: RequestInit | runtime.InitOverrideFunction,
  ): Promise<AppGetPlaidSettingsResponse>;

  /**
   *
   * @summary Update or create provider
   * @param {AppCreateOrUpdateProviderRequest} [appCreateOrUpdateProviderRequest]
   * @param {*} [options] Override http request option.
   * @throws {RequiredError}
   * @memberof FinancialDataProvidersApiInterface
   */
  updateOrCreateFinancialDataProviderRaw(
    requestParameters: UpdateOrCreateFinancialDataProviderRequest,
    initOverrides?: RequestInit | runtime.InitOverrideFunction,
  ): Promise<runtime.ApiResponse<AppCreateOrUpdateProviderResponse>>;

  /**
   *
   * Update or create provider
   */
  updateOrCreateFinancialDataProvider(
    requestParameters: UpdateOrCreateFinancialDataProviderRequest,
    initOverrides?: RequestInit | runtime.InitOverrideFunction,
  ): Promise<AppCreateOrUpdateProviderResponse>;
}

/**
 *
 */
export class FinancialDataProvidersApi
  extends runtime.BaseAPI
  implements FinancialDataProvidersApiInterface
{
  /**
   *
   * Delete provider
   */
  async deleteFinancialDataProviderRaw(
    requestParameters: DeleteFinancialDataProviderRequest,
    initOverrides?: RequestInit | runtime.InitOverrideFunction,
  ): Promise<runtime.ApiResponse<object>> {
    if (requestParameters["providerId"] == null) {
      throw new runtime.RequiredError(
        "providerId",
        'Required parameter "providerId" was null or undefined when calling deleteFinancialDataProvider().',
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
        path: `/api/v1/providers/{provider_id}/`.replace(
          `{${"provider_id"}}`,
          encodeURIComponent(String(requestParameters["providerId"])),
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
   * Delete provider
   */
  async deleteFinancialDataProvider(
    requestParameters: DeleteFinancialDataProviderRequest,
    initOverrides?: RequestInit | runtime.InitOverrideFunction,
  ): Promise<object> {
    const response = await this.deleteFinancialDataProviderRaw(
      requestParameters,
      initOverrides,
    );
    return await response.value();
  }

  /**
   *
   * Get provider
   */
  async getFinancialDataProviderRaw(
    requestParameters: GetFinancialDataProviderRequest,
    initOverrides?: RequestInit | runtime.InitOverrideFunction,
  ): Promise<runtime.ApiResponse<AppGetProviderResponse>> {
    if (requestParameters["providerId"] == null) {
      throw new runtime.RequiredError(
        "providerId",
        'Required parameter "providerId" was null or undefined when calling getFinancialDataProvider().',
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
        path: `/api/v1/providers/{provider_id}/`.replace(
          `{${"provider_id"}}`,
          encodeURIComponent(String(requestParameters["providerId"])),
        ),
        method: "GET",
        headers: headerParameters,
        query: queryParameters,
      },
      initOverrides,
    );

    return new runtime.JSONApiResponse(response, (jsonValue) =>
      AppGetProviderResponseFromJSON(jsonValue),
    );
  }

  /**
   *
   * Get provider
   */
  async getFinancialDataProvider(
    requestParameters: GetFinancialDataProviderRequest,
    initOverrides?: RequestInit | runtime.InitOverrideFunction,
  ): Promise<AppGetProviderResponse> {
    const response = await this.getFinancialDataProviderRaw(
      requestParameters,
      initOverrides,
    );
    return await response.value();
  }

  /**
   *
   * Get providers
   */
  async getFinancialDataProvidersRaw(
    initOverrides?: RequestInit | runtime.InitOverrideFunction,
  ): Promise<runtime.ApiResponse<AppGetProvidersResponse>> {
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
        path: `/api/v1/providers/`,
        method: "GET",
        headers: headerParameters,
        query: queryParameters,
      },
      initOverrides,
    );

    return new runtime.JSONApiResponse(response, (jsonValue) =>
      AppGetProvidersResponseFromJSON(jsonValue),
    );
  }

  /**
   *
   * Get providers
   */
  async getFinancialDataProviders(
    initOverrides?: RequestInit | runtime.InitOverrideFunction,
  ): Promise<AppGetProvidersResponse> {
    const response = await this.getFinancialDataProvidersRaw(initOverrides);
    return await response.value();
  }

  /**
   *
   * Get plaid settings
   */
  async getPlaidSettingsRaw(
    initOverrides?: RequestInit | runtime.InitOverrideFunction,
  ): Promise<runtime.ApiResponse<AppGetPlaidSettingsResponse>> {
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
        path: `/api/v1/providers/plaid/settings/`,
        method: "GET",
        headers: headerParameters,
        query: queryParameters,
      },
      initOverrides,
    );

    return new runtime.JSONApiResponse(response, (jsonValue) =>
      AppGetPlaidSettingsResponseFromJSON(jsonValue),
    );
  }

  /**
   *
   * Get plaid settings
   */
  async getPlaidSettings(
    initOverrides?: RequestInit | runtime.InitOverrideFunction,
  ): Promise<AppGetPlaidSettingsResponse> {
    const response = await this.getPlaidSettingsRaw(initOverrides);
    return await response.value();
  }

  /**
   *
   * Update or create provider
   */
  async updateOrCreateFinancialDataProviderRaw(
    requestParameters: UpdateOrCreateFinancialDataProviderRequest,
    initOverrides?: RequestInit | runtime.InitOverrideFunction,
  ): Promise<runtime.ApiResponse<AppCreateOrUpdateProviderResponse>> {
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
        path: `/api/v1/providers/`,
        method: "PUT",
        headers: headerParameters,
        query: queryParameters,
        body: AppCreateOrUpdateProviderRequestToJSON(
          requestParameters["appCreateOrUpdateProviderRequest"],
        ),
      },
      initOverrides,
    );

    return new runtime.JSONApiResponse(response, (jsonValue) =>
      AppCreateOrUpdateProviderResponseFromJSON(jsonValue),
    );
  }

  /**
   *
   * Update or create provider
   */
  async updateOrCreateFinancialDataProvider(
    requestParameters: UpdateOrCreateFinancialDataProviderRequest = {},
    initOverrides?: RequestInit | runtime.InitOverrideFunction,
  ): Promise<AppCreateOrUpdateProviderResponse> {
    const response = await this.updateOrCreateFinancialDataProviderRaw(
      requestParameters,
      initOverrides,
    );
    return await response.value();
  }
}
