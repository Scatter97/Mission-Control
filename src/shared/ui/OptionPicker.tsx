export type SemanticTone =
  | "neutral"
  | "accent"
  | "success"
  | "warning"
  | "danger"
  | "info"
  | "low"
  | "medium"
  | "high"
  | "critical";

export interface PickerOption<T extends string> {
  value: T;
  label: string;
  tone?: SemanticTone;
}

interface OptionPickerProps<T extends string> {
  label: string;
  value: T;
  options: Array<PickerOption<T>>;
  onChange: (value: T) => void;
  compact?: boolean;
}

export function OptionPicker<T extends string>({
  label,
  value,
  options,
  onChange,
  compact = false
}: OptionPickerProps<T>) {
  return (
    <fieldset className={`mc-option-picker${compact ? " is-compact" : ""}`}>
      <legend>{label}</legend>
      <div className="mc-option-picker-grid">
        {options.map((option) => {
          const selected = option.value === value;

          return (
            <button
              key={option.value}
              type="button"
              role="radio"
              aria-checked={selected}
              data-tone={option.tone ?? "neutral"}
              className={`mc-option-choice${selected ? " is-selected" : ""}`}
              onClick={() => onChange(option.value)}
            >
              <span className="mc-option-dot" />
              {option.label}
            </button>
          );
        })}
      </div>
    </fieldset>
  );
}
