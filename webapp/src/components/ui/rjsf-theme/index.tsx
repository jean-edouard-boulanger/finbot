import {
  FormContextType,
  RJSFSchema,
  StrictRJSFSchema,
  TemplatesType,
  WidgetProps,
  FieldTemplateProps,
  BaseInputTemplateProps,
  ThemeProps,
} from "@rjsf/utils";
import { Input } from "components/ui/input";
import { Label } from "components/ui/label";
import { Checkbox } from "components/ui/checkbox";

function BaseInputTemplate<
  T = any,
  S extends StrictRJSFSchema = RJSFSchema,
  F extends FormContextType = any,
>(props: BaseInputTemplateProps<T, S, F>) {
  const {
    id,
    type,
    value,
    disabled,
    readonly,
    required,
    onChange,
    onBlur,
    onFocus,
    placeholder,
  } = props;
  return (
    <Input
      id={id}
      type={type || "text"}
      value={value ?? ""}
      disabled={disabled || readonly}
      required={required}
      placeholder={placeholder}
      onChange={(e) => onChange(e.target.value === "" ? undefined : e.target.value)}
      onBlur={(e) => onBlur(id, e.target.value)}
      onFocus={(e) => onFocus(id, e.target.value)}
    />
  );
}

function FieldTemplate<
  T = any,
  S extends StrictRJSFSchema = RJSFSchema,
  F extends FormContextType = any,
>(props: FieldTemplateProps<T, S, F>) {
  const { id, label, children, errors, help, description, hidden, required } =
    props;
  if (hidden) {
    return <div className="hidden">{children}</div>;
  }
  return (
    <div className="mb-3 space-y-2">
      {label && (
        <Label htmlFor={id}>
          {label}
          {required && <span className="text-red-500"> *</span>}
        </Label>
      )}
      {description}
      {children}
      {errors}
      {help}
    </div>
  );
}

function CheckboxWidget<
  T = any,
  S extends StrictRJSFSchema = RJSFSchema,
  F extends FormContextType = any,
>(props: WidgetProps<T, S, F>) {
  const { id, value, disabled, readonly, label, onChange } = props;
  return (
    <div className="flex items-center gap-2">
      <Checkbox
        id={id}
        checked={value}
        disabled={disabled || readonly}
        onCheckedChange={(checked) => onChange(!!checked)}
      />
      {label && <Label htmlFor={id}>{label}</Label>}
    </div>
  );
}

function PasswordWidget<
  T = any,
  S extends StrictRJSFSchema = RJSFSchema,
  F extends FormContextType = any,
>(props: WidgetProps<T, S, F>) {
  const { id, value, disabled, readonly, required, onChange, onBlur, onFocus } =
    props;
  return (
    <Input
      id={id}
      type="password"
      value={value ?? ""}
      disabled={disabled || readonly}
      required={required}
      onChange={(e) =>
        onChange(e.target.value === "" ? undefined : e.target.value)
      }
      onBlur={(e) => onBlur(id, e.target.value)}
      onFocus={(e) => onFocus(id, e.target.value)}
    />
  );
}

const templates: Partial<TemplatesType> = {
  BaseInputTemplate,
  FieldTemplate,
};

const widgets = {
  CheckboxWidget,
  PasswordWidget: PasswordWidget,
};

export const shadcnTheme: ThemeProps = {
  templates,
  widgets,
};
