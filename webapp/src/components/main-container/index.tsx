import React from "react";

export const MainContainer: React.FC<React.HTMLAttributes<HTMLElement>> = (
  props,
) => {
  return (
    <div className="container mx-auto px-6 pb-48 pt-6">{props.children}</div>
  );
};

export default MainContainer;
