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
  AppGetAccountsFormattingRulesResponse,
  ValidationErrorElement,
} from "../models/index";
import {
  AppGetAccountsFormattingRulesResponseFromJSON,
  AppGetAccountsFormattingRulesResponseToJSON,
  ValidationErrorElementFromJSON,
  ValidationErrorElementToJSON,
} from "../models/index";

/**
 * FormattingRulesApi - interface
 *
 * @export
 * @interface FormattingRulesApiInterface
 */
export interface FormattingRulesApiInterface {
  /**
   *
   * @summary Get accounts formatting rules
   * @param {*} [options] Override http request option.
   * @throws {RequiredError}
   * @memberof FormattingRulesApiInterface
   */
  getAccountsFormattingRulesRaw(
    initOverrides?: RequestInit | runtime.InitOverrideFunction,
  ): Promise<runtime.ApiResponse<AppGetAccountsFormattingRulesResponse>>;

  /**
   *
   * Get accounts formatting rules
   */
  getAccountsFormattingRules(
    initOverrides?: RequestInit | runtime.InitOverrideFunction,
  ): Promise<AppGetAccountsFormattingRulesResponse>;
}

/**
 *
 */
export class FormattingRulesApi
  extends runtime.BaseAPI
  implements FormattingRulesApiInterface
{
  /**
   *
   * Get accounts formatting rules
   */
  async getAccountsFormattingRulesRaw(
    initOverrides?: RequestInit | runtime.InitOverrideFunction,
  ): Promise<runtime.ApiResponse<AppGetAccountsFormattingRulesResponse>> {
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
        path: `/api/v1/formatting_rules/accounts/`,
        method: "GET",
        headers: headerParameters,
        query: queryParameters,
      },
      initOverrides,
    );

    return new runtime.JSONApiResponse(response, (jsonValue) =>
      AppGetAccountsFormattingRulesResponseFromJSON(jsonValue),
    );
  }

  /**
   *
   * Get accounts formatting rules
   */
  async getAccountsFormattingRules(
    initOverrides?: RequestInit | runtime.InitOverrideFunction,
  ): Promise<AppGetAccountsFormattingRulesResponse> {
    const response = await this.getAccountsFormattingRulesRaw(initOverrides);
    return await response.value();
  }
}
