import React, { useState, useEffect, useContext } from "react";

import { ServicesContext } from "contexts";

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

  const { finbotClient } = useContext(ServicesContext);
  const [options, setOptions] = useState<Array<SelectItem>>([]);

  useEffect(() => {
    const fetch = async () => {
      const providers = await finbotClient!.getProviders();
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
  }, [finbotClient, onNew]);

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
