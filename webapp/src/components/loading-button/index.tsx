import React from "react";

import { Button, ButtonProps, Spinner } from "react-bootstrap";

export interface LoadingButtonProps extends ButtonProps {
  loading?: boolean;
}

export const LoadingButton: React.FC<LoadingButtonProps> = (props) => {
  const { children, loading = true, ...buttonProps } = props;
  return (
    <Button disabled={loading} {...buttonProps}>
      {loading && <Spinner size={"sm"} animation={"border"} />} {children}
    </Button>
  );
};

export default LoadingButton;
