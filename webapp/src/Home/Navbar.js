import React from "react";
import Navbar from 'react-bootstrap/Navbar';
import NavBar from 'react-bootstrap/NavBar';
import Nav from 'react-bootstrap/Nav';

const Navigation = () => {

    return (
        <NavBar bg="dark" variant="dark">
            <Navbar.Brand href="#home">Finbot</Navbar.Brand>
            <Nav className="mr-auto">
                <Nav.Link href="#home">Home</Nav.Link>
            </Nav>
        </NavBar>
    )
}

export default Navigation;