import type { SemanticTone } from "./OptionPicker";

interface StateBadgeProps {
  label: string;
  tone?: SemanticTone;
}

export function StateBadge({ label, tone = "neutral" }: StateBadgeProps) {
  return (
    <span className="mc-state-badge" data-tone={tone}>
      <span className="mc-state-dot" />
      {label}
    </span>
  );
}
