import React, { useState } from "react";

import { Form, InputGroup, Button } from "react-bootstrap";
import { FaEye, FaEyeSlash } from "react-icons/fa";

export const ToggleSecret = (props) => {
  const { renderAs, ...rest } = props;
  const [displayed, setDisplayed] = useState(false);

  const onToggle = () => {
    setDisplayed(!displayed);
  };
  const As = renderAs ? renderAs : Form.Control;
  const ControlIcon = displayed ? FaEyeSlash : FaEye;

  return (
    <InputGroup>
      <As type={displayed ? "text" : "password"} {...rest} />
      <InputGroup.Append>
        <Button onClick={onToggle}>
          <ControlIcon />
        </Button>
      </InputGroup.Append>
    </InputGroup>
  );
};
