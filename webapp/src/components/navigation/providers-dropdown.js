import React, { useContext } from "react";
import NavDropdown from 'react-bootstrap/NavDropdown';
import ProvidersContext from "../../context/linked-account-context"

const Providers = (props) => {
    const providersContext = useContext(ProvidersContext);
    const { providersList } = providersContext;

    return (
        <NavDropdown className="px-5" title="Link provider" id="nav-dropdown" active={props.pathname.includes("linked-account/create")}>
            {providersList.map(provider => <NavDropdown.Item onSelect={props._setProvider} size="xxs" key={provider.id} eventKey={provider.id}>{provider.description}</NavDropdown.Item>)}
        </NavDropdown>
    )
}

export default Providers;