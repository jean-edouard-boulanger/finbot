import React from "react";

import { Container } from "react-bootstrap";

export const MainContainer: React.FC<React.HTMLAttributes<HTMLElement>> = (
  props,
) => {
  return (
    <div className="main-wrapper">
      <Container fluid>{props.children}</Container>
    </div>
  );
};

export default MainContainer;
