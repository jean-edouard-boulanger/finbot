import React, { useState } from "react";
import { Eye, EyeOff } from "lucide-react";

import { Input } from "components/ui/input";
import { Button } from "components/ui/button";

export interface ToggleSecretProps {
  renderAs?: any;
}

export const ToggleSecret: React.FC<
  ToggleSecretProps & { [x: string]: any }
> = (props) => {
  const { renderAs, ...rest } = props;
  const [displayed, setDisplayed] = useState(false);

  const onToggle = () => {
    setDisplayed(!displayed);
  };
  const As = renderAs ? renderAs : Input;
  const ControlIcon = displayed ? EyeOff : Eye;

  return (
    <div className="flex">
      <As
        type={displayed ? "text" : "password"}
        className="rounded-r-none"
        {...rest}
      />
      <Button
        type="button"
        variant="outline"
        className="rounded-l-none border-l-0"
        onClick={onToggle}
      >
        <ControlIcon className="h-4 w-4" />
      </Button>
    </div>
  );
};
