/* tslint:disable */
/* eslint-disable */
/**
 * Finbot application service
 * API documentation for appwsrv
 *
 * The version of the OpenAPI document: v0.0.4
 *
 *
 * NOTE: This class is auto generated by OpenAPI Generator (https://openapi-generator.tech).
 * https://openapi-generator.tech
 * Do not edit the class manually.
 */

import * as runtime from "../runtime";
import type {
  AppGetUserAccountValuationByAssetClassResponse,
  AppGetUserAccountValuationByAssetTypeResponse,
  AppGetUserAccountValuationByCurrencyExposureResponse,
  AppGetUserAccountValuationHistoryByAssetClassResponse,
  AppGetUserAccountValuationHistoryByAssetTypeResponse,
  AppGetUserAccountValuationHistoryResponse,
  AppGetUserAccountValuationResponse,
  ValidationErrorElement,
  ValuationFrequency,
} from "../models/index";
import {
  AppGetUserAccountValuationByAssetClassResponseFromJSON,
  AppGetUserAccountValuationByAssetClassResponseToJSON,
  AppGetUserAccountValuationByAssetTypeResponseFromJSON,
  AppGetUserAccountValuationByAssetTypeResponseToJSON,
  AppGetUserAccountValuationByCurrencyExposureResponseFromJSON,
  AppGetUserAccountValuationByCurrencyExposureResponseToJSON,
  AppGetUserAccountValuationHistoryByAssetClassResponseFromJSON,
  AppGetUserAccountValuationHistoryByAssetClassResponseToJSON,
  AppGetUserAccountValuationHistoryByAssetTypeResponseFromJSON,
  AppGetUserAccountValuationHistoryByAssetTypeResponseToJSON,
  AppGetUserAccountValuationHistoryResponseFromJSON,
  AppGetUserAccountValuationHistoryResponseToJSON,
  AppGetUserAccountValuationResponseFromJSON,
  AppGetUserAccountValuationResponseToJSON,
  ValidationErrorElementFromJSON,
  ValidationErrorElementToJSON,
  ValuationFrequencyFromJSON,
  ValuationFrequencyToJSON,
} from "../models/index";

export interface GetUserAccountHistoricalValuationRequest {
  userAccountId: number;
  fromTime?: Date;
  toTime?: Date;
  frequency?: ValuationFrequency;
}

export interface GetUserAccountHistoricalValuationByAssetClassRequest {
  userAccountId: number;
  fromTime?: Date;
  toTime?: Date;
  frequency?: ValuationFrequency;
}

export interface GetUserAccountHistoricalValuationByAssetTypeRequest {
  userAccountId: number;
  fromTime?: Date;
  toTime?: Date;
  frequency?: ValuationFrequency;
}

export interface GetUserAccountValuationRequest {
  userAccountId: number;
}

export interface GetUserAccountValuationByAssetClassRequest {
  userAccountId: number;
}

export interface GetUserAccountValuationByAssetTypeRequest {
  userAccountId: number;
}

export interface GetUserAccountValuationByCurrencyExposureRequest {
  userAccountId: number;
}

export interface TriggerUserAccountValuationRequest {
  userAccountId: number;
}

/**
 * UserAccountsValuationApi - interface
 *
 * @export
 * @interface UserAccountsValuationApiInterface
 */
export interface UserAccountsValuationApiInterface {
  /**
   *
   * @summary Get user account valuation historical valuation
   * @param {number} userAccountId
   * @param {Date} [fromTime]
   * @param {Date} [toTime]
   * @param {ValuationFrequency} [frequency]
   * @param {*} [options] Override http request option.
   * @throws {RequiredError}
   * @memberof UserAccountsValuationApiInterface
   */
  getUserAccountHistoricalValuationRaw(
    requestParameters: GetUserAccountHistoricalValuationRequest,
    initOverrides?: RequestInit | runtime.InitOverrideFunction,
  ): Promise<runtime.ApiResponse<AppGetUserAccountValuationHistoryResponse>>;

  /**
   *
   * Get user account valuation historical valuation
   */
  getUserAccountHistoricalValuation(
    requestParameters: GetUserAccountHistoricalValuationRequest,
    initOverrides?: RequestInit | runtime.InitOverrideFunction,
  ): Promise<AppGetUserAccountValuationHistoryResponse>;

  /**
   *
   * @summary Get user account valuation historical valuation by asset class
   * @param {number} userAccountId
   * @param {Date} [fromTime]
   * @param {Date} [toTime]
   * @param {ValuationFrequency} [frequency]
   * @param {*} [options] Override http request option.
   * @throws {RequiredError}
   * @memberof UserAccountsValuationApiInterface
   */
  getUserAccountHistoricalValuationByAssetClassRaw(
    requestParameters: GetUserAccountHistoricalValuationByAssetClassRequest,
    initOverrides?: RequestInit | runtime.InitOverrideFunction,
  ): Promise<
    runtime.ApiResponse<AppGetUserAccountValuationHistoryByAssetClassResponse>
  >;

  /**
   *
   * Get user account valuation historical valuation by asset class
   */
  getUserAccountHistoricalValuationByAssetClass(
    requestParameters: GetUserAccountHistoricalValuationByAssetClassRequest,
    initOverrides?: RequestInit | runtime.InitOverrideFunction,
  ): Promise<AppGetUserAccountValuationHistoryByAssetClassResponse>;

  /**
   *
   * @summary Get user account valuation historical valuation by asset type
   * @param {number} userAccountId
   * @param {Date} [fromTime]
   * @param {Date} [toTime]
   * @param {ValuationFrequency} [frequency]
   * @param {*} [options] Override http request option.
   * @throws {RequiredError}
   * @memberof UserAccountsValuationApiInterface
   */
  getUserAccountHistoricalValuationByAssetTypeRaw(
    requestParameters: GetUserAccountHistoricalValuationByAssetTypeRequest,
    initOverrides?: RequestInit | runtime.InitOverrideFunction,
  ): Promise<
    runtime.ApiResponse<AppGetUserAccountValuationHistoryByAssetTypeResponse>
  >;

  /**
   *
   * Get user account valuation historical valuation by asset type
   */
  getUserAccountHistoricalValuationByAssetType(
    requestParameters: GetUserAccountHistoricalValuationByAssetTypeRequest,
    initOverrides?: RequestInit | runtime.InitOverrideFunction,
  ): Promise<AppGetUserAccountValuationHistoryByAssetTypeResponse>;

  /**
   *
   * @summary Get user account valuation
   * @param {number} userAccountId
   * @param {*} [options] Override http request option.
   * @throws {RequiredError}
   * @memberof UserAccountsValuationApiInterface
   */
  getUserAccountValuationRaw(
    requestParameters: GetUserAccountValuationRequest,
    initOverrides?: RequestInit | runtime.InitOverrideFunction,
  ): Promise<runtime.ApiResponse<AppGetUserAccountValuationResponse>>;

  /**
   *
   * Get user account valuation
   */
  getUserAccountValuation(
    requestParameters: GetUserAccountValuationRequest,
    initOverrides?: RequestInit | runtime.InitOverrideFunction,
  ): Promise<AppGetUserAccountValuationResponse>;

  /**
   *
   * @summary Get user account valuation by asset class
   * @param {number} userAccountId
   * @param {*} [options] Override http request option.
   * @throws {RequiredError}
   * @memberof UserAccountsValuationApiInterface
   */
  getUserAccountValuationByAssetClassRaw(
    requestParameters: GetUserAccountValuationByAssetClassRequest,
    initOverrides?: RequestInit | runtime.InitOverrideFunction,
  ): Promise<
    runtime.ApiResponse<AppGetUserAccountValuationByAssetClassResponse>
  >;

  /**
   *
   * Get user account valuation by asset class
   */
  getUserAccountValuationByAssetClass(
    requestParameters: GetUserAccountValuationByAssetClassRequest,
    initOverrides?: RequestInit | runtime.InitOverrideFunction,
  ): Promise<AppGetUserAccountValuationByAssetClassResponse>;

  /**
   *
   * @summary Get user account valuation by asset type
   * @param {number} userAccountId
   * @param {*} [options] Override http request option.
   * @throws {RequiredError}
   * @memberof UserAccountsValuationApiInterface
   */
  getUserAccountValuationByAssetTypeRaw(
    requestParameters: GetUserAccountValuationByAssetTypeRequest,
    initOverrides?: RequestInit | runtime.InitOverrideFunction,
  ): Promise<
    runtime.ApiResponse<AppGetUserAccountValuationByAssetTypeResponse>
  >;

  /**
   *
   * Get user account valuation by asset type
   */
  getUserAccountValuationByAssetType(
    requestParameters: GetUserAccountValuationByAssetTypeRequest,
    initOverrides?: RequestInit | runtime.InitOverrideFunction,
  ): Promise<AppGetUserAccountValuationByAssetTypeResponse>;

  /**
   *
   * @summary Get user account valuation by currency exposure
   * @param {number} userAccountId
   * @param {*} [options] Override http request option.
   * @throws {RequiredError}
   * @memberof UserAccountsValuationApiInterface
   */
  getUserAccountValuationByCurrencyExposureRaw(
    requestParameters: GetUserAccountValuationByCurrencyExposureRequest,
    initOverrides?: RequestInit | runtime.InitOverrideFunction,
  ): Promise<
    runtime.ApiResponse<AppGetUserAccountValuationByCurrencyExposureResponse>
  >;

  /**
   *
   * Get user account valuation by currency exposure
   */
  getUserAccountValuationByCurrencyExposure(
    requestParameters: GetUserAccountValuationByCurrencyExposureRequest,
    initOverrides?: RequestInit | runtime.InitOverrideFunction,
  ): Promise<AppGetUserAccountValuationByCurrencyExposureResponse>;

  /**
   *
   * @summary Trigger user account valuation
   * @param {number} userAccountId
   * @param {*} [options] Override http request option.
   * @throws {RequiredError}
   * @memberof UserAccountsValuationApiInterface
   */
  triggerUserAccountValuationRaw(
    requestParameters: TriggerUserAccountValuationRequest,
    initOverrides?: RequestInit | runtime.InitOverrideFunction,
  ): Promise<runtime.ApiResponse<object>>;

  /**
   *
   * Trigger user account valuation
   */
  triggerUserAccountValuation(
    requestParameters: TriggerUserAccountValuationRequest,
    initOverrides?: RequestInit | runtime.InitOverrideFunction,
  ): Promise<object>;
}

/**
 *
 */
export class UserAccountsValuationApi
  extends runtime.BaseAPI
  implements UserAccountsValuationApiInterface
{
  /**
   *
   * Get user account valuation historical valuation
   */
  async getUserAccountHistoricalValuationRaw(
    requestParameters: GetUserAccountHistoricalValuationRequest,
    initOverrides?: RequestInit | runtime.InitOverrideFunction,
  ): Promise<runtime.ApiResponse<AppGetUserAccountValuationHistoryResponse>> {
    if (
      requestParameters.userAccountId === null ||
      requestParameters.userAccountId === undefined
    ) {
      throw new runtime.RequiredError(
        "userAccountId",
        "Required parameter requestParameters.userAccountId was null or undefined when calling getUserAccountHistoricalValuation.",
      );
    }

    const queryParameters: any = {};

    if (requestParameters.fromTime !== undefined) {
      queryParameters["from_time"] = (
        requestParameters.fromTime as any
      ).toISOString();
    }

    if (requestParameters.toTime !== undefined) {
      queryParameters["to_time"] = (
        requestParameters.toTime as any
      ).toISOString();
    }

    if (requestParameters.frequency !== undefined) {
      queryParameters["frequency"] = requestParameters.frequency;
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
        path: `/api/v1/accounts/{user_account_id}/valuation/history/`.replace(
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
      AppGetUserAccountValuationHistoryResponseFromJSON(jsonValue),
    );
  }

  /**
   *
   * Get user account valuation historical valuation
   */
  async getUserAccountHistoricalValuation(
    requestParameters: GetUserAccountHistoricalValuationRequest,
    initOverrides?: RequestInit | runtime.InitOverrideFunction,
  ): Promise<AppGetUserAccountValuationHistoryResponse> {
    const response = await this.getUserAccountHistoricalValuationRaw(
      requestParameters,
      initOverrides,
    );
    return await response.value();
  }

  /**
   *
   * Get user account valuation historical valuation by asset class
   */
  async getUserAccountHistoricalValuationByAssetClassRaw(
    requestParameters: GetUserAccountHistoricalValuationByAssetClassRequest,
    initOverrides?: RequestInit | runtime.InitOverrideFunction,
  ): Promise<
    runtime.ApiResponse<AppGetUserAccountValuationHistoryByAssetClassResponse>
  > {
    if (
      requestParameters.userAccountId === null ||
      requestParameters.userAccountId === undefined
    ) {
      throw new runtime.RequiredError(
        "userAccountId",
        "Required parameter requestParameters.userAccountId was null or undefined when calling getUserAccountHistoricalValuationByAssetClass.",
      );
    }

    const queryParameters: any = {};

    if (requestParameters.fromTime !== undefined) {
      queryParameters["from_time"] = (
        requestParameters.fromTime as any
      ).toISOString();
    }

    if (requestParameters.toTime !== undefined) {
      queryParameters["to_time"] = (
        requestParameters.toTime as any
      ).toISOString();
    }

    if (requestParameters.frequency !== undefined) {
      queryParameters["frequency"] = requestParameters.frequency;
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
        path: `/api/v1/accounts/{user_account_id}/valuation/history/by/asset_class/`.replace(
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
      AppGetUserAccountValuationHistoryByAssetClassResponseFromJSON(jsonValue),
    );
  }

  /**
   *
   * Get user account valuation historical valuation by asset class
   */
  async getUserAccountHistoricalValuationByAssetClass(
    requestParameters: GetUserAccountHistoricalValuationByAssetClassRequest,
    initOverrides?: RequestInit | runtime.InitOverrideFunction,
  ): Promise<AppGetUserAccountValuationHistoryByAssetClassResponse> {
    const response =
      await this.getUserAccountHistoricalValuationByAssetClassRaw(
        requestParameters,
        initOverrides,
      );
    return await response.value();
  }

  /**
   *
   * Get user account valuation historical valuation by asset type
   */
  async getUserAccountHistoricalValuationByAssetTypeRaw(
    requestParameters: GetUserAccountHistoricalValuationByAssetTypeRequest,
    initOverrides?: RequestInit | runtime.InitOverrideFunction,
  ): Promise<
    runtime.ApiResponse<AppGetUserAccountValuationHistoryByAssetTypeResponse>
  > {
    if (
      requestParameters.userAccountId === null ||
      requestParameters.userAccountId === undefined
    ) {
      throw new runtime.RequiredError(
        "userAccountId",
        "Required parameter requestParameters.userAccountId was null or undefined when calling getUserAccountHistoricalValuationByAssetType.",
      );
    }

    const queryParameters: any = {};

    if (requestParameters.fromTime !== undefined) {
      queryParameters["from_time"] = (
        requestParameters.fromTime as any
      ).toISOString();
    }

    if (requestParameters.toTime !== undefined) {
      queryParameters["to_time"] = (
        requestParameters.toTime as any
      ).toISOString();
    }

    if (requestParameters.frequency !== undefined) {
      queryParameters["frequency"] = requestParameters.frequency;
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
        path: `/api/v1/accounts/{user_account_id}/valuation/history/by/asset_type/`.replace(
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
      AppGetUserAccountValuationHistoryByAssetTypeResponseFromJSON(jsonValue),
    );
  }

  /**
   *
   * Get user account valuation historical valuation by asset type
   */
  async getUserAccountHistoricalValuationByAssetType(
    requestParameters: GetUserAccountHistoricalValuationByAssetTypeRequest,
    initOverrides?: RequestInit | runtime.InitOverrideFunction,
  ): Promise<AppGetUserAccountValuationHistoryByAssetTypeResponse> {
    const response = await this.getUserAccountHistoricalValuationByAssetTypeRaw(
      requestParameters,
      initOverrides,
    );
    return await response.value();
  }

  /**
   *
   * Get user account valuation
   */
  async getUserAccountValuationRaw(
    requestParameters: GetUserAccountValuationRequest,
    initOverrides?: RequestInit | runtime.InitOverrideFunction,
  ): Promise<runtime.ApiResponse<AppGetUserAccountValuationResponse>> {
    if (
      requestParameters.userAccountId === null ||
      requestParameters.userAccountId === undefined
    ) {
      throw new runtime.RequiredError(
        "userAccountId",
        "Required parameter requestParameters.userAccountId was null or undefined when calling getUserAccountValuation.",
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
        path: `/api/v1/accounts/{user_account_id}/valuation/`.replace(
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
      AppGetUserAccountValuationResponseFromJSON(jsonValue),
    );
  }

  /**
   *
   * Get user account valuation
   */
  async getUserAccountValuation(
    requestParameters: GetUserAccountValuationRequest,
    initOverrides?: RequestInit | runtime.InitOverrideFunction,
  ): Promise<AppGetUserAccountValuationResponse> {
    const response = await this.getUserAccountValuationRaw(
      requestParameters,
      initOverrides,
    );
    return await response.value();
  }

  /**
   *
   * Get user account valuation by asset class
   */
  async getUserAccountValuationByAssetClassRaw(
    requestParameters: GetUserAccountValuationByAssetClassRequest,
    initOverrides?: RequestInit | runtime.InitOverrideFunction,
  ): Promise<
    runtime.ApiResponse<AppGetUserAccountValuationByAssetClassResponse>
  > {
    if (
      requestParameters.userAccountId === null ||
      requestParameters.userAccountId === undefined
    ) {
      throw new runtime.RequiredError(
        "userAccountId",
        "Required parameter requestParameters.userAccountId was null or undefined when calling getUserAccountValuationByAssetClass.",
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
        path: `/api/v1/accounts/{user_account_id}/valuation/by/asset_class/`.replace(
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
      AppGetUserAccountValuationByAssetClassResponseFromJSON(jsonValue),
    );
  }

  /**
   *
   * Get user account valuation by asset class
   */
  async getUserAccountValuationByAssetClass(
    requestParameters: GetUserAccountValuationByAssetClassRequest,
    initOverrides?: RequestInit | runtime.InitOverrideFunction,
  ): Promise<AppGetUserAccountValuationByAssetClassResponse> {
    const response = await this.getUserAccountValuationByAssetClassRaw(
      requestParameters,
      initOverrides,
    );
    return await response.value();
  }

  /**
   *
   * Get user account valuation by asset type
   */
  async getUserAccountValuationByAssetTypeRaw(
    requestParameters: GetUserAccountValuationByAssetTypeRequest,
    initOverrides?: RequestInit | runtime.InitOverrideFunction,
  ): Promise<
    runtime.ApiResponse<AppGetUserAccountValuationByAssetTypeResponse>
  > {
    if (
      requestParameters.userAccountId === null ||
      requestParameters.userAccountId === undefined
    ) {
      throw new runtime.RequiredError(
        "userAccountId",
        "Required parameter requestParameters.userAccountId was null or undefined when calling getUserAccountValuationByAssetType.",
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
        path: `/api/v1/accounts/{user_account_id}/valuation/by/asset_type/`.replace(
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
      AppGetUserAccountValuationByAssetTypeResponseFromJSON(jsonValue),
    );
  }

  /**
   *
   * Get user account valuation by asset type
   */
  async getUserAccountValuationByAssetType(
    requestParameters: GetUserAccountValuationByAssetTypeRequest,
    initOverrides?: RequestInit | runtime.InitOverrideFunction,
  ): Promise<AppGetUserAccountValuationByAssetTypeResponse> {
    const response = await this.getUserAccountValuationByAssetTypeRaw(
      requestParameters,
      initOverrides,
    );
    return await response.value();
  }

  /**
   *
   * Get user account valuation by currency exposure
   */
  async getUserAccountValuationByCurrencyExposureRaw(
    requestParameters: GetUserAccountValuationByCurrencyExposureRequest,
    initOverrides?: RequestInit | runtime.InitOverrideFunction,
  ): Promise<
    runtime.ApiResponse<AppGetUserAccountValuationByCurrencyExposureResponse>
  > {
    if (
      requestParameters.userAccountId === null ||
      requestParameters.userAccountId === undefined
    ) {
      throw new runtime.RequiredError(
        "userAccountId",
        "Required parameter requestParameters.userAccountId was null or undefined when calling getUserAccountValuationByCurrencyExposure.",
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
        path: `/api/v1/accounts/{user_account_id}/valuation/by/currency_exposure/`.replace(
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
      AppGetUserAccountValuationByCurrencyExposureResponseFromJSON(jsonValue),
    );
  }

  /**
   *
   * Get user account valuation by currency exposure
   */
  async getUserAccountValuationByCurrencyExposure(
    requestParameters: GetUserAccountValuationByCurrencyExposureRequest,
    initOverrides?: RequestInit | runtime.InitOverrideFunction,
  ): Promise<AppGetUserAccountValuationByCurrencyExposureResponse> {
    const response = await this.getUserAccountValuationByCurrencyExposureRaw(
      requestParameters,
      initOverrides,
    );
    return await response.value();
  }

  /**
   *
   * Trigger user account valuation
   */
  async triggerUserAccountValuationRaw(
    requestParameters: TriggerUserAccountValuationRequest,
    initOverrides?: RequestInit | runtime.InitOverrideFunction,
  ): Promise<runtime.ApiResponse<object>> {
    if (
      requestParameters.userAccountId === null ||
      requestParameters.userAccountId === undefined
    ) {
      throw new runtime.RequiredError(
        "userAccountId",
        "Required parameter requestParameters.userAccountId was null or undefined when calling triggerUserAccountValuation.",
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
        path: `/api/v1/accounts/{user_account_id}/valuation/trigger/`.replace(
          `{${"user_account_id"}}`,
          encodeURIComponent(String(requestParameters.userAccountId)),
        ),
        method: "POST",
        headers: headerParameters,
        query: queryParameters,
      },
      initOverrides,
    );

    return new runtime.JSONApiResponse<any>(response);
  }

  /**
   *
   * Trigger user account valuation
   */
  async triggerUserAccountValuation(
    requestParameters: TriggerUserAccountValuationRequest,
    initOverrides?: RequestInit | runtime.InitOverrideFunction,
  ): Promise<object> {
    const response = await this.triggerUserAccountValuationRaw(
      requestParameters,
      initOverrides,
    );
    return await response.value();
  }
}
