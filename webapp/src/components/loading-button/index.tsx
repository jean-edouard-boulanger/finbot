import React from "react";
import { Loader2 } from "lucide-react";

import { Button, type ButtonProps } from "components/ui/button";

export interface LoadingButtonProps extends ButtonProps {
  loading?: boolean;
}

export const LoadingButton: React.FC<LoadingButtonProps> = (props) => {
  const { children, loading = true, ...buttonProps } = props;
  return (
    <Button disabled={loading} {...buttonProps}>
      {loading && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
      {children}
    </Button>
  );
};

export default LoadingButton;
