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
  AppEmailDeliverySettings,
  AppGetEmailDeliveryProvidersResponse,
  AppGetEmailDeliverySettingsResponse,
  ValidationErrorElement,
} from "../models/index";
import {
  AppEmailDeliverySettingsFromJSON,
  AppEmailDeliverySettingsToJSON,
  AppGetEmailDeliveryProvidersResponseFromJSON,
  AppGetEmailDeliveryProvidersResponseToJSON,
  AppGetEmailDeliverySettingsResponseFromJSON,
  AppGetEmailDeliverySettingsResponseToJSON,
  ValidationErrorElementFromJSON,
  ValidationErrorElementToJSON,
} from "../models/index";

export interface SetEmailDeliverySettingsRequest {
  validate?: boolean;
  appEmailDeliverySettings?: AppEmailDeliverySettings;
}

/**
 * AdministrationApi - interface
 *
 * @export
 * @interface AdministrationApiInterface
 */
export interface AdministrationApiInterface {
  /**
   *
   * @summary Get email delivery providers
   * @param {*} [options] Override http request option.
   * @throws {RequiredError}
   * @memberof AdministrationApiInterface
   */
  getEmailDeliveryProvidersRaw(
    initOverrides?: RequestInit | runtime.InitOverrideFunction,
  ): Promise<runtime.ApiResponse<AppGetEmailDeliveryProvidersResponse>>;

  /**
   *
   * Get email delivery providers
   */
  getEmailDeliveryProviders(
    initOverrides?: RequestInit | runtime.InitOverrideFunction,
  ): Promise<AppGetEmailDeliveryProvidersResponse>;

  /**
   *
   * @summary Get email delivery settings
   * @param {*} [options] Override http request option.
   * @throws {RequiredError}
   * @memberof AdministrationApiInterface
   */
  getEmailDeliverySettingsRaw(
    initOverrides?: RequestInit | runtime.InitOverrideFunction,
  ): Promise<runtime.ApiResponse<AppGetEmailDeliverySettingsResponse>>;

  /**
   *
   * Get email delivery settings
   */
  getEmailDeliverySettings(
    initOverrides?: RequestInit | runtime.InitOverrideFunction,
  ): Promise<AppGetEmailDeliverySettingsResponse>;

  /**
   *
   * @summary remove_email_delivery_settings <DELETE>
   * @param {*} [options] Override http request option.
   * @throws {RequiredError}
   * @memberof AdministrationApiInterface
   */
  removeEmailDeliverySettingsRaw(
    initOverrides?: RequestInit | runtime.InitOverrideFunction,
  ): Promise<runtime.ApiResponse<object>>;

  /**
   *
   * remove_email_delivery_settings <DELETE>
   */
  removeEmailDeliverySettings(
    initOverrides?: RequestInit | runtime.InitOverrideFunction,
  ): Promise<object>;

  /**
   *
   * @summary set_email_delivery_settings <PUT>
   * @param {boolean} [validate]
   * @param {AppEmailDeliverySettings} [appEmailDeliverySettings]
   * @param {*} [options] Override http request option.
   * @throws {RequiredError}
   * @memberof AdministrationApiInterface
   */
  setEmailDeliverySettingsRaw(
    requestParameters: SetEmailDeliverySettingsRequest,
    initOverrides?: RequestInit | runtime.InitOverrideFunction,
  ): Promise<runtime.ApiResponse<object>>;

  /**
   *
   * set_email_delivery_settings <PUT>
   */
  setEmailDeliverySettings(
    requestParameters: SetEmailDeliverySettingsRequest,
    initOverrides?: RequestInit | runtime.InitOverrideFunction,
  ): Promise<object>;
}

/**
 *
 */
export class AdministrationApi
  extends runtime.BaseAPI
  implements AdministrationApiInterface
{
  /**
   *
   * Get email delivery providers
   */
  async getEmailDeliveryProvidersRaw(
    initOverrides?: RequestInit | runtime.InitOverrideFunction,
  ): Promise<runtime.ApiResponse<AppGetEmailDeliveryProvidersResponse>> {
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
        path: `/api/v1/admin/settings/email_delivery/providers/`,
        method: "GET",
        headers: headerParameters,
        query: queryParameters,
      },
      initOverrides,
    );

    return new runtime.JSONApiResponse(response, (jsonValue) =>
      AppGetEmailDeliveryProvidersResponseFromJSON(jsonValue),
    );
  }

  /**
   *
   * Get email delivery providers
   */
  async getEmailDeliveryProviders(
    initOverrides?: RequestInit | runtime.InitOverrideFunction,
  ): Promise<AppGetEmailDeliveryProvidersResponse> {
    const response = await this.getEmailDeliveryProvidersRaw(initOverrides);
    return await response.value();
  }

  /**
   *
   * Get email delivery settings
   */
  async getEmailDeliverySettingsRaw(
    initOverrides?: RequestInit | runtime.InitOverrideFunction,
  ): Promise<runtime.ApiResponse<AppGetEmailDeliverySettingsResponse>> {
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
        path: `/api/v1/admin/settings/email_delivery/`,
        method: "GET",
        headers: headerParameters,
        query: queryParameters,
      },
      initOverrides,
    );

    return new runtime.JSONApiResponse(response, (jsonValue) =>
      AppGetEmailDeliverySettingsResponseFromJSON(jsonValue),
    );
  }

  /**
   *
   * Get email delivery settings
   */
  async getEmailDeliverySettings(
    initOverrides?: RequestInit | runtime.InitOverrideFunction,
  ): Promise<AppGetEmailDeliverySettingsResponse> {
    const response = await this.getEmailDeliverySettingsRaw(initOverrides);
    return await response.value();
  }

  /**
   *
   * remove_email_delivery_settings <DELETE>
   */
  async removeEmailDeliverySettingsRaw(
    initOverrides?: RequestInit | runtime.InitOverrideFunction,
  ): Promise<runtime.ApiResponse<object>> {
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
        path: `/api/v1/admin/settings/email_delivery/`,
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
   * remove_email_delivery_settings <DELETE>
   */
  async removeEmailDeliverySettings(
    initOverrides?: RequestInit | runtime.InitOverrideFunction,
  ): Promise<object> {
    const response = await this.removeEmailDeliverySettingsRaw(initOverrides);
    return await response.value();
  }

  /**
   *
   * set_email_delivery_settings <PUT>
   */
  async setEmailDeliverySettingsRaw(
    requestParameters: SetEmailDeliverySettingsRequest,
    initOverrides?: RequestInit | runtime.InitOverrideFunction,
  ): Promise<runtime.ApiResponse<object>> {
    const queryParameters: any = {};

    if (requestParameters["validate"] != null) {
      queryParameters["validate"] = requestParameters["validate"];
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
        path: `/api/v1/admin/settings/email_delivery/`,
        method: "PUT",
        headers: headerParameters,
        query: queryParameters,
        body: AppEmailDeliverySettingsToJSON(
          requestParameters["appEmailDeliverySettings"],
        ),
      },
      initOverrides,
    );

    return new runtime.JSONApiResponse<any>(response);
  }

  /**
   *
   * set_email_delivery_settings <PUT>
   */
  async setEmailDeliverySettings(
    requestParameters: SetEmailDeliverySettingsRequest = {},
    initOverrides?: RequestInit | runtime.InitOverrideFunction,
  ): Promise<object> {
    const response = await this.setEmailDeliverySettingsRaw(
      requestParameters,
      initOverrides,
    );
    return await response.value();
  }
}
