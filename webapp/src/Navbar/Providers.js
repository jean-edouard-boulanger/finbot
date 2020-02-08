import React, { useContext } from "react";
import NavDropdown from 'react-bootstrap/NavDropdown';
import ProvidersContext from "../context/LinkedAccountContext"

const Providers = ({ _setProvider }) => {
    const providersContext = useContext(ProvidersContext);
    const { providersList } = providersContext;

    return (
        <NavDropdown className="px-5" title="Link provider" id="nav-dropdown">
            {providersList.map(provider => <NavDropdown.Item onSelect={_setProvider} size="xxs" eventKey={provider.id}>{provider.description}</NavDropdown.Item>)}
        </NavDropdown>
    )
}

export default Providers;