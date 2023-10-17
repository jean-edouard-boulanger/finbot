import React, { useState, useEffect } from "react";
import { SketchPicker } from "react-color";

export interface ColourPickerProps {
  colour: string;
  onChange?: (newColour: string) => void;
  presetsColours?: Array<string>;
}

export const ColourPicker: React.FC<ColourPickerProps> = (props) => {
  const [colour, setColour] = useState(props.colour);
  const [displayPicker, setDisplayPicker] = useState(false);

  useEffect(() => {
    setColour(props.colour);
  }, [props.colour]);

  const handleColourChanged = (newColour: string, notify?: boolean) => {
    setColour(newColour);
    if (notify && props.onChange) {
      props.onChange(newColour);
    }
  };

  return (
    <div>
      <div
        style={{
          display: "inline-block",
          cursor: "pointer",
          marginTop: "10px",
          marginRight: "10px",
        }}
        onClick={() => setDisplayPicker(!displayPicker)}
      >
        <div
          style={{
            width: "16px",
            height: "16px",
            borderRadius: "8px",
            background: `${colour}`,
          }}
        ></div>
      </div>
      {displayPicker && (
        <div style={{ position: "absolute", zIndex: "2" }}>
          <div
            style={{
              position: "fixed",
              top: "0px",
              right: "0px",
              bottom: "0px",
              left: "0px",
            }}
            onClick={() => setDisplayPicker(false)}
          ></div>
          <SketchPicker
            disableAlpha
            color={colour}
            onChangeComplete={(result) => handleColourChanged(result.hex, true)}
            onChange={(result) => handleColourChanged(result.hex)}
            presetColors={props.presetsColours ?? undefined}
          />
        </div>
      )}
    </div>
  );
};

export default ColourPicker;
