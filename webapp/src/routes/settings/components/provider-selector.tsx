import React, { useState, useEffect } from "react";
import { useApi, FinancialDataProvidersApi } from "clients";

import Select from "react-select";

interface SelectItem {
  label: string;
  value: string;
}

const isNewProvider = (value: SelectItem | null) => {
  return (
    value === null ||
    (value.label === ProviderSelector.New.label &&
      value.value === ProviderSelector.New.value)
  );
};

export type OnChangeCb = (item: SelectItem | null) => void;

export type OnNewCb = () => void;

export interface ProviderSelectorProps {
  onChange: OnChangeCb;
  onNew: OnNewCb | null;
  defaultValue: SelectItem | null;
}

export const ProviderSelector: React.FC<ProviderSelectorProps> & {
  New: SelectItem;
} = (props) => {
  const { onChange = () => {}, onNew = null, defaultValue = null } = props;
  const financialDataProvidersApi = useApi(FinancialDataProvidersApi);

  const [options, setOptions] = useState<Array<SelectItem>>([]);

  useEffect(() => {
    const fetch = async () => {
      const results =
        await financialDataProvidersApi.getFinancialDataProviders();
      const providers = results.providers;
      const allowNew = onNew !== null;
      const newOption = allowNew ? [ProviderSelector.New] : [];
      const otherOptions = providers.map((provider) => {
        return {
          label: provider.description,
          value: provider.id,
        };
      });
      setOptions([...newOption, ...otherOptions]);
    };
    fetch();
  }, [financialDataProvidersApi, onNew]);

  return (
    <Select
      isSearchable
      defaultValue={defaultValue}
      onChange={(value) => {
        if (isNewProvider(value)) {
          if (onNew !== null) {
            onNew();
          }
          return;
        }
        onChange(value);
      }}
      options={options}
    />
  );
};

ProviderSelector.New = { label: "New provider", value: "__NEW_PROVIDER__" };
