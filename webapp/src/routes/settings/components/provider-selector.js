import React, {useState, useEffect, useContext} from "react";

import { ServicesContext } from "contexts";

import Select from 'react-select'


const isNewProvider = (value) => {
  return value.label === ProviderSelector.New.label
           && value.value === ProviderSelector.New.value;
}


export const ProviderSelector = (props) => {
  const {
    onChange = (() => {}),
    onNew = null,
    defaultValue = null
  } = props;

  const {finbotClient} = useContext(ServicesContext);
  const [options, setOptions] = useState([])

  useEffect(() => {
    const fetch = async () => {
      const providers = await finbotClient.getProviders();
      const allowNew = onNew !== null;
      const newOption = (allowNew) ? [ProviderSelector.New] : [];
      const otherOptions = providers.map((provider) => {
        return {
          label: provider.description,
          value: provider.id
        }
      });
      setOptions([...newOption, ...otherOptions])
    }
    fetch();
  }, [finbotClient, onNew]);

  return (
    <Select
      searchable
      defaultValue={defaultValue}
      onChange={(value) => {
        if(isNewProvider(value)) {
          if(onNew !== null) {
            onNew();
          }
          return;
        }
        onChange(value);
      }}
      options={options} />
  )
}

ProviderSelector.New = {label: "New provider", value: "__NEW_PROVIDER__"}
