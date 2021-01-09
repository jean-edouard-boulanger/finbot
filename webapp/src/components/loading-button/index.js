import React from 'react';

import { Button, Spinner } from "react-bootstrap";


export const LoadingButton = (props) => {
  const {children, loading = true, ...buttonProps} = props;
  return (
    <Button {...buttonProps} disabled={loading}>
      {(loading)
          && <Spinner size={"sm"} animation={"border"} />}
      {" "}
      {children}
    </Button>
  )
};

export default LoadingButton;
