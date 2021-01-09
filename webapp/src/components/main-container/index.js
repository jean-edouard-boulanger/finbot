import {Container} from "react-bootstrap";
import React from "react";


export function MainContainer(props) {
    return (
      <div className="main-wrapper">
        <Container fluid>
          {props.children}
        </Container>
      </div>
    );
}

export default MainContainer;
