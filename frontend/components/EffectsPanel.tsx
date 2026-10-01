"use client";

import React from "react";

export interface EffectOptions {
  apply_8d: boolean;
  apply_slow: boolean;
  apply_reverb: boolean;
  apply_bass_boost: boolean;
  bass_boost_db: number;
}

interface Props {
  options: EffectOptions;
  onToggle: (key: keyof Omit<EffectOptions, "bass_boost_db">) => void;
  onBassBoostChange: (value: number) => void;
  onReset: () => void;
}

const effectIcons: Record<string, string> = {
  apply_8d: "🎯",
  apply_slow: "🐢",
  apply_reverb: "🔊",
  apply_bass_boost: "🔉",
};

const effectDescriptions: Record<string, string> = {
  apply_8d: "Spatial 360° panning effect",
  apply_slow: "Slow down playback speed",
  apply_reverb: "Add hall reverb ambience",
  apply_bass_boost: "Enhance low frequencies",
};

export default function EffectsPanel({
  options,
  onToggle,
  onBassBoostChange,
  onReset,
}: Props) {
  const effects = [
    { key: "apply_8d", label: "8D Audio" },
    { key: "apply_slow", label: "Slow Effect" },
    { key: "apply_reverb", label: "Reverb" },
    { key: "apply_bass_boost", label: "Bass Booster" },
  ] as const;

  return (
    <div
      style={{
        marginTop: "20px",
        padding: "18px",
        borderRadius: "16px",
        background: "rgba(9, 12, 24, 0.55)",
        border: "1px solid rgba(255, 255, 255, 0.08)",
      }}
    >
      <div
        style={{
          marginBottom: "16px",
          display: "flex",
          alignItems: "center",
          gap: "8px",
        }}
      >
        <span style={{ fontSize: "16px" }}>🎚️</span>
        <div
          style={{
            fontWeight: 700,
            fontSize: "15px",
            color: "var(--text-primary)",
          }}
        >
          Audio Effects
        </div>
        <div
          style={{
            marginLeft: "auto",
            fontSize: "12px",
            color: "var(--text-muted)",
            padding: "4px 10px",
            borderRadius: "20px",
            background: "rgba(139, 92, 246, 0.1)",
          }}
        >
          {[
            options.apply_8d && "8D",
            options.apply_slow && "Slow",
            options.apply_reverb && "Reverb",
            options.apply_bass_boost && "Bass",
          ]
            .filter(Boolean)
            .join(", ") || "None"}
        </div>
      </div>

      <div className="effects-panel">
        {effects.map(({ key, label }) => {
          const isChecked = options[key] as boolean;

          return (
            <div key={key}>
              <div
                className={`effect-item ${isChecked ? "active" : ""}`}
                onClick={() => onToggle(key as keyof Omit<EffectOptions, "bass_boost_db">)}
              >
                <label className="effect-item-label" style={{ cursor: "pointer" }}>
                  <span className="effect-item-label-icon">{effectIcons[key]}</span>
                  <div>
                    <div className="effect-item-label-text">{label}</div>
                    <div className="effect-item-description">{effectDescriptions[key]}</div>
                  </div>
                </label>
                <input
                  type="checkbox"
                  className="effect-checkbox"
                  checked={isChecked}
                  onChange={() => onToggle(key as keyof Omit<EffectOptions, "bass_boost_db">)}
                  onClick={(e) => e.stopPropagation()}
                  aria-label={label}
                />
              </div>

              {key === "apply_bass_boost" && isChecked && (
                <div className="bass-boost-controls">
                  <div className="bass-boost-header">
                    <span>Boost Level</span>
                    <span className="bass-boost-value">{options.bass_boost_db} dB</span>
                  </div>

                  <input
                    type="range"
                    className="effect-slider"
                    min={1}
                    max={12}
                    step={1}
                    value={options.bass_boost_db}
                    onChange={(e) => onBassBoostChange(Number(e.target.value))}
                    aria-label="Bass boost level"
                    style={{ cursor: "pointer" }}
                  />

                  <div
                    style={{
                      display: "flex",
                      justifyContent: "space-between",
                      fontSize: "11px",
                      color: "var(--text-muted)",
                      paddingTop: "4px",
                    }}
                  >
                    <span>Subtle</span>
                    <span>Medium</span>
                    <span>Aggressive</span>
                  </div>

                  <div className="bass-boost-info">
                    <i className="bi bi-info-circle" style={{ fontSize: "11px" }}></i>
                    <span>
                      {options.bass_boost_db <= 3
                        ? "Subtle low-end enhancement"
                        : options.bass_boost_db <= 7
                          ? "Balanced bass presence"
                          : "Strong bass emphasis"}
                    </span>
                  </div>
                </div>
              )}
            </div>
          );
        })}
      </div>

      <div
        style={{
          marginTop: "16px",
          paddingTop: "14px",
          borderTop: "1px solid rgba(139, 92, 246, 0.15)",
          display: "grid",
          gap: "8px",
        }}
      >
        <div
          style={{
            fontSize: "12px",
            fontWeight: 600,
            color: "var(--text-muted)",
            marginBottom: "2px",
            textTransform: "uppercase",
            letterSpacing: "0.05em",
          }}
        >
          Quick Presets
        </div>
        <div
          style={{
            display: "grid",
            gridTemplateColumns: "repeat(2, 1fr)",
            gap: "8px",
          }}
        >
          <button
            onClick={() => {
              if (!options.apply_8d) onToggle("apply_8d");
              if (!options.apply_slow) onToggle("apply_slow");
              if (!options.apply_reverb) onToggle("apply_reverb");
              if (!options.apply_bass_boost) onToggle("apply_bass_boost");
              if (options.bass_boost_db !== 7) onBassBoostChange(7);
            }}
            style={{
              padding: "8px 12px",
              borderRadius: "8px",
              background: "rgba(139, 92, 246, 0.12)",
              border: "1px solid rgba(139, 92, 246, 0.25)",
              color: "var(--text-secondary)",
              fontSize: "12px",
              fontWeight: 500,
              cursor: "pointer",
              transition: "all 0.2s ease",
            }}
            onMouseEnter={(e) => {
              (e.target as HTMLButtonElement).style.background = "rgba(139, 92, 246, 0.2)";
              (e.target as HTMLButtonElement).style.color = "var(--text-primary)";
            }}
            onMouseLeave={(e) => {
              (e.target as HTMLButtonElement).style.background = "rgba(139, 92, 246, 0.12)";
              (e.target as HTMLButtonElement).style.color = "var(--text-secondary)";
            }}
          >
            ✨ Full Experience
          </button>
          <button
            onClick={() => {
              if (!options.apply_8d) onToggle("apply_8d");
              if (options.apply_slow) onToggle("apply_slow");
              if (options.apply_reverb) onToggle("apply_reverb");
              if (options.apply_bass_boost) onToggle("apply_bass_boost");
            }}
            style={{
              padding: "8px 12px",
              borderRadius: "8px",
              background: "rgba(139, 92, 246, 0.12)",
              border: "1px solid rgba(139, 92, 246, 0.25)",
              color: "var(--text-secondary)",
              fontSize: "12px",
              fontWeight: 500,
              cursor: "pointer",
              transition: "all 0.2s ease",
            }}
            onMouseEnter={(e) => {
              (e.target as HTMLButtonElement).style.background = "rgba(139, 92, 246, 0.2)";
              (e.target as HTMLButtonElement).style.color = "var(--text-primary)";
            }}
            onMouseLeave={(e) => {
              (e.target as HTMLButtonElement).style.background = "rgba(139, 92, 246, 0.12)";
              (e.target as HTMLButtonElement).style.color = "var(--text-secondary)";
            }}
          >
            🎯 8D Only
          </button>
        </div>

        <button
          onClick={onReset}
          style={{
            width: "100%",
            padding: "10px 12px",
            borderRadius: "10px",
            border: "1px solid rgba(148, 163, 184, 0.25)",
            background: "rgba(255, 255, 255, 0.03)",
            color: "var(--text-primary)",
            fontSize: "12px",
            fontWeight: 600,
            cursor: "pointer",
            transition: "all 0.2s ease",
          }}
          onMouseEnter={(e) => {
            (e.target as HTMLButtonElement).style.background = "rgba(255, 255, 255, 0.08)";
            (e.target as HTMLButtonElement).style.borderColor = "rgba(148, 163, 184, 0.4)";
          }}
          onMouseLeave={(e) => {
            (e.target as HTMLButtonElement).style.background = "rgba(255, 255, 255, 0.03)";
            (e.target as HTMLButtonElement).style.borderColor = "rgba(148, 163, 184, 0.25)";
          }}
        >
          ↻ Reset to Default
        </button>
      </div>
    </div>
  );
}
