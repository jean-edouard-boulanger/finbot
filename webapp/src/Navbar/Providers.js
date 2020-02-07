import React from "react";
import NavDropdown from 'react-bootstrap/NavDropdown';

const Providers = props => {
    return (
        <NavDropdown title="Link provider" id="nav-dropdown">
            {props.options.map(provider => <NavDropdown.Item onSelect={() => console.log("i wsas selected")} eventKey={provider.id}>{provider.description}</NavDropdown.Item>)}
        </NavDropdown>
    )
}

export default Providers;